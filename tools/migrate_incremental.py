#!/usr/bin/env python3
# tools/migrate_incremental.py — Re-migrate specific legacy bees/honeycomb rooms
# into the four-level structure during the deprecation window.
#
# The full migration (migrate_v2.py) snapshotted bees/honeycomb at v1.0. Any
# bees/honeycomb edits made AFTER that snapshot drift the static-prompt-injection
# corpus (legacy bees path) ahead of the honeycomb-as-canonical-source. This
# script catches that drift and folds the edits into a patch release.
#
# Pipeline per drifted source:
#   1. Find the existing closet (via `migrated from <name>.md` frontmatter)
#   2. Delete the closet directory
#   3. Re-run migrate_v2's per-room pipeline (classify + mechanical split)
#
# Usage:
#   tools/migrate_incremental.py --since v1.0
#       Diff bees/honeycomb/ since that honeycomb tag and migrate the diff
#
#   tools/migrate_incremental.py --rooms petitions-format.md role-queen.md
#       Re-migrate the named legacy rooms regardless of git state
#
#   tools/migrate_incremental.py --dry-run …
#       Report what would change; write nothing

from __future__ import annotations

import argparse
import asyncio
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

LEGACY_HONEYCOMB = Path("/Users/vivian/claude/bees/honeycomb")
TARGET_HONEYCOMB = REPO_ROOT  # honeycomb repo root


# ── Discovery ────────────────────────────────────────────────────────────────


