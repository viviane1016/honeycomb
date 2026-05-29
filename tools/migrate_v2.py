#!/usr/bin/env python3
# tools/migrate_v2.py — canonical-content migration from legacy bees/honeycomb
# to four-level wing/room/closet/drawer structure (ADR-0024).
#
# Lessons from v1 (archived in tools/archive/migrate_v1.py):
#   • v1 asked Haiku to WRITE drawer files → 7.2× content bloat from synthesised
#     paraphrase. v2 treats drawers as canonical artifacts.
#   • v1 regenerated closet.md via LLM → 96% of legacy rooms already have an
#     author-written `## Closet` section. v2 uses it verbatim.
#   • v1 fabricated Readme.md / design.md with no source basis. v2 doesn't.
#
# Pipeline per legacy room:
#   1. Parse — strip HTML frontmatter, extract Hall, split body by `## ` headings
#   2. Classify — single Haiku call returns {wing, room, closet} triple
#   3. Place — mechanical mkdir + write closet.md (from `## Closet` verbatim) +
#               write each `## <H>` section as <kebab(H)>.md drawer + tunnels.md
#               + index.md
#
# Haiku is used ONLY for classification. Everything else is mechanical.
# Multi-source closets (multiple legacy files → same destination) get a
# .multi-source marker file for operator review.
#
# Usage:
#   tools/migrate_v2.py --dry-run                  # classify-only, no writes
#   tools/migrate_v2.py --room briefing-template.md   # single-room test
#   tools/migrate_v2.py                            # full migration

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# ── Configuration ────────────────────────────────────────────────────────────

LEGACY_HONEYCOMB = Path("/Users/vivian/claude/bees/honeycomb")
TARGET_HONEYCOMB = Path("/Users/vivian/claude/honeycomb")

CLAUDE_MODEL = "haiku"
ASYNC_CONCURRENCY = 8

WINGS_DIR_NAMES = [
    "wing_bees",
    "wing_repo_bees",
    "wing_practices",
    "wing_antipatterns",
    "wing_tools",
    "wing_models",
]

# ── JSON extraction (tolerant — borrowed from v1) ────────────────────────────


def extract_json(text: str) -> dict:
    """Robustly extract a JSON object from model output."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError(f"no JSON object found in model output: {text[:200]}…")


# ── Classification prompt ────────────────────────────────────────────────────

CLASSIFY_PROMPT = """\
You are a classifier for a honeycomb knowledge migration. You ONLY classify;
you do NOT write content.

The user message contains a legacy markdown room delimited by
<<<ROOM>>> ... <<<END>>> markers. IGNORE everything outside those markers
(any system preamble, available tools, etc.). Classify the room content.

Available target wings and their canonical rooms:
{wing_summary}

Output a JSON object (ONLY a JSON object — no prose, no code fences) with:

  target_wing:    one of the wings above
  target_room:    one of the canonical rooms for that wing
  target_closet:  a kebab-case directory name for this specific topic
  tags:           object with optional keys 'tools', 'models', 'languages'
                  (arrays of string identifiers; omit any key with empty array)
  notes:          one-sentence rationale (≤200 chars)

Guidance:
  - target_room should be one of the wing's canonical_rooms when possible.
    Inventing rooms is allowed if the content genuinely doesn't fit any
    canonical room — but prefer the closest canonical match.
  - target_closet kebab-case names what THIS specific topic is, not the
    broader room (e.g. "sapper-drone" not "drone", "manual-amend" not
    "build").
  - Drones / GitHub Actions workflows belong in wing_bees/actions/<name>/.
  - When a file's content is about the bees codebase itself (how it's
    structured, what its actors are), prefer wing_repo_bees.
  - When it's about how bees operates at runtime (procedures, contracts,
    operating prompts), prefer wing_bees.
  - When it's a universal pattern or anti-pattern, prefer wing_practices
    or wing_antipatterns.
