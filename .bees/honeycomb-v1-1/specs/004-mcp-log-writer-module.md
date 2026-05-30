---
output-files: [lib/honeycomb/log.py, tests/test_log.py]
scribe-model: claude-opus-4-7
---

# Spec 004 — MCP log writer module

## Builder model

claude-sonnet-4-6

## Goal

Add `lib/honeycomb/log.py` exposing a `write_call_record()` function that appends one JSONL record per MCP tool call to a destination derived from env vars, with actor identity propagation and multi-process-safe locking.

## Scope

**Files created:**
- `lib/honeycomb/log.py`
- `tests/test_log.py`

**Public functions in `lib/honeycomb/log.py`:**
- `resolve_destination() -> pathlib.Path`
- `write_call_record(tool: str, request: dict, response: dict, duration_ms: float) -> None`

**Destination resolution (`resolve_destination`):**
- If both `BEES_REPO_ROOT` and `BEES_FEATURE_SLUG` are set, return `Path($BEES_REPO_ROOT) / ".bees" / <slug> / "mcp-calls.jsonl"`.
- Otherwise return `Path($HONEYCOMB_ROOT or ".") / ".calls.jsonl"`.
- Create parent directories as needed (`mkdir(parents=True, exist_ok=True)`).

**Record schema (every field required; dict serialised as one JSON line + trailing `\n`):**
- `schema_version` (int, always `1`)
- `ts` (str, ISO-8601 UTC, millisecond precision, e.g. `"2026-05-30T12:34:56.789Z"`)
- `tool` (str — argument)
- `slug` (str — `$BEES_FEATURE_SLUG` or `"unknown"`)
- `actor` (str — `$BEES_ACTOR` or `"unknown"`)
- `stage` (str — `$BEES_STAGE` or `"unknown"`)
- `model` (str — `$BEES_MODEL` or `"unknown"`)
- `request` (dict — argument)
- `response` (dict — argument)
- `duration_ms` (float — argument)

**Concurrency model:**
- Open destination in append-text mode.
- Acquire `fcntl.flock(fileno, LOCK_EX)` before writing.
- Write the JSON line, call `f.flush()` for synchronous durability, release the lock in a `finally` block.

**Non-goals:**
- No redaction of sensitive fields (BACKLOG).
- No async / batched writers.
- No wiring into `bin/honeycomb-mcp` (handled in spec 005).
- No edits to `lib/honeycomb/__init__.py` (rely on PEP 420 namespace package or an existing `__init__.py`).

## Failing test

`tests/test_log.py` — class `TestWriteCallRecord(unittest.TestCase)` with four methods, all initially failing because the module does not yet exist:

1. `test_writes_jsonl_record_with_actor_identity` — sets every env var (`BEES_REPO_ROOT=<tmp>`, `BEES_FEATURE_SLUG="feature-x"`, `BEES_ACTOR="queen"`, `BEES_STAGE="plan"`, `BEES_MODEL="claude-opus-4-7"`); calls `write_call_record("palace_recall", {"query": "foo"}, {"closets": []}, 12.5)`; opens `<tmp>/.bees/feature-x/mcp-calls.jsonl`, asserts exactly one line, parses JSON, asserts every schema field is present with the correct value (including `schema_version == 1`, `slug == "feature-x"`, `duration_ms == 12.5`, `request == {"query": "foo"}`, `response == {"closets": []}`, `ts` is a non-empty string).

2. `test_falls_back_to_honeycomb_root_when_slug_missing` — clears `BEES_REPO_ROOT` and `BEES_FEATURE_SLUG`, sets `HONEYCOMB_ROOT=<tmp>`; calls the writer; asserts `<tmp>/.calls.jsonl` exists and contains exactly one valid record.

3. `test_missing_actor_env_writes_unknown` — clears `BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL`, `BEES_FEATURE_SLUG`; sets `BEES_REPO_ROOT=<tmp>`; calls the writer; asserts the JSON record has `actor == "unknown"`, `stage == "unknown"`, `model == "unknown"`, `slug == "unknown"`.

4. `test_concurrent_writes_do_not_corrupt_log` — forks two child processes via `os.fork()`; each child writes 50 records via `write_call_record` then calls `os._exit(0)`; parent waits with `os.waitpid` for both; asserts the destination file contains exactly 100 lines and every line round-trips through `json.loads` with `schema_version == 1` (no partial or interleaved bytes).

Run via `python3 -m unittest discover -s tests` from the repo root. All four pass when the implementation lands.

## Builder prompt

You are implementing Honeycomb v1.1 spec 004 — the MCP tool-call observability log writer.

Create exactly two files: `lib/honeycomb/log.py` and `tests/test_log.py`. Do not edit any other file. Do not create a new `lib/honeycomb/__init__.py` if one is not already present — rely on PEP 420 namespace package semantics so `from lib.honeycomb import log` resolves.

### `lib/honeycomb/log.py`

The module docstring must document:
- The v1 schema and that bumping the `schema_version` is a breaking change.
- Every env var read: `BEES_REPO_ROOT`, `BEES_FEATURE_SLUG`, `BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL`, `HONEYCOMB_ROOT`.
- The concurrency model (`fcntl.flock(LOCK_EX)` + synchronous `f.flush()`).

Reference implementation — use this as your starting point and adapt only if you find a clear improvement (stdlib only, keep the module under ~120 lines):

