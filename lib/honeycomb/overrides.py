"""honeycomb.overrides — parse drawer override files with HTML-comment frontmatter."""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


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
