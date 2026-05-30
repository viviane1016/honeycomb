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