```python
"""MCP tool-call observability log writer.

Writes one JSON Lines record per MCP tool invocation to
`$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl`, falling back to
`$HONEYCOMB_ROOT/.calls.jsonl` when the bees-side env vars are unset.

Record schema (schema_version: 1; bumping is breaking):
    schema_version (int): always 1 for this module version.
    ts (str): ISO-8601 UTC timestamp, millisecond precision.
    tool (str): MCP tool name.
    slug (str): BEES_FEATURE_SLUG or "unknown".
    actor (str): BEES_ACTOR or "unknown".
    stage (str): BEES_STAGE or "unknown".
    model (str): BEES_MODEL or "unknown".
    request (dict): tool input arguments.
    response (dict): tool response payload.
    duration_ms (float): wall-clock duration of the call.

Environment:
    BEES_REPO_ROOT      Primary destination requires this + BEES_FEATURE_SLUG.
    BEES_FEATURE_SLUG   Feature slug used in the destination path.
    BEES_ACTOR          Actor identity; defaults to "unknown".
    BEES_STAGE          Workflow stage; defaults to "unknown".
    BEES_MODEL          Model id; defaults to "unknown".
    HONEYCOMB_ROOT      Used only by the dev fallback path.

Concurrency:
    Appends are wrapped in fcntl.flock(LOCK_EX) and flushed synchronously
    so multi-process writes do not interleave even when a record exceeds
    PIPE_BUF.
"""

from __future__ import annotations

import datetime as _dt
import fcntl
import json
import os
import pathlib

UNKNOWN = "unknown"
SCHEMA_VERSION = 1


def resolve_destination() -> pathlib.Path:
    repo_root = os.environ.get("BEES_REPO_ROOT")
    slug = os.environ.get("BEES_FEATURE_SLUG")
    if repo_root and slug:
        dest = pathlib.Path(repo_root) / ".bees" / slug / "mcp-calls.jsonl"
    else:
        hc_root = os.environ.get("HONEYCOMB_ROOT", ".")
        dest = pathlib.Path(hc_root) / ".calls.jsonl"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def _utc_now_iso() -> str:
    now = _dt.datetime.now(_dt.timezone.utc)
    return f"{now:%Y-%m-%dT%H:%M:%S}.{now.microsecond // 1000:03d}Z"


def write_call_record(
    tool: str,
    request: dict,
    response: dict,
    duration_ms: float,
) -> None:
    record = {
        "schema_version": SCHEMA_VERSION,
        "ts": _utc_now_iso(),
        "tool": tool,
        "slug": os.environ.get("BEES_FEATURE_SLUG", UNKNOWN),
        "actor": os.environ.get("BEES_ACTOR", UNKNOWN),
        "stage": os.environ.get("BEES_STAGE", UNKNOWN),
        "model": os.environ.get("BEES_MODEL", UNKNOWN),
        "request": request,
        "response": response,
        "duration_ms": duration_ms,
    }
    line = json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n"
    dest = resolve_destination()
    with open(dest, "a", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(line)
            f.flush()
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

### `tests/test_log.py`

Use stdlib `unittest`. At the top of the file:

```python
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.honeycomb import log
```

Implement `TestWriteCallRecord(unittest.TestCase)` with the four methods named in the **Failing test** section.

Implementation hints:
- Use `tempfile.TemporaryDirectory()` per test for destination isolation.
- Use `unittest.mock.patch.dict(os.environ, {...}, clear=False)` to inject env vars; explicitly `del os.environ["KEY"]` (inside a patch context) when a test needs to verify a default `"unknown"`.
- For the concurrency test, use `os.fork()` (POSIX-only is fine — honeycomb targets macOS/Linux). Each child must call `os._exit(0)` after writing its 50 records (do NOT call `sys.exit`, which would run the parent's teardown). The parent calls `os.waitpid(pid, 0)` for each child before reading the file.
- For the millisecond precision assertion, accept any well-formed ISO-8601 string ending in `Z`; do not pin to a specific moment.

### Convention

This module is one of the first Python modules added under `lib/honeycomb/`. Establish (or follow) the convention:
- Tests live under `tests/`.
- Runner: `python3 -m unittest discover -s tests` from the repo root.
- Tests inject the repo root into `sys.path` at the top of the file so source under `lib/` resolves without an installed package.
- One test file per public module.

### Verification before declaring complete

1. From the repo root, run `python3 -m unittest discover -s tests`. All four `TestWriteCallRecord` tests pass; the command exits 0.
2. Spot-check one record: write a single record manually under a temp directory and confirm `json.loads(line)` produces a dict containing every one of the ten schema keys and `schema_version == 1`.
3. Confirm the module is under ~120 lines and depends only on the Python standard library.

## Success check

`python3 -m unittest discover -s tests` exits 0. `tests/test_log.py` contains exactly the four `TestWriteCallRecord` methods named in the **Failing test** section. `lib/honeycomb/log.py` exposes `write_call_record` and `resolve_destination` with the documented signatures. Every JSONL record contains the ten required schema fields, with `schema_version: 1` and an ISO-8601 UTC `ts`.

## Commit message

```
feat(honeycomb): MCP tool-call JSONL log writer (#004)

Adds lib/honeycomb/log.py with `write_call_record` and
`resolve_destination`. Each MCP tool invocation appends one JSONL
record to $BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl (or
$HONEYCOMB_ROOT/.calls.jsonl when slug/root are absent), with actor
identity propagated from BEES_ACTOR/STAGE/MODEL env vars (missing
values → "unknown") and appends wrapped in fcntl.flock for
multi-process safety.

Refs: .bees/honeycomb-v1-1/specs/004-mcp-log-writer-module.md
```
