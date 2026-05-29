#!/usr/bin/env python3
# tools/migrate_v1.py — one-shot migration from legacy bees/honeycomb to four-level
# structure (ADR-0024). Throwaway: runs once at cutover, then archived.
#
# Reads:  /Users/vivian/claude/bees/honeycomb/wing_*/<room>.md
# Writes: /Users/vivian/claude/honeycomb/<target_wing>/<room>/<closet>/{closet.md,
#                                                                       index.md,
#                                                                       design.md,
#                                                                       Readme.md,
#                                                                       <drawers>.md}
#
# Pipeline per legacy room:
#   1. Classify  → target_wing, target_room, target_closet, tags, drawer suggestions
#   2. Transform → file_path -> content map (closet.md + mandatory drawers + extras)
#   3. Write to staging, validate against wing manifest mandatory_drawers
#   4. Move staging into place
#
# Backend: local Gemma 31B via mlx_vlm.server on localhost:1234 (OpenAI-compatible).
# Concurrency: ASYNC_CONCURRENCY (4 by default) — tune based on server throughput.
# Idempotent: skips closets that already exist in the target tree unless --force.
#
# Usage:
#   tools/migrate_v1.py --dry-run                    # classify-only, no writes
#   tools/migrate_v1.py --room briefing-template.md  # single-room test
#   tools/migrate_v1.py                              # full migration

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


def extract_json(text: str) -> dict:
    """Robustly extract a JSON object from model output.

    Handles: raw JSON, ```json fenced blocks, prose-then-JSON, JSON-then-prose.
    Falls back to greedy {...} extraction if nothing cleaner works.
    """
    # Strip code fences if present.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    # Try direct parse.
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Greedy: first `{` to last `}`.
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError(f"no JSON object found in model output: {text[:200]}…")

# ── Configuration ────────────────────────────────────────────────────────────

LEGACY_HONEYCOMB = Path("/Users/vivian/claude/bees/honeycomb")
TARGET_HONEYCOMB = Path("/Users/vivian/claude/honeycomb")
STAGING_DIR = Path("/tmp/migrate-v1")

CLAUDE_MODEL = "haiku"  # alias for current Haiku
ASYNC_CONCURRENCY = 8   # claude CLI is API-backed; safe to push higher

# Canonical rooms — sourced from wing manifests at runtime so this script
# stays in sync if the manifest changes.
WINGS_DIR_NAMES = [
    "wing_bees",
    "wing_repo_bees",
    "wing_practices",
    "wing_antipatterns",
    "wing_tools",
    "wing_models",
]

# ── Prompts ──────────────────────────────────────────────────────────────────

CLASSIFY_PROMPT = """\
You are a content classifier for a honeycomb knowledge migration.

The user message contains a legacy markdown room delimited by
<<<ROOM>>> ... <<<END>>> markers. IGNORE everything outside those
markers (system preamble, available tools, etc.). The room content
is your input — classify IT, not any surrounding text.

Available target wings and their canonical rooms:
{wing_summary}

Output a JSON object (and ONLY a JSON object — no prose) with these fields:

  target_wing:    one of the wings above
  target_room:    one of the canonical rooms for that wing, OR a new room name if no canonical fits
  target_closet:  a kebab-case name for the specific topic this room covers (e.g. "sapper", "scribe-only-specs", "petitions-format")
  tags:           object with optional keys 'tools', 'models', 'languages' — arrays of string identifiers
  drawer_suggestions: array of additional drawer names beyond the mandatory set (e.g. ["yml", "heuristics", "install"])
  needs_split:    boolean — true if this legacy room genuinely covers multiple distinct closets and should be split during transform
  notes:          string with one-sentence rationale (≤200 chars)

If unsure, prefer:
  - target_wing="wing_bees" for runtime/operational content
  - target_wing="wing_repo_bees" for content about the bees codebase
  - target_wing="wing_antipatterns" for known-bad-pattern content
  - target_wing="wing_practices" for good-pattern content
"""