"""

# ── Parse legacy markdown ────────────────────────────────────────────────────


@dataclass
class ParsedRoom:
    source_path: Path
    hall: str | None
    closet_text: str        # verbatim `## Closet` section (or empty)
    drawers: dict[str, str] # kebab-name -> verbatim section text
    see_also: list[str]     # raw room names from `## See also`
    body: str               # full body (without frontmatter) for classification


_FRONTMATTER_RE = re.compile(r"^<!--.*?-->\s*", re.DOTALL)
_HALL_RE = re.compile(r"^Hall:\s*(hall_\w+)\s*$", re.MULTILINE)
_H2_RE = re.compile(r"^## ", re.MULTILINE)


def kebab(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def parse_room(path: Path) -> ParsedRoom:
    text = path.read_text(encoding="utf-8")

    # Extract Hall from the frontmatter (if present) before stripping it.
    hall_match = _HALL_RE.search(text)
    hall = hall_match.group(1) if hall_match else None

    # Strip the leading HTML-comment frontmatter.
    body = _FRONTMATTER_RE.sub("", text, count=1).strip()

    # Split into sections by `## ` headings.
    # Find heading positions.
    positions: list[tuple[int, str]] = []
    for m in re.finditer(r"^## (.+)$", body, re.MULTILINE):
        positions.append((m.start(), m.group(1).strip()))

    closet_text = ""
    drawers: dict[str, str] = {}
    see_also: list[str] = []

    for i, (start, heading) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(body)
        section_text = body[start:end].rstrip() + "\n"
        heading_lower = heading.lower().strip()

        if heading_lower == "closet":
            # Closet text WITHOUT the `## Closet` heading line — it's the
            # closet.md content, which carries its own frontmatter instead.
            # Strip the first line (the `## Closet` heading).
            lines = section_text.splitlines()
            closet_text = "\n".join(lines[1:]).strip() + "\n"
        elif heading_lower == "see also":
            # Extract room references from bullets or comma-separated text.
            for line in section_text.splitlines()[1:]:
                line = line.strip()
                if not line:
                    continue
                # Bullet list: `- room-name — description` or `- room-name`
                m = re.match(r"^[-*]\s+`?([a-z0-9][a-z0-9-]*)`?\s*(?:[—\-:].*)?$", line)
                if m:
                    see_also.append(m.group(1))
                    continue
                # Comma-separated: `room-a, room-b, room-c`
                for token in re.split(r"[,;]\s*", line):
                    token = token.strip().strip("`").strip()
                    if re.match(r"^[a-z0-9][a-z0-9-]*$", token):
                        see_also.append(token)
        else:
            # Regular drawer. Include the heading line verbatim.
            drawer_name = kebab(heading)
            if drawer_name:
                drawers[drawer_name] = section_text

    return ParsedRoom(
        source_path=path,
        hall=hall,
        closet_text=closet_text,
        drawers=drawers,
        see_also=see_also,
        body=body,
    )


# ── Manifest helpers ─────────────────────────────────────────────────────────


def load_wing_manifests() -> dict[str, dict]:
    manifests = {}
    for wing in WINGS_DIR_NAMES:
        path = TARGET_HONEYCOMB / wing / "_manifest.yaml"
        if path.exists():
            manifests[wing] = yaml.safe_load(path.read_text())
    return manifests


def build_wing_summary(manifests: dict[str, dict]) -> str:
    lines = []
    for wing, manifest in manifests.items():
        scope = manifest.get("scope", "?")
        rooms = ", ".join(manifest.get("canonical_rooms", [])) or "(open)"
        lines.append(f"  {wing} ({scope}): {rooms}")
    return "\n".join(lines)


# ── LLM call (subprocess-based; borrowed from v1) ────────────────────────────


async def claude_call(system_prompt: str, user_prompt: str) -> str:
    args = [
        "claude",
        "-p",
        "--model", CLAUDE_MODEL,
        "--system-prompt", system_prompt,
        "--no-session-persistence",
        "--output-format", "text",
    ]
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(user_prompt.encode())
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude exit {proc.returncode}: {stderr.decode()[:400]}"
        )
    return stdout.decode()


@dataclass
class Classification:
    target_wing: str
    target_room: str
    target_closet: str
    tags: dict
    notes: str


async def classify_room(parsed: ParsedRoom, wing_summary: str) -> Classification:
    sys_prompt = CLASSIFY_PROMPT.format(wing_summary=wing_summary)
    wrapped = f"<<<ROOM>>>\n{parsed.body}\n<<<END>>>"
    out = await claude_call(sys_prompt, wrapped)
    data = extract_json(out)
    return Classification(
        target_wing=data["target_wing"],
        target_room=data["target_room"],
        target_closet=data["target_closet"],
        tags={k: v for k, v in (data.get("tags") or {}).items() if v},
        notes=data.get("notes", ""),
    )


# ── Placement (mechanical) ───────────────────────────────────────────────────


def build_closet_md(parsed: ParsedRoom, classification: Classification) -> str:
    """Build closet.md content: HTML frontmatter + verbatim `## Closet` text."""
    src_name = parsed.source_path.name
    lines = [f"<!-- {classification.target_closet}.md: migrated from {src_name}."]
    lines.append("")
    if parsed.hall:
        lines.append(f"Hall: {parsed.hall}")
    if classification.tags.get("tools"):
        lines.append(f"tools: [{', '.join(classification.tags['tools'])}]")
    if classification.tags.get("models"):
        lines.append(f"models: [{', '.join(classification.tags['models'])}]")
    if classification.tags.get("languages"):
        lines.append(f"languages: [{', '.join(classification.tags['languages'])}]")
    lines.append("-->")
    lines.append("")
    if parsed.closet_text:
        lines.append(parsed.closet_text.rstrip())
    else:
        lines.append("<!-- legacy room had no `## Closet` section -->")
    return "\n".join(lines) + "\n"


def build_index_md(drawer_files: list[str], drawer_dir: Path) -> str:
    """Build index.md: TOC of drawers with one-line subtitles."""
    lines = ["## Drawers", ""]
    for name in sorted(drawer_files):
        stub = name.removesuffix(".md")
        # Subtitle = first non-blank line of the drawer file, stripped of `## `.
        try:
            text = (drawer_dir / name).read_text()
            subtitle = ""
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith("<!--"):
                    subtitle = line.lstrip("# ").strip()
                    break
        except Exception:
            subtitle = ""
        if subtitle:
            lines.append(f"- **{stub}** — {subtitle}")
        else:
            lines.append(f"- **{stub}**")
    return "\n".join(lines) + "\n"


def place_room(
    parsed: ParsedRoom,
    classification: Classification,
    dry_run: bool,
) -> tuple[Path, bool]:
    """Place the parsed room into target_wing/target_room/target_closet/.

    Returns (target_path, is_multi_source). is_multi_source is True when the
    target directory already exists with a different source's content."""
    target = (
        TARGET_HONEYCOMB
        / classification.target_wing
        / classification.target_room
        / classification.target_closet
    )

    multi_source = False
    if target.exists() and any(target.iterdir()):
        # Already has content from a previous source.
        multi_source = True

    if dry_run:
        return target, multi_source

    target.mkdir(parents=True, exist_ok=True)

    if not multi_source:
        # Single-source: write closet.md verbatim from this source's `## Closet`.
        (target / "closet.md").write_text(
            build_closet_md(parsed, classification), encoding="utf-8"
        )

    # Drawers: write each section file. If a drawer of the same name already
    # exists (multi-source case), append with a source-divider rather than
    # silently overwriting.
    for name, text in parsed.drawers.items():
        drawer_path = target / f"{name}.md"
        if drawer_path.exists():
            existing = drawer_path.read_text()
            divider = f"\n\n<!-- additional content from {parsed.source_path.name} -->\n\n"
            drawer_path.write_text(existing.rstrip() + divider + text, encoding="utf-8")
        else:
            drawer_path.write_text(text, encoding="utf-8")

    # tunnels.md: see-also references. Append-merge in multi-source case.
    if parsed.see_also:
        tunnels_path = target / "tunnels.md"
        existing_lines: list[str] = []
        if tunnels_path.exists():
            existing_lines = [
                ln.strip() for ln in tunnels_path.read_text().splitlines() if ln.strip()
            ]
        all_refs = sorted(set(existing_lines) | set(parsed.see_also))
        tunnels_path.write_text("\n".join(all_refs) + "\n", encoding="utf-8")

    if multi_source:
        # Marker file listing contributing sources for operator review.
        marker = target / ".multi-source"
        existing = ""
        if marker.exists():
            existing = marker.read_text()
        if str(parsed.source_path) not in existing:
            marker.write_text(
                existing + f"{parsed.source_path}\n", encoding="utf-8"
            )

    return target, multi_source


