---
output-files: [lib/honeycomb/overrides.py, tests/test_overrides_parse.py]
scribe-model: claude-opus-4-7
---

# Spec 001 — Override file format + frontmatter parser

## Builder model

claude-sonnet-4-6

## Goal

Add `lib/honeycomb/overrides.py` exposing an `OverrideSpec` dataclass and `parse_override_file(path) -> OverrideSpec` that parses the HTML-comment frontmatter at the top of an override drawer file (`target`, `tool`, `tool_version`, `consumer`, `rationale`), and establish the project's stdlib-unittest test convention.

## Scope

**Files to create**
- `lib/honeycomb/overrides.py`
- `tests/test_overrides_parse.py`

**Public symbols in `lib/honeycomb/overrides.py`**
- `OverrideSpec` — frozen `@dataclass` with fields:
  - `path: pathlib.Path` — the override file path
  - `target: str` — the canonical drawer name this override targets (e.g. `"behaviour"`)
  - `tool: Optional[str]` — tool axis (e.g. `"bees"`); `None` when unscoped on this axis
  - `tool_version: Optional[str]` — version expression as written (e.g. `">=v1.18"`, `"==v1.18"`, `"v1.18"`); `None` when unscoped
  - `consumer: Optional[str]` — consumer name (e.g. `"scarab"`); `None` when unscoped (matches "any consumer")
  - `rationale: str` — free-text rationale; empty string when not provided
  - `body: str` — the post-frontmatter override content body
- `parse_override_file(path: pathlib.Path) -> OverrideSpec`
- `class OverrideParseError(ValueError)` — raised when the frontmatter is missing or `target:` is absent. Other fields are optional and default to `None` / `""`.

**Frontmatter format the parser accepts**

The override file begins with an HTML comment whose body contains key/value lines and an optional multi-line `rationale: |` block. Example matching ADR-0002:

```markdown
<!-- behaviour.queenfile_bees-v1.18.md: bees v1.18 override.

target: behaviour
tool: bees
tool_version: ">=v1.18"
consumer: null
rationale: |
  v1.18 introduces the scoped recall context. Builders need to pass
  tool_version through queries; spec contract documents this.
-->

<override content body — replaces behaviour.md when this scope applies>
```

Parser rules:
- The HTML comment must be the first non-whitespace content in the file. If absent, raise `OverrideParseError`.
- Recognise lines of the form `^\s*<key>:\s*<value>\s*$` for the four scalar keys (`target`, `tool`, `tool_version`, `consumer`).
- Strip surrounding double-quotes from values (so `tool_version: ">=v1.18"` yields `">=v1.18"`).
- Treat the unquoted literal `null` (case-insensitive) on a scalar line as Python `None`.
- `rationale: |` introduces a literal block — every subsequent line that begins with leading whitespace belongs to the block; the block ends at the first non-indented line (or comment terminator). Dedent the block to its minimum common indent and `rstrip()` trailing whitespace; the result is the `rationale` string.
- `target:` is required; missing → `OverrideParseError`.
- The post-frontmatter body is everything after `-->` with one leading newline stripped (preserve interior formatting). Store on `OverrideSpec.body`.
- The **filename is a hint only** — the parser MUST NOT infer fields from `<name>.queenfile_<scope>.md`. Frontmatter is authoritative.

**Non-goals (defer to spec 002)**
- Specificity ranking, context matching, candidate resolution.
- Walking a directory to discover overrides.
- Materialising a flattened view.

## Failing test

`tests/test_overrides_parse.py` — written using stdlib `unittest`, runnable with `python3 -m unittest discover -s tests`. Establishes the project's test convention (no third-party deps; one test module per public module).

Required test cases (each a separate `test_*` method on a `unittest.TestCase`):

1. `test_parses_tool_and_version_override` — fixture matches the ADR-0002 example above; asserts `target == "behaviour"`, `tool == "bees"`, `tool_version == ">=v1.18"`, `consumer is None`, `rationale` contains the multi-line text dedented, and `body` starts with `<override content body`.
2. `test_consumer_only_override` — fixture with `consumer: scarab` and `tool: null` / `tool_version: null`; asserts `consumer == "scarab"` and both tool fields are `None`.
3. `test_filename_is_hint_only` — fixture's filename is `behaviour.queenfile_bees-v1.18.md` but its frontmatter declares `tool: scarab` (a different scope); asserts the returned `OverrideSpec.tool == "scarab"` (frontmatter wins, filename ignored).
4. `test_missing_frontmatter_raises` — file starts with body content directly; asserts `OverrideParseError` is raised.
5. `test_missing_target_raises` — frontmatter exists but lacks a `target:` line; asserts `OverrideParseError`.
6. `test_rationale_optional` — frontmatter omits `rationale:`; asserts `rationale == ""` and parsing succeeds.

Fixtures are written to a per-test `tempfile.TemporaryDirectory()` so the suite has no on-disk dependencies.

The failing test exists before the module does — `parse_override_file` will be importable only after the builder writes `lib/honeycomb/overrides.py`.