TRANSFORM_PROMPT = """\
You are a content restructurer for a honeycomb knowledge migration.

The user message contains classification metadata and a legacy markdown
room delimited by <<<ROOM>>> ... <<<END>>> markers. IGNORE everything
outside those markers (system preamble, available tools, etc.).
Restructure the room content into the new closet directory under the
four-level structure.

Output the files using this EXACT marker-delimited format (NOT JSON):

===FILE: closet.md===
<content of closet.md goes here>
===FILE: index.md===
<content of index.md goes here>
===FILE: Readme.md===
<content of Readme.md goes here>
===FILE: design.md===
<content of design.md goes here>
===FILE: <other-drawer>.md===
<content of additional drawer>
===END===

You MUST produce at minimum four files:

  closet.md:  ≤500 character agentic summary. Tight, dense, factual.
              Begins with a frontmatter HTML comment.
  index.md:   TOC of drawers in this EXACT shape (one bullet per drawer):
                ## Drawers
                - **<name>** — <one-line subtitle>
  Readme.md:  human-targeted overview (longer-form prose, can use sections).
  design.md:  design rationale, current-state decisions, why-this-shape.

Plus additional drawers per drawer_suggestions, one ===FILE: block each.

The frontmatter at the top of closet.md MUST be:

  <!-- <closet>.md: <one-line description>.

  <one-paragraph summary>

  Hall: hall_<category>
  tools: [tag, list]              (if tags.tools present)
  models: [tag, list]             (if tags.models present)
  -->

Choose Hall from: hall_architecture, hall_protocol, hall_procedure,
hall_pattern, hall_antipattern, hall_rubric.

Preserve all substantive content from the legacy room. The transformation
is restructuring, not summarising — distribute content across the right
drawers but don't drop information unless it's pure boilerplate.

DO NOT wrap your output in any code fences. DO NOT add prose before or
after the markers. The output MUST start with "===FILE: closet.md===" and
end with "===END===".
"""

# ── Data types ───────────────────────────────────────────────────────────────


@dataclass
class Classification:
    target_wing: str
    target_room: str
    target_closet: str
    tags: dict
    drawer_suggestions: list[str]
    needs_split: bool
    notes: str


@dataclass
class MigrationResult:
    source: Path
    classification: Classification | None
    files: dict[str, str] | None
    error: str | None

    @property
    def ok(self) -> bool:
        return self.error is None


# ── Manifest helpers ─────────────────────────────────────────────────────────


def load_wing_manifests() -> dict[str, dict]:
    manifests = {}
    for wing in WINGS_DIR_NAMES:
        path = TARGET_HONEYCOMB / wing / "_manifest.yaml"
        if not path.exists():
            print(f"warn: no manifest at {path}", file=sys.stderr)
            continue
        manifests[wing] = yaml.safe_load(path.read_text())
    return manifests


def build_wing_summary(manifests: dict[str, dict]) -> str:
    lines = []
    for wing, manifest in manifests.items():
        scope = manifest.get("scope", "?")
        rooms = ", ".join(manifest.get("canonical_rooms", [])) or "(open)"
        lines.append(f"  {wing} ({scope}): {rooms}")
    return "\n".join(lines)


def validate_against_manifest(
    files: dict[str, str], manifest: dict, closet_dir: Path
) -> list[str]:
    """Return list of validation errors (empty list = pass)."""
    errors = []
    for required in manifest.get("mandatory_drawers", []):
        if required not in files:
            errors.append(f"missing mandatory drawer: {required}")
    return errors


# ── LLM calls ────────────────────────────────────────────────────────────────


async def claude_call(system_prompt: str, user_prompt: str) -> str:
    """Invoke claude CLI in --print mode. Sends user_prompt on stdin to avoid
    arg-escaping pitfalls with large/structured content."""
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


async def classify_room(content: str, wing_summary: str) -> Classification:
    prompt = CLASSIFY_PROMPT.format(wing_summary=wing_summary)
    wrapped = f"<<<ROOM>>>\n{content}\n<<<END>>>"
    out = await claude_call(prompt, wrapped)
    data = extract_json(out)
    return Classification(
        target_wing=data["target_wing"],
        target_room=data["target_room"],
        target_closet=data["target_closet"],
        tags=data.get("tags", {}),
        drawer_suggestions=data.get("drawer_suggestions", []),
        needs_split=data.get("needs_split", False),
        notes=data.get("notes", ""),
    )