# ── Per-room pipeline ────────────────────────────────────────────────────────


@dataclass
class RoomResult:
    source: Path
    classification: Classification | None
    target: Path | None
    multi_source: bool
    error: str | None

    @property
    def ok(self) -> bool:
        return self.error is None


async def migrate_one(
    source: Path,
    wing_summary: str,
    sem: asyncio.Semaphore,
    dry_run: bool,
    counter: dict,
) -> RoomResult:
    async with sem:
        try:
            t0 = asyncio.get_event_loop().time()
            print(f"  …  {source.name}", flush=True)
            parsed = parse_room(source)
            classification = await classify_room(parsed, wing_summary)
            target, multi_source = place_room(parsed, classification, dry_run)

            elapsed = asyncio.get_event_loop().time() - t0
            counter["done"] += 1
            tag = ""
            if classification.tags.get("tools"):
                tag = f"  tools={','.join(classification.tags['tools'])}"
            multi = "  (multi-source)" if multi_source else ""
            print(
                f"  ✓  [{counter['done']:2d}/{counter['total']}] "
                f"{elapsed:5.1f}s  {source.name:38s} → "
                f"{classification.target_wing}/{classification.target_room}/"
                f"{classification.target_closet}{tag}{multi}",
                flush=True,
            )
            return RoomResult(
                source=source,
                classification=classification,
                target=target,
                multi_source=multi_source,
                error=None,
            )

        except Exception as e:
            elapsed = asyncio.get_event_loop().time() - t0
            counter["done"] += 1
            print(
                f"  ✗  [{counter['done']:2d}/{counter['total']}] "
                f"{elapsed:5.1f}s  {source.name:38s}   "
                f"{type(e).__name__}: {str(e)[:120]}",
                flush=True,
            )
            return RoomResult(
                source=source,
                classification=None,
                target=None,
                multi_source=False,
                error=f"{type(e).__name__}: {e}",
            )


