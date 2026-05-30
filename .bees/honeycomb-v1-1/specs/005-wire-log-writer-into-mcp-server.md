---
depends-on: [004]
output-files: [bin/honeycomb-mcp, tests/test_mcp_log_integration.py]
scribe-model: claude-opus-4-7
---

# Spec 005 — Wire log writer into MCP server

## Builder model

claude-sonnet-4-6

## Goal

Route every `palace_recall` and `palace_recall_semantic` dispatch through `lib/honeycomb/log.write_call_record(...)` so each MCP tool call produces one JSONL observability record, with no change to the existing JSON-RPC response shape.

## Scope

**Edit `bin/honeycomb-mcp`:**

1. Import `log` from `honeycomb` after `sys.path` is set (lazy, same pattern as `_load_palace_recall`). A small helper `_load_log_writer()` returning the `write_call_record` callable, or `None` if the import fails (so the server still works without v1.1 log support during partial rollouts).
2. In `_handle_tools_call`, when `name` is `palace_recall` or `palace_recall_semantic`:
   - Capture `start = time.monotonic()` before dispatching to the underlying callable.
   - After the response payload is built (success path), compute:
     - `duration_ms = int((time.monotonic() - start) * 1000)`
     - `rendered = json.dumps(result, indent=2)` — same string used to build the MCP response payload (do NOT call `json.dumps` twice; reuse the value).
     - `bytes_len = len(rendered.encode("utf-8"))`
     - `content_sha = hashlib.sha256(rendered.encode("utf-8")).hexdigest()`
   - Call `write_call_record(tool=name, request=arguments, response={"bytes": bytes_len, "content_sha": content_sha, "result_count": <len(result) if list else 1>}, duration_ms=duration_ms)`. Do NOT include the full rendered content in the record `response` field — only the metadata above.
   - On the error path (palace_recall raised, or semantic fallback returned `[]` after exception), still emit a record. Use `response={"error": "<short msg>", "bytes": 0, "content_sha": null, "result_count": 0}` and `duration_ms` measured to the failure point.
3. Wrap the log call itself in `try/except Exception: pass` so a logging failure never breaks the MCP response.
4. Update the module docstring to enumerate the new env vars consumed by the writer (`BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL`) alongside the existing `BEES_FEATURE_SLUG` and `BEES_REPO_ROOT`, and note that every tool call appends one JSONL record to `$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl` (with the dev-fallback path).
5. Update `TOOL_DESCRIPTOR["description"]` and `SEMANTIC_TOOL_DESCRIPTOR["description"]` to append one sentence noting the log side-effect: e.g. `"Each call appends one JSONL record to $BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl (honeycomb v1.1 observability)."`

**Add `tests/test_mcp_log_integration.py`** (stdlib `unittest`):
- A test that spawns the MCP server as a subprocess (`subprocess.Popen` on `bin/honeycomb-mcp`), feeds an `initialize` then a `tools/call` request for `palace_recall` over stdin, reads two JSON-RPC responses from stdout, and asserts that exactly one new line was appended to the configured log file with the expected schema fields (`schema_version`, `ts`, `tool == "palace_recall"`, `actor`, `stage`, `model`, `slug`, `request.query`, `response.bytes > 0`, `response.content_sha` matches `^[0-9a-f]{64}$`, `duration_ms >= 0`).
- A second test repeats for `palace_recall_semantic`. If the semantic backend returns an empty fallback (chromadb missing), the response record may have `result_count: 0` but the log record still appears.
- A third test asserts that a logging failure (e.g. unwritable destination) does NOT prevent the MCP JSON-RPC response from being returned — point the env at an unwritable path and check the `tools/call` still returns success.
- Set env: `HONEYCOMB_ROOT`, `BEES_REPO_ROOT=<tmpdir>`, `BEES_FEATURE_SLUG=test-slug`, `BEES_ACTOR=test-actor`, `BEES_STAGE=spec`, `BEES_MODEL=claude-sonnet-4-6`. Use a tmp `HONEYCOMB_ROOT` containing a minimal `wing_bees/` tree with one closet so `palace_recall` returns at least one match.

**Non-goals**:
- The petition tools (`palace_petition_*`) are wired in spec 007; do not register them here.
- The overlay-aware recall path is added in spec 008; this spec must not pass `overlay_root` to the underlying callables.
- Log-record redaction is BACKLOG; record content as-is.
- Do not add `BEES_*` env reads to this file beyond updating the docstring — the writer module (`lib/honeycomb/log.py`, spec 004) handles env resolution.

## Failing test

`tests/test_mcp_log_integration.py::TestMCPLogIntegration::test_palace_recall_writes_log_record` — spawns the MCP server, issues a `tools/call` for `palace_recall`, asserts a new JSONL line appears in `$BEES_REPO_ROOT/.bees/test-slug/mcp-calls.jsonl` with the expected schema. Fails before the builder edits `bin/honeycomb-mcp` because no log record is written; passes once the writer is wired in.

## Builder prompt

You are wiring honeycomb v1.1's observability log writer into the existing MCP stdio server.

Spec 004 has delivered `lib/honeycomb/log.py` exposing `write_call_record(tool, request, response, duration_ms) -> None`. The writer reads `BEES_REPO_ROOT`, `BEES_FEATURE_SLUG`, `BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL` from the environment, writes one JSONL line per call to `$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl`, and uses `fcntl.flock` for concurrent-write safety. Treat it as a stable import.

Your job is to wrap every `palace_recall` and `palace_recall_semantic` dispatch in `bin/honeycomb-mcp` with the writer. Specifics:

1. In `bin/honeycomb-mcp`, add a helper `_load_log_writer()` that returns `write_call_record` from `honeycomb.log` (same lazy-import pattern as `_load_palace_recall`). Return `None` if the import raises — never let a logging-side import problem break the MCP server.

2. In `_handle_tools_call`, for both `palace_recall` and `palace_recall_semantic` branches:
   - Capture `start = time.monotonic()` BEFORE the underlying call.
   - Build the rendered response string once: `rendered = json.dumps(result, indent=2)`. Use this same value to build the MCP `payload` (do not re-serialise).
   - Compute `bytes_len = len(rendered.encode("utf-8"))` and `content_sha = hashlib.sha256(rendered.encode("utf-8")).hexdigest()`.
   - Compute `result_count` — for a list result, `len(result)`; otherwise `1`.
   - Compute `duration_ms = int((time.monotonic() - start) * 1000)`.
   - Call the writer (guarded by `try/except Exception: pass`):
     ```python
     writer = _load_log_writer()
     if writer is not None:
         try:
             writer(
                 tool=name,
                 request=arguments,
                 response={"bytes": bytes_len, "content_sha": content_sha, "result_count": result_count},
                 duration_ms=duration_ms,
             )
         except Exception:
             pass
     ```
   - On the error path (underlying call raises, or semantic fallback hits its `except`), still emit a record with `response={"error": "<short msg>", "bytes": 0, "content_sha": None, "result_count": 0}` and `duration_ms` measured to the failure point. The MCP error/empty response shape stays exactly as it is today.

3. Update the module docstring at the top of `bin/honeycomb-mcp` to list the new env vars (`BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL`) and note that each call appends one JSONL record to `$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl` (with the dev-fallback path `$HONEYCOMB_ROOT/.calls.jsonl`).

4. Append one sentence to each tool descriptor's `description` field noting the log side-effect (see Scope).

5. Add `tests/test_mcp_log_integration.py` using stdlib `unittest`. Subprocess the MCP server (`subprocess.Popen([sys.executable, "bin/honeycomb-mcp"], stdin=PIPE, stdout=PIPE, env=...)`), feed JSON-RPC messages via stdin, read responses from stdout. Required tests:
   - `test_palace_recall_writes_log_record` — issue a `tools/call` for `palace_recall` with `{"query": "queen"}` (or any term that hits the seed wing tree). After the response arrives, read the JSONL log file and assert exactly one new line with: `schema_version == 1`, `tool == "palace_recall"`, `slug == "test-slug"`, `actor == "test-actor"`, `stage == "spec"`, `model == "claude-sonnet-4-6"`, `request.query == "queen"`, `response.bytes > 0`, `response.content_sha` is a 64-char hex string, `duration_ms` is an int `>= 0`.
   - `test_palace_recall_semantic_writes_log_record` — same shape, tool name `palace_recall_semantic`. The semantic backend may fall through to `[]`; the record must still appear with `tool == "palace_recall_semantic"` and `result_count == 0` if no matches.
   - `test_logging_failure_does_not_break_response` — point `BEES_REPO_ROOT` at a path under a read-only directory (use `os.chmod` on a tmpdir; remember to restore perms in `tearDown`). Issue a `tools/call`; assert the JSON-RPC response is still a normal success (not an error envelope).

   For the seed wing tree, build a tmpdir with `wing_bees/architecture/sample/closet.md` containing the word "queen" so keyword recall returns at least one hit. Set `HONEYCOMB_ROOT` to the tmpdir.

6. Use the project's existing test convention: stdlib `unittest`, invoked via `python3 -m unittest discover -s tests`.

Repo layout to expect (repo-relative):
- `bin/honeycomb-mcp` — the file you edit
- `lib/honeycomb/log.py` — exists from spec 004
- `lib/honeycomb/recall.py`, `lib/honeycomb/semantic.py` — unchanged here
- `tests/test_mcp_log_integration.py` — the file you create

Constraints:
- Do NOT modify `lib/honeycomb/log.py` or `lib/honeycomb/recall.py` or `lib/honeycomb/semantic.py`.
- Do NOT pass an `overlay_root` to the underlying callables (spec 008's job).
- Do NOT add petition tool descriptors (spec 007's job).
- The MCP JSON-RPC response shape MUST be byte-identical to the v1.0 server for the same input when logging is disabled or fails — backwards compat is non-negotiable.
- Keep the helper imports lazy so existing dev environments without `lib/honeycomb/log.py` (briefly during cherry-pick) still produce working `tools/list` and `tools/call` responses.

Success check: `python3 -m unittest discover -s tests -p "test_mcp_log_integration.py" -v` exits 0 with all three tests passing.

## Success check

- `python3 -m unittest discover -s tests -p "test_mcp_log_integration.py" -v` exits 0.
- `python3 -m unittest discover -s tests` continues to exit 0 (no regression in spec 001–004 tests).
- Diff review confirms: no behavioural change to JSON-RPC response shapes; log writer is invoked once per tool call; logging failures are swallowed; module docstring + tool descriptors mention the log side-effect; env vars `BEES_ACTOR`/`STAGE`/`MODEL` enumerated in docstring.

## Commit message

feat(mcp): wire observability log writer into palace_recall dispatch (#005)

Every palace_recall and palace_recall_semantic invocation now produces
one JSONL record via lib/honeycomb/log.write_call_record, capturing
actor identity, request, response metadata (bytes/content_sha/
result_count), and duration. The MCP JSON-RPC response shape is
unchanged; logging failures are swallowed so observability never
breaks the recall path.

Refs: .bees/honeycomb-v1-1/specs/005-wire-log-writer-into-mcp-server.md
