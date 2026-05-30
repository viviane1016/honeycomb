"""honeycomb.overrides — parse drawer override files with HTML-comment frontmatter."""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

__all__ = [
    "OverrideParseError",
    "OverrideSpec",
    "parse_override_file",
    "ResolutionContext",
    "RankedMatch",
    "rank_by_specificity",
    "resolve_overrides",
]


class OverrideParseError(ValueError):
    """Raised when an override file's frontmatter is missing or malformed."""


@dataclass(frozen=True)
class OverrideSpec:
    path: Path
    target: str
    tool: Optional[str] = None
    tool_version: Optional[str] = None
    consumer: Optional[str] = None
    rationale: str = ""
    body: str = ""


# Matches the opening HTML comment block (first in file, allows leading whitespace)
_COMMENT_RE = re.compile(r"\A\s*<!--(.*?)-->", re.DOTALL)

_SCALAR_RE = re.compile(r"^\s*(target|tool|tool_version|consumer):\s*(.+?)\s*$")
_RATIONALE_START_RE = re.compile(r"^\s*rationale:\s*\|\s*$")


def _parse_value(raw: str) -> Optional[str]:
    v = raw.strip('"')
    if v.lower() == "null":
        return None
    return v


def parse_override_file(path: Path) -> OverrideSpec:
    text = path.read_text(encoding="utf-8", errors="replace")

    m = _COMMENT_RE.match(text)
    if m is None:
        raise OverrideParseError("missing frontmatter comment")

    comment_body = m.group(1)
    fields: dict = {}
    rationale_lines: list[str] = []
    in_rationale = False

    for line in comment_body.splitlines():
        if in_rationale:
            # A line that starts with at least one space/tab continues the block
            if line and (line[0] == " " or line[0] == "\t"):
                rationale_lines.append(line)
            else:
                in_rationale = False

        if not in_rationale:
            if _RATIONALE_START_RE.match(line):
                in_rationale = True
                continue
            scalar = _SCALAR_RE.match(line)
            if scalar:
                key, raw = scalar.group(1), scalar.group(2)
                fields[key] = _parse_value(raw)

    if "target" not in fields:
        raise OverrideParseError("override missing 'target:' field")

    rationale = ""
    if rationale_lines:
        rationale = textwrap.dedent("\n".join(rationale_lines)).rstrip()

    body = text[m.end():]
    if body.startswith("\n"):
        body = body[1:]

    return OverrideSpec(
        path=path,
        target=fields["target"],
        tool=fields.get("tool"),
        tool_version=fields.get("tool_version"),
        consumer=fields.get("consumer"),
        rationale=rationale,
        body=body,
    )


# ---------------------------------------------------------------------------
# Override resolution
# ---------------------------------------------------------------------------

@dataclass
class ResolutionContext:
    """Describes the installation environment used to filter and rank overrides."""
    tool: Optional[str] = None
    tool_version: Optional[str] = None
    consumer: Optional[str] = None


@dataclass
class RankedMatch:
    """A surviving override candidate with its sort key."""
    spec: OverrideSpec
    path: Path
    score: tuple  # (axes_matched, version_exactness, consumer_exactness, mtime_epoch)


def _parse_tv_op(tv: str) -> tuple:
    """Split a tool_version value into (operator, version_string).

    Returns ('>=', 'v1.17') for '>=v1.17', ('==', 'v1.18') for '==v1.18',
    and ('', value) for bare scalars.
    """
    if tv.startswith(">="):
        return (">=", tv[2:])
    if tv.startswith("=="):
        return ("==", tv[2:])
    return ("", tv)


def _version_matches(spec_tv: Optional[str], ctx_tv: str) -> bool:
    """Return True if spec's tool_version value is compatible with ctx_tv.

    For >= ranges: uses lexicographic string comparison (e.g. '>=v1.17' matches
    'v1.18' because 'v1.18' >= 'v1.17' lex). This is NOT semver-aware — it can
    produce incorrect results when minor/patch components differ in digit count
    (e.g. 'v1.9' > 'v1.10' lexicographically). Semver-aware matching is a
    non-goal for v1.1.
    """
    if spec_tv is None:
        return True
    op, ver = _parse_tv_op(spec_tv)
    if op == ">=":
        return ctx_tv >= ver
    # == or bare scalar: exact match
    return ctx_tv == ver


def rank_by_specificity(
    matches: list,
    context: ResolutionContext,
) -> list:
    """Filter and rank override candidates against *context*.

    **Filtering**: any (spec, path) pair is dropped if a *populated* context
    axis (non-None) conflicts with the spec's value. An axis is compatible if
    the spec value is None (wildcard) or explicitly matches the context value.
    For ``tool_version`` the ``>=vX`` form uses a lexicographic comparison —
    see ``_version_matches`` for the documented limitation.

    **Scoring**: each survivor receives a four-tuple
    ``(axes_matched, version_exactness, consumer_exactness, mtime_epoch)``
    where higher values are better.

    Returns the surviving ``RankedMatch`` list sorted by score descending.
    """
    result = []
    for spec, path in matches:
        # --- axis filtering ---
        if context.tool is not None:
            if spec.tool is not None and spec.tool != context.tool:
                continue

        if context.tool_version is not None:
            if not _version_matches(spec.tool_version, context.tool_version):
                continue

        if context.consumer is not None:
            if spec.consumer is not None and spec.consumer != context.consumer:
                continue

        # --- scoring ---
        axes_matched = 0
        if context.tool is not None and spec.tool is not None:
            axes_matched += 1
        if context.tool_version is not None and spec.tool_version is not None:
            axes_matched += 1
        if context.consumer is not None and spec.consumer is not None:
            axes_matched += 1

        if spec.tool_version is None:
            version_exactness = 0
        else:
            op, _ = _parse_tv_op(spec.tool_version)
            version_exactness = 1 if op == ">=" else 2

        consumer_exactness = 1 if spec.consumer is not None else 0

        mtime = path.stat().st_mtime
        score = (axes_matched, version_exactness, consumer_exactness, mtime)
        result.append(RankedMatch(spec=spec, path=path, score=score))

    result.sort(key=lambda m: m.score, reverse=True)
    return result


def resolve_overrides(
    candidates: dict,
    context: ResolutionContext,
) -> tuple:
    """Pick one winning override path per drawer key.

    *candidates* maps drawer paths to lists of (OverrideSpec, Path) tuples.
    Returns ``(winners, ambiguous)`` where:
    - ``winners`` maps drawer key → winning override Path
    - ``ambiguous`` lists drawer keys where the top two matches tied on the
      first three score components (axes/version/consumer) and only mtime
      broke the tie — a lint signal, not an error.

    Drawers whose every candidate fails axis filtering are omitted from both
    return values.
    """
    winners: dict = {}
    ambiguous: list = []

    for drawer, candidate_list in candidates.items():
        ranked = rank_by_specificity(candidate_list, context)
        if not ranked:
            continue

        winners[drawer] = ranked[0].path

        if len(ranked) >= 2 and ranked[0].score[:3] == ranked[1].score[:3]:
            ambiguous.append(drawer)

    return winners, ambiguous