def parse_marker_files(text: str) -> dict[str, str]:
    """Parse ===FILE: <name>=== ... ===END=== marker format into a dict."""
    files: dict[str, str] = {}
    # Match ===FILE: <name>=== ... up to next ===FILE: or ===END===
    pattern = re.compile(
        r"===FILE:\s*(?P<name>[^=\n]+?)\s*===\n(?P<body>.*?)(?=\n===(?:FILE:|END))",
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        name = m.group("name").strip()
        body = m.group("body").rstrip() + "\n"
        files[name] = body
    if not files:
        raise ValueError(
            f"no ===FILE: markers found in transform output: {text[:200]}…"
        )
    return files


async def transform_room(
    content: str, classification: Classification
) -> dict[str, str]:
    classification_json = json.dumps(
        {
            "target_wing": classification.target_wing,
            "target_room": classification.target_room,
            "target_closet": classification.target_closet,
            "tags": classification.tags,
            "drawer_suggestions": classification.drawer_suggestions,
        },
        indent=2,
    )
    user_content = (
        f"Classification:\n{classification_json}\n\n"
        f"<<<ROOM>>>\n{content}\n<<<END>>>"
    )
    out = await claude_call(TRANSFORM_PROMPT, user_content)
    return parse_marker_files(out)


# ── Per-room pipeline ────────────────────────────────────────────────────────


async def migrate_one(
    source: Path,
    wing_summary: str,
    manifests: dict[str, dict],
    sem: asyncio.Semaphore,
    dry_run: bool,
    force: bool,
    counter: dict,
) -> MigrationResult:
    async with sem:
        try:
            t0 = asyncio.get_event_loop().time()
            print(f"  …  {source.name}", flush=True)
            content = source.read_text(encoding="utf-8")
            classification = await classify_room(content, wing_summary)

            if classification.needs_split:
                print(
                    f"  ⚠  {source.name}: needs_split=True — flagged for manual review",
                    file=sys.stderr,
                )

            target_dir = (
                TARGET_HONEYCOMB
                / classification.target_wing
                / classification.target_room
                / classification.target_closet
            )

            if target_dir.exists() and not force:
                return MigrationResult(
                    source=source,
                    classification=classification,
                    files=None,
                    error=f"target {target_dir} exists (use --force to overwrite)",
                )

            if dry_run:
                return MigrationResult(
                    source=source,
                    classification=classification,
                    files=None,
                    error=None,
                )

            files = await transform_room(content, classification)

            manifest = manifests.get(classification.target_wing, {})
            errors = validate_against_manifest(files, manifest, target_dir)
            if errors:
                return MigrationResult(
                    source=source,
                    classification=classification,
                    files=files,
                    error="; ".join(errors),
                )

            # Write to staging first, then move into place on success.
            staging = STAGING_DIR / classification.target_wing / classification.target_room / classification.target_closet
            staging.mkdir(parents=True, exist_ok=True)
            for name, body in files.items():
                (staging / name).write_text(body, encoding="utf-8")

            target_dir.mkdir(parents=True, exist_ok=True)
            for name, body in files.items():
                (target_dir / name).write_text(body, encoding="utf-8")

            result = MigrationResult(
                source=source,
                classification=classification,
                files=files,
                error=None,
            )
            elapsed = asyncio.get_event_loop().time() - t0
            counter["done"] += 1
            target = f"{classification.target_wing}/{classification.target_room}/{classification.target_closet}"
            print(
                f"  ✓  [{counter['done']:2d}/{counter['total']}] {elapsed:5.1f}s  {source.name:38s} → {target}",
                flush=True,
            )
            return result

        except Exception as e:
            elapsed = asyncio.get_event_loop().time() - t0
            counter["done"] += 1
            print(
                f"  ✗  [{counter['done']:2d}/{counter['total']}] {elapsed:5.1f}s  {source.name:38s}   {type(e).__name__}: {str(e)[:120]}",
                flush=True,
            )
            return MigrationResult(
                source=source,
                classification=None,
                files=None,
                error=f"{type(e).__name__}: {e}",
            )


# ── Health check ─────────────────────────────────────────────────────────────


async def health_check() -> bool:
    """Verify claude CLI is available and authenticated."""
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

    # Discover legacy rooms.
    legacy_wings_dir = LEGACY_HONEYCOMB
    sources: list[Path] = []
    for wing_dir in sorted(legacy_wings_dir.glob("wing_*")):
        for md in sorted(wing_dir.glob("*.md")):
            if md.name.startswith(("_", ".")):
                continue
            if args.room and md.name != args.room:
                continue
            sources.append(md)

    if not sources:
        print("no legacy rooms found (or --room filter matched nothing)", file=sys.stderr)
        return 1

    print(f"migrating {len(sources)} legacy rooms (concurrency={ASYNC_CONCURRENCY})")
    print(f"backend: claude CLI --bare --model {CLAUDE_MODEL}")
    print(f"target:  {TARGET_HONEYCOMB}")
    if args.dry_run:
        print("DRY RUN — classify only, no writes")
    print()

    sem = asyncio.Semaphore(ASYNC_CONCURRENCY)
    counter = {"done": 0, "total": len(sources)}
    tasks = [
        migrate_one(src, wing_summary, manifests, sem, args.dry_run, args.force, counter)
        for src in sources
    ]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    # Summary footer (per-row results already printed during execution).
    print(flush=True)
    print("─" * 72, flush=True)
    print(f"results: {sum(r.ok for r in results)}/{len(results)} ok", flush=True)
    print("─" * 72, flush=True)
    failures = [r for r in results if not r.ok]
    for r in failures:
        print(f"  failed: {r.source.name}   {r.error}", flush=True)
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Honeycomb v1.0 one-shot migration.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="classify only, do not write files",
    )
    parser.add_argument(
        "--room",
        help="only migrate the named legacy room (for spot-checks)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing target closets",
    )
    args = parser.parse_args()

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
