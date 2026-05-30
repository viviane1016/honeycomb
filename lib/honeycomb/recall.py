# lib/honeycomb/recall.py — keyword palace_recall over the four-level
# wing/room/closet/drawer structure (honeycomb v1.0).
#
# Walks <root>/wing_*/<room>/<closet>/ directories, parses each closet's
# closet.md for the frontmatter (Hall, tags) and body, scores against a
# query, and returns the top-K matches.
#
# Return shape is unchanged from legacy bees-honeycomb to preserve the MCP
# contract:
#   {"wing": "wing_bees", "room": "build/manual-amend", "hall": "hall_procedure",
#    "path": "<closet.md path>", "closet": "<closet text>",
#    "drawer": "<full canonical content>" (only when drawer=True)}
# Note: the `room` field is a COMPOSITE "<room>/<closet>" so the same room
# can host multiple closets without collision in the response.
#
# Forward-compat: extension points for `scope`, `tools`, `models` params are
# noted (commented stubs) — they'll be wired in v1.1 once we want to refine
# what gets returned in context.

from __future__ import annotations

import fcntl
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

# ── Frontmatter parsing ──────────────────────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"\A<!--(.*?)-->", re.DOTALL)
_HALL_RE = re.compile(r"^\s*Hall:\s*(hall_\w+)\s*$", re.MULTILINE)
_TAG_RE = re.compile(r"^\s*(tools|models|languages):\s*\[([^\]]*)\]\s*$", re.MULTILINE)


def _parse_frontmatter(text: str) -> tuple[Optional[str], dict[str, list[str]], str]:
    """Return (hall, tags, body_after_frontmatter). hall may be None."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None, {}, text.lstrip()
    fm = m.group(1)
    body = text[m.end():].lstrip()
    hall_match = _HALL_RE.search(fm)
    hall = hall_match.group(1) if hall_match else None
    tags: dict[str, list[str]] = {}
    for tm in _TAG_RE.finditer(fm):
        key, raw = tm.group(1), tm.group(2)
        vals = [v.strip() for v in raw.split(",") if v.strip()]
        if vals:
            tags[key] = vals
    return hall, tags, body


# ── Closet discovery ────────────────────────────────────────────────────────


def _discover_closets(root: Path) -> list[dict]:
    """Walk <root>/wing_*/<room>/<closet>/ and return one dict per closet.

    Each dict has: wing, room, closet, path (closet.md), full_dir, hall, tags,
    closet_text, drawer_text (lazy via _read_drawer_text)."""
    if not root.exists() or not root.is_dir():
        return []

    closets: list[dict] = []
    for wing_dir in sorted(root.iterdir()):
        if not (wing_dir.is_dir() and wing_dir.name.startswith("wing_")):
            continue
        wing = wing_dir.name
        for room_dir in sorted(wing_dir.iterdir()):
            if not room_dir.is_dir() or room_dir.name.startswith((".", "_")):
                continue
            room = room_dir.name
            for closet_dir in sorted(room_dir.iterdir()):
                if not closet_dir.is_dir() or closet_dir.name.startswith((".", "_")):
                    continue
                closet_name = closet_dir.name
                closet_path = closet_dir / "closet.md"
                if not closet_path.is_file():
                    continue
                try:
                    text = closet_path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                hall, tags, body = _parse_frontmatter(text)
                closets.append({
                    "wing": wing,
                    "room": room,
                    "closet": closet_name,
                    "path": closet_path,
                    "full_dir": closet_dir,
                    "hall": hall,
                    "tags": tags,
                    "closet_text": body,
                })
    return closets


def _read_drawer_text(closet_dir: Path) -> str:
    """Concatenate all drawer files in the closet directory.

    Excludes closet.md (already in `closet_text`) and index.md (TOC, not
    content). Tunnels are included as they're canonical references."""
    parts: list[str] = []
    excluded = {"closet.md", "index.md"}
    for f in sorted(closet_dir.iterdir()):
        if not f.is_file() or f.suffix != ".md" or f.name in excluded:
            continue
        if f.name.startswith(("_", ".")):
            continue
        try:
            parts.append(f.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n\n".join(parts)


# ── Scoring ──────────────────────────────────────────────────────────────────


def _normalize(query: str) -> str:
    return " ".join(query.lower().split())


def _tokens(query: str) -> list[str]:
    return [t for t in _normalize(query).split() if len(t) >= 3]


def score_match(query: str, closet: dict) -> int:
    """Score a closet against a query. Returns 0 for no match.

    Weights: closet/room/closet-name substring match = 100; token in closet
    text = 10; token in drawer text = 1. Same weights as legacy bees_honeycomb
    so scores are comparable for side-by-side validation."""
    norm_q = _normalize(query)
    if not norm_q:
        return 0
    score = 0
    name_blob = f"{closet['room']} {closet['closet']}".lower()
    if norm_q in name_blob:
        score += 100
    closet_text = (closet.get("closet_text") or "").lower()
    drawer_text = _read_drawer_text(closet["full_dir"]).lower()
    for tok in _tokens(query):
        if tok in closet_text:
            score += 10
        if tok in drawer_text:
            score += 1
    return score


# ── Filter normalisation ─────────────────────────────────────────────────────


def _normalize_wing_filter(wings: Optional[Iterable[str]]) -> Optional[set[str]]:
    if wings is None:
        return None
    out: set[str] = set()
    for w in wings:
        if not w:
            continue
        out.add(w if w.startswith("wing_") else f"wing_{w}")
    return out


def _normalize_hall_filter(halls: Optional[Iterable[str]]) -> Optional[set[str]]:
    if halls is None:
        return None
    out: set[str] = set()
    for h in halls:
        if not h:
            continue
        out.add(h if h.startswith("hall_") else f"hall_{h}")
    return out


# ── Trace writing (side-effect, preserved from legacy contract) ──────────────


def _resolve_repo_root(repo_root: Optional[Path]) -> Optional[Path]:
    if repo_root is not None:
        return Path(repo_root)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return None
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip())
    return None