## Builder prompt

You are writing one new module and its unit tests for the honeycomb v1.1 drawer-overrides mechanism. Both files live in the repo; no edits to other files.

**Repo layout you need to know**
- `lib/honeycomb/` already contains `__init__.py`, `recall.py`, `semantic.py`. Add `overrides.py` next to them. Do NOT export the new symbols from `__init__.py` in this spec — a later spec consolidates the re-exports.
- `tests/` is currently empty. Your test file establishes the convention: stdlib `unittest` only, no pytest, no third-party deps. The full suite is run via `python3 -m unittest discover -s tests`.

**Module to create — `lib/honeycomb/overrides.py`**

Implement:

```python
from __future__ import annotations
from dataclasses import dataclass, field
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


def parse_override_file(path: Path) -> OverrideSpec:
    ...
```

Parser contract (see Scope above for the field grammar):
- Read the file as UTF-8 with `errors="replace"`.
- The first non-whitespace content must be an HTML comment `<!-- ... -->`. Use `re.compile(r"\A\s*<!--(.*?)-->", re.DOTALL)`. Missing → `OverrideParseError("missing frontmatter comment")`.
- Inside the comment, walk lines in order. Recognise scalar keys with `^\s*(target|tool|tool_version|consumer):\s*(.+?)\s*$`. Strip wrapping `"` from the value. The unquoted literal `null` (case-insensitive, after quote strip) → Python `None`.
- Recognise `^\s*rationale:\s*\|\s*$` as the start of a literal block; collect every following indented line (lines whose first non-empty character is preceded by at least one space/tab) until you hit a non-indented line or the comment terminator. Dedent using `textwrap.dedent` after stripping the common leading whitespace, then `rstrip()`.
- `target:` is required. Missing → `OverrideParseError("override missing 'target:' field")`.
- `body` is `text[m.end():]` with one leading `\n` stripped if present (preserve interior whitespace and trailing newline).
- Return `OverrideSpec(path=path, target=..., tool=..., tool_version=..., consumer=..., rationale=..., body=...)`.

**Tests to create — `tests/test_overrides_parse.py`**

Use stdlib `unittest`. Each test writes its fixture to a `tempfile.TemporaryDirectory()` (use `setUp`/`tearDown` or a `with` block per test). The six cases listed in Failing test above. Inline the fixture text as a triple-quoted string in each test; do NOT add a separate fixtures directory. Sample skeleton:

```python
import tempfile
import textwrap
import unittest
from pathlib import Path

from honeycomb.overrides import (
    OverrideParseError,
    OverrideSpec,
    parse_override_file,
)


class ParseOverrideFileTests(unittest.TestCase):
    def _write(self, name: str, content: str) -> Path:
        d = Path(self._tmp.name)
        p = d / name
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_parses_tool_and_version_override(self) -> None:
        ...
```

Notes on imports: the module is imported as `from honeycomb.overrides import ...` (the package is `honeycomb` — see `lib/honeycomb/__init__.py`). The test runner discovers `tests/test_*.py` from the repo root and `lib/` is on `sys.path` because of the existing project layout — if you find imports fail, prepend `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))` at the top of the test module (mirroring how `recall.py` is reached today).

**Constraints**
- No third-party dependencies — stdlib only (`re`, `dataclasses`, `pathlib`, `typing`, `textwrap`).
- No mutation: `OverrideSpec` is `frozen=True`.
- The filename is NOT consulted to derive any field. The parser may be passed a file named `random.md` and must still return correct values if the frontmatter is well-formed.
- Keep comments minimal — only the module docstring and a 1-line comment above the frontmatter regex are warranted.

**Success check**
- `python3 -m unittest discover -s tests -v` exits 0 with all six new test methods listed as `ok`.
- `python3 -c "from honeycomb.overrides import OverrideSpec, parse_override_file, OverrideParseError"` imports cleanly.

## Success check

- `python3 -m unittest discover -s tests -v` runs from the repo root with all six test methods passing.
- `lib/honeycomb/overrides.py` exists, defines `OverrideSpec` (frozen dataclass), `OverrideParseError`, and `parse_override_file`.
- `tests/test_overrides_parse.py` uses only stdlib `unittest`; no pytest or third-party imports.
- Diff review: no edits to `lib/honeycomb/__init__.py`, `recall.py`, `semantic.py`, or any other existing file.

## Commit message

```
feat(honeycomb): add override file parser and OverrideSpec dataclass (#001)

Introduces lib/honeycomb/overrides.py with the OverrideSpec frozen
dataclass and parse_override_file(), which reads the HTML-comment
frontmatter (target, tool, tool_version, consumer, rationale) at the
top of a drawer override. Filename is treated as a hint only;
frontmatter is authoritative.

Establishes the project's test-suite convention: stdlib unittest under
tests/, runnable via `python3 -m unittest discover -s tests`.

Refs: .bees/honeycomb-v1-1/specs/001-override-file-format-and-parser.md
```