# ── Post-pass: generate index.md for every populated closet ──────────────────


def write_indexes() -> int:
    """Walk every closet directory and write/refresh index.md."""
    count = 0
    for closet_dir in TARGET_HONEYCOMB.glob("wing_*/*/*/"):
        if not closet_dir.is_dir():
            continue
        drawer_files = sorted(
            p.name
            for p in closet_dir.iterdir()
            if p.is_file()
            and p.suffix == ".md"
            and p.name not in {"closet.md", "index.md", "tunnels.md"}
            and not p.name.startswith(".")
        )
        index_path = closet_dir / "index.md"
        index_path.write_text(
            build_index_md(drawer_files, closet_dir), encoding="utf-8"
        )
        count += 1
    return count


# ── Health check ─────────────────────────────────────────────────────────────


async def health_check() -> bool:
    proc = await asyncio.create_subprocess_exec(
        "claude", "--version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        print(f"error: claude CLI not available: {err.decode()[:200]}", file=sys.stderr)
        return False
    return True


# ── Main ─────────────────────────────────────────────────────────────────────


async def main_async(args) -> int:
    if not await health_check():
        return 2

    manifests = load_wing_manifests()
    wing_summary = build_wing_summary(manifests)

    sources: list[Path] = []
    for wing_dir in sorted(LEGACY_HONEYCOMB.glob("wing_*")):
        for md in sorted(wing_dir.glob("*.md")):
            if md.name.startswith(("_", ".")):
                continue
            if args.room and md.name != args.room:
                continue
            sources.append(md)

    if not sources:
        print("no legacy rooms found", file=sys.stderr)
        return 1

    print(f"migrating {len(sources)} legacy rooms (concurrency={ASYNC_CONCURRENCY})")
    print(f"backend: claude CLI --model {CLAUDE_MODEL} (classify only)")
    print(f"target:  {TARGET_HONEYCOMB}")
    if args.dry_run:
        print("DRY RUN — classify only, no writes")
    print()

    sem = asyncio.Semaphore(ASYNC_CONCURRENCY)
    counter = {"done": 0, "total": len(sources)}
    tasks = [
        migrate_one(src, wing_summary, sem, args.dry_run, counter)
        for src in sources
    ]
    results = await asyncio.gather(*tasks)

    # Post-pass: regenerate index.md for every populated closet.
    if not args.dry_run:
        n = write_indexes()
        print(f"\nwrote index.md for {n} closet(s)", flush=True)

    print()
    print("─" * 72)
    ok = sum(r.ok for r in results)
    multi = sum(r.multi_source for r in results if r.ok)
    print(f"results: {ok}/{len(results)} ok ({multi} multi-source)")
    print("─" * 72)
    failures = [r for r in results if not r.ok]
    for r in failures:
        print(f"  failed: {r.source.name}   {r.error}", flush=True)
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Honeycomb v1.0 canonical-content migration.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--room", help="only migrate the named legacy room")
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