def _write_trace(
    repo_root: Path,
    slug: str,
    query: str,
    wings,
    halls,
    drawer: bool,
    results: list[dict],
) -> None:
    bees_dir = repo_root / ".bees" / slug
    if not bees_dir.is_dir():
        return
    trace_path = bees_dir / "honeycomb-trace.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"## {ts}",
        "",
        f"- query: {query}",
        f"- wings: {', '.join(wings) if wings else 'all'}",
        f"- halls: {', '.join(halls) if halls else 'all'}",
        f"- drawer: {drawer}",
        "- returned:",
    ]
    for r in results:
        lines.append(f"  - {r['wing']}/{r['room']}")
    lines.append("")
    block = "\n".join(lines) + "\n"
    with trace_path.open("a", encoding="utf-8") as f:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(block)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


_FALLBACK_SECRET_PATTERNS = [
    r"sk-ant-[A-Za-z0-9_\-]{20,}",
    r"ghp_[A-Za-z0-9]{30,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
]
_compiled_fallback = None


def _scan_query(query: str) -> list[str]:
    """Detect secret patterns in the query before tracing.

    Honeycomb is standalone (no bees CLI dep); we use the fallback set
    embedded here. Returns list of matched pattern strings (empty = clean).
    """
    global _compiled_fallback
    if _compiled_fallback is None:
        _compiled_fallback = [re.compile(p) for p in _FALLBACK_SECRET_PATTERNS]
    return [p.pattern for p in _compiled_fallback if p.search(query)]


# ── Public API ───────────────────────────────────────────────────────────────


def _default_root() -> Path:
    """Default honeycomb root — env var, then auto-detect from this file."""
    import os
    raw = os.environ.get("HONEYCOMB_ROOT")
    if raw:
        return Path(raw)
    # lib/honeycomb/recall.py → <repo>/lib/honeycomb → <repo>
    return Path(__file__).resolve().parent.parent.parent