def find_drift_since_tag(since_tag: str) -> list[Path]:
    """Return bees/honeycomb/wing_*/*.md files modified after the given
    honeycomb tag's commit date."""
    # 1. Read the tag's commit date from honeycomb.
    try:
        ts = subprocess.check_output(
            ["git", "log", "-1", "--format=%aI", since_tag],
            cwd=str(TARGET_HONEYCOMB),
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        print(f"could not resolve tag {since_tag} in honeycomb repo", file=sys.stderr)
        return []

    # 2. List bees/honeycomb files modified after that date.
    try:
        out = subprocess.check_output(
            [
                "git", "log", f"--since={ts}",
                "--name-only", "--pretty=format:",
                "--", "honeycomb/",
            ],
            cwd=str(LEGACY_HONEYCOMB.parent),
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"git log in bees failed: {e}", file=sys.stderr)
        return []

    seen: set[Path] = set()
    out_paths: list[Path] = []
    for line in out.splitlines():
        line = line.strip()
        if not line or not line.endswith(".md"):
            continue
        # Skip non-room files (e.g. CHANGELOG.md in the honeycomb subdir).
        if "/wing_" not in line and not line.startswith("honeycomb/wing_"):
            continue
        rel = Path(line)
        full = LEGACY_HONEYCOMB.parent / rel
        if not full.exists():
            continue  # deleted file — handled separately, out of scope here
        if full in seen:
            continue
        seen.add(full)
        out_paths.append(full)
    return out_paths


def find_existing_closet(source_name: str) -> Path | None:
    """Find the closet directory matching the given source filename via the
    `migrated from <name>.md` line in its closet.md frontmatter."""
    needle = f"migrated from {source_name}"
    for closet_md in TARGET_HONEYCOMB.glob("wing_*/*/*/closet.md"):
        if needle in closet_md.read_text(encoding="utf-8"):
            return closet_md.parent
    return None


# ── Re-migration ─────────────────────────────────────────────────────────────


async def remigrate(sources: list[Path], dry_run: bool) -> int:
    """For each source, write fresh closet content into the EXISTING closet
    location (no reclassification). New rooms classify normally via
    migrate_v2's full pipeline. Returns 0 on full success, 1 otherwise."""
    # Import lazily so dry-run doesn't pay the LLM client import cost.
    from migrate_v2 import (
        Classification, parse_room, place_room, classify_room,
        load_wing_manifests, build_wing_summary, health_check,
    )

    manifests = load_wing_manifests()
    wing_summary = build_wing_summary(manifests)

    in_place: list[tuple[Path, Path]] = []   # (source, existing_closet)
    new_sources: list[Path] = []
    for src in sources:
        existing = find_existing_closet(src.name)
        if existing:
            in_place.append((src, existing))
        else:
            new_sources.append(src)

    print(f"in-place updates: {len(in_place)}")
    print(f"new closets:      {len(new_sources)}")

    if dry_run:
        return 0

    if new_sources and not await health_check():
        return 2

    ok = 0
    failures: list[tuple[Path, str]] = []

    # ── In-place updates: no classifier call, content rewrite only ──────────
    import re as _re
    for src, existing in in_place:
        try:
            wing, room, closet = (
                existing.parent.parent.name,
                existing.parent.name,
                existing.name,
            )
            # Preserve existing closet's tags from its frontmatter so they
            # carry across the in-place rewrite. Tag lines look like:
            #   tools: [a, b]   languages: [python]   models: [haiku]
            existing_closet_text = (existing / "closet.md").read_text(encoding="utf-8")
            tags: dict[str, list[str]] = {}
            for key in ("tools", "models", "languages"):
                m = _re.search(rf"^{key}:\s*\[([^\]]*)\]", existing_closet_text, _re.MULTILINE)
                if m:
                    vals = [v.strip() for v in m.group(1).split(",") if v.strip()]
                    if vals:
                        tags[key] = vals
            classification = Classification(
                target_wing=wing,
                target_room=room,
                target_closet=closet,
                tags=tags,
                notes="in-place update",
            )
            parsed = parse_room(src)
            shutil.rmtree(existing)
            target, _ = place_room(parsed, classification, dry_run=False)
            print(f"  ✓  {src.name:36s} → {target.relative_to(TARGET_HONEYCOMB)} (in-place, tags={list(tags)})", flush=True)
            ok += 1
        except Exception as e:  # noqa: BLE001
            failures.append((src, f"{type(e).__name__}: {e}"))
            print(f"  ✗  {src.name:36s} {type(e).__name__}: {e}", flush=True)

    # Refresh all index.md files (drawer listing may have changed for any
    # in-place update; cheap to do everything).
    if in_place or new_sources:
        from migrate_v2 import write_indexes
        n = write_indexes()
        print(f"  refreshed index.md for {n} closet(s)", flush=True)

    # ── New closets: full classify + place via migrate_v2 ───────────────────
    if new_sources:
        from migrate_v2 import migrate_one
        sem = asyncio.Semaphore(4)
        counter = {"done": 0, "total": len(new_sources)}
        results = await asyncio.gather(*[
            migrate_one(src, wing_summary, sem, False, counter)
            for src in new_sources
        ])
        for r in results:
            if r.ok:
                ok += 1
            else:
                failures.append((r.source, r.error or "unknown"))

    print()
    total = len(in_place) + len(new_sources)
    print(f"results: {ok}/{total} ok")
    for src, err in failures:
        print(f"  failed: {src.name}  {err}")
    return 0 if ok == total else 1


# ── Main ─────────────────────────────────────────────────────────────────────


async def main_async(args) -> int:
    if args.rooms:
        sources = [LEGACY_HONEYCOMB / "wing_bees" / r for r in args.rooms]
        missing = [s for s in sources if not s.exists()]
        if missing:
            for m in missing:
                print(f"not found: {m}", file=sys.stderr)
            return 1
    else:
        sources = find_drift_since_tag(args.since)

    if not sources:
        print("no drift detected")
        return 0

    print(f"drift: {len(sources)} source room(s)")
    for s in sources:
        existing = find_existing_closet(s.name)
        marker = "→ " + str(existing.relative_to(TARGET_HONEYCOMB)) if existing else "(new)"
        print(f"  {s.relative_to(LEGACY_HONEYCOMB.parent)}  {marker}")

    if args.dry_run:
        print("\nDRY RUN — would re-migrate the above.")
        return 0

    print()
    return await remigrate(sources, args.dry_run)


def main() -> int:
    parser = argparse.ArgumentParser(description="Incremental honeycomb migration.")
    parser.add_argument("--since", default="v1.0", help="git tag in the honeycomb repo (default v1.0)")
    parser.add_argument("--rooms", nargs="+", help="explicit legacy room names (skips git diff)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