def palace_recall(
    query: str,
    wings: Optional[Iterable[str]] = None,
    halls: Optional[Iterable[str]] = None,
    top_k: int = 3,
    drawer: bool = False,
    *,
    # v1.1 extension points (not yet wired — accepted-and-ignored for now):
    scope: Optional[str] = None,        # "runtime" | "universal" | "project:<X>"
    tools: Optional[Iterable[str]] = None,
    models: Optional[Iterable[str]] = None,
    project: Optional[str] = None,
    overlay_root: Optional[Path] = None,
    # Legacy side-effect parameters (trace writing):
    slug: Optional[str] = None,
    root: Optional[Path] = None,
    repo_root: Optional[Path] = None,
) -> list[dict]:
    """Keyword recall over the honeycomb four-level structure.

    Returns a list of result dicts ranked by relevance, top-K. Shape preserved
    from legacy bees_honeycomb to keep the MCP contract stable:
        {"wing", "room", "hall", "path", "closet", "drawer" (if drawer=True)}
    where `room` is a composite "<room>/<closet>" string.

    The `scope`, `tools`, `models`, `project` params are placeholder
    extension points for v1.1 targeted recall — currently accepted and
    ignored to keep the call signature forward-compatible.

    overlay_root: Optional consumer-side overlay tree; when set and existing,
        overlay drawer files win over canon at matching (wing, room, closet)
        keys. Absent or non-existent path = canon-only (v1.0 behaviour).
    """
    search_root = Path(root) if root is not None else _default_root()
    closets = _discover_closets(search_root)

    # Overlay merge: walk overlay tree and replace/append on (wing, room, closet).
    if overlay_root is not None and Path(overlay_root).is_dir():
        overlay_closets = _discover_closets(Path(overlay_root))
        if overlay_closets:
            canon_index: dict[tuple, int] = {}
            for i, c in enumerate(closets):
                canon_index[(c["wing"], c["room"], c["closet"])] = i
            for oc in overlay_closets:
                closet_key = re.sub(r"\.queenfile_[^.]+$", "", oc["closet"])
                if closet_key != oc["closet"]:
                    oc = dict(oc, closet=closet_key)
                key = (oc["wing"], oc["room"], oc["closet"])
                if key in canon_index:
                    closets[canon_index[key]] = oc
                else:
                    closets.append(oc)

    if not closets:
        return []

    wing_filter = _normalize_wing_filter(wings)
    hall_filter = _normalize_hall_filter(halls)

    candidates: list[dict] = []
    for c in closets:
        if wing_filter is not None and c["wing"] not in wing_filter:
            continue
        if hall_filter is not None and c.get("hall") not in hall_filter:
            continue
        candidates.append(c)

    scored: list[tuple[int, dict]] = []
    for c in candidates:
        s = score_match(query, c)
        if s > 0:
            scored.append((s, c))

    scored.sort(key=lambda item: (-item[0], item[1]["wing"], item[1]["room"], item[1]["closet"]))
    top = scored[: max(0, int(top_k))]

    results: list[dict] = []
    for _score, c in top:
        entry: dict = {
            "wing": c["wing"],
            "room": f"{c['room']}/{c['closet']}",   # composite to preserve API shape
            "hall": c.get("hall"),
            "path": str(c["path"]),
            "closet": c.get("closet_text") or "",
        }
        if drawer:
            entry["drawer"] = _read_drawer_text(c["full_dir"])
        results.append(entry)

    # Side-effect: write honeycomb-trace.md if slug is set and query is clean.
    if slug and results:
        if not _scan_query(query):
            resolved = _resolve_repo_root(repo_root)
            if resolved is not None:
                _write_trace(resolved, slug, query, wings, halls, drawer, results)

    return results
