---
depends-on: [005, 006]
output-files: [bin/honeycomb-mcp, tests/test_mcp_petitions.py]
scribe-model: claude-opus-4-7
---

# Spec 007 — Register petition MCP tools

## Builder model

claude-sonnet-4-6

## Goal

Expose the petition helpers from `lib/honeycomb/petitions.py` as three MCP tools (`palace_petition_submit`, `palace_petition_list`, `palace_petition_withdraw`) on the `honeycomb-mcp` JSON-RPC server, wrapping each call through the log writer from spec 004/005 so every petition invocation appends a record to `mcp-calls.jsonl`.

## Scope

**Files edited:**
- `bin/honeycomb-mcp` — add three tool descriptors, dispatch routing, log-writer wrapping for petition calls.

**Files added:**
- `tests/test_mcp_petitions.py` — unit tests asserting the dispatch shape and log-writer integration.

**Symbols added in `bin/honeycomb-mcp`:**
- `PETITION_SUBMIT_DESCRIPTOR`, `PETITION_LIST_DESCRIPTOR`, `PETITION_WITHDRAW_DESCRIPTOR` — tool descriptors with input schemas matching the helper kwargs (excluding `hc_root`/`overlay_root`, which the server injects).
- `_load_petitions()` — lazy importer mirroring `_load_palace_recall()`.
- `_overlay_root_for_petitions()` — returns `Path(BEES_REPO_ROOT) / ".bees" / "honeycomb-overlay"` when `BEES_REPO_ROOT` is set, else `None`.
- Extend `_handle_tools_call` to route `palace_petition_submit|list|withdraw` to the helper, catch `PetitionError` → `_err(req_id, -32603, ...)`, and pass through the log writer (same schema as spec 005, with `tool` field = the petition tool name).

**Schemas (each descriptor's `inputSchema`):**
- `palace_petition_submit`: required `target` (string), `content` (string), `rationale` (string), `context` (object with `tool`/`tool_version`/`consumer` string keys; all required).
- `palace_petition_list`: optional `consumer` (string; default null = all).
- `palace_petition_withdraw`: required `petition_id` (string).

**`tools/list` response** updated to return all five descriptors (existing two + three new).

**Non-goals:**
- No changes to `lib/honeycomb/petitions.py` (built in spec 006).
- No changes to the log-writer module (built in spec 004/005).
- No new env vars beyond those already documented.
- No transport changes; still stdio JSON-RPC 2.0.

## Failing test

`tests/test_mcp_petitions.py::test_tools_list_includes_petition_descriptors` — drives the binary as a subprocess with a `tools/list` request and asserts that the response contains exactly five tool names: `palace_recall`, `palace_recall_semantic`, `palace_petition_submit`, `palace_petition_list`, `palace_petition_withdraw`. Fails today because only the first two are registered.

Additional tests in the same file (also fail until built):
- `test_petition_submit_dispatches_to_helper` — monkeypatches `lib.honeycomb.petitions.submit` via a fake module on `sys.path` and asserts the returned JSON contains the expected `petition_id`/`branch`/`pr_url` fields.
- `test_petition_submit_logs_call` — asserts that after a successful `tools/call` for `palace_petition_submit`, the JSONL log file (under a tmp `BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl`) has one record with `tool == "palace_petition_submit"` and the actor env propagated.
- `test_petition_error_returns_jsonrpc_error` — fake helper raises `PetitionError("gh CLI not found")`; assert the response is a JSON-RPC error with code -32603 and the message includes the helper's text.
- `test_petition_list_no_consumer_passes_none` — asserts that when the request omits `consumer`, the helper is invoked with `consumer=None`.

## Builder prompt

You are editing `bin/honeycomb-mcp` and creating `tests/test_mcp_petitions.py` to register the three petition MCP tools defined by `lib/honeycomb/petitions.py` (built in spec 006).

**Context — current shape of `bin/honeycomb-mcp`:**
- It is a JSON-RPC 2.0 stdio server speaking the minimal MCP handshake (`initialize`, `tools/list`, `tools/call`).
- Two tool descriptors exist: `TOOL_DESCRIPTOR` (`palace_recall`) and `SEMANTIC_TOOL_DESCRIPTOR` (`palace_recall_semantic`).
- `_handle_tools_list` returns `{"tools": [TOOL_DESCRIPTOR, SEMANTIC_TOOL_DESCRIPTOR]}`.
- `_handle_tools_call` dispatches by `name`; unknown names → `_err(req_id, -32601, ...)`.
- Per spec 005, both existing tool calls now flow through `log.write_call_record(...)` from `lib/honeycomb/log.py`.
- `HONEYCOMB_ROOT`, `BEES_REPO_ROOT`, `BEES_FEATURE_SLUG`, `BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL` are the relevant env vars.

**What to add:**

1. Three module-level descriptors in `bin/honeycomb-mcp`:
   - `PETITION_SUBMIT_DESCRIPTOR` — `name: "palace_petition_submit"`, description explains: writes an override file (`<drawer>.queenfile_<scope>.md`) to a fresh feature branch in `$HONEYCOMB_ROOT`, opens a PR via `gh`, optionally writes a copy to the consumer overlay at `$BEES_REPO_ROOT/.bees/honeycomb-overlay/`, returns `{petition_id, branch, pr_url, overlay_path}`. `inputSchema` requires `target` (string), `content` (string), `rationale` (string), `context` (object with required `tool`, `tool_version`, `consumer` string properties).
   - `PETITION_LIST_DESCRIPTOR` — `name: "palace_petition_list"`, description explains: lists pending override files across canon (`$HONEYCOMB_ROOT`) and overlay, filtered by `consumer` (omit = all consumers). `inputSchema` properties: optional `consumer` (string); no required fields.
   - `PETITION_WITHDRAW_DESCRIPTOR` — `name: "palace_petition_withdraw"`, description explains: removes the override file from its feature branch and closes the PR. `inputSchema` requires `petition_id` (string).

2. Update `_handle_tools_list` to return all five descriptors in this order: recall, semantic, submit, list, withdraw.

3. Add `_load_petitions()` mirroring `_load_palace_recall()`:
   ```python
   def _load_petitions():
       sys.path.insert(0, str(_repo_root() / "lib"))
       from honeycomb import petitions  # type: ignore  # noqa: WPS433
       return petitions
   ```

4. Add `_overlay_root_for_petitions()`:
   ```python
   def _overlay_root_for_petitions() -> Path | None:
       raw = os.environ.get("BEES_REPO_ROOT")
       if not raw:
           return None
       return Path(raw) / ".bees" / "honeycomb-overlay"
   ```

5. Extend `_handle_tools_call`: add three new `if name == "palace_petition_..."` branches (placed after the existing two), each of which:
   - Loads the petitions module via `_load_petitions()`; on `ImportError`/`Exception` returns `_err(req_id, -32603, f"failed to load petitions: {e}")`.
   - Resolves `hc_root = _repo_root()` and `overlay_root = _overlay_root_for_petitions()`.
   - For `palace_petition_submit`: validates required args (`target`, `content`, `rationale`, `context`); calls `petitions.submit(target=..., content=..., rationale=..., context=..., hc_root=hc_root, overlay_root=overlay_root)`.
   - For `palace_petition_list`: calls `petitions.list_pending(consumer=arguments.get("consumer"), hc_root=hc_root, overlay_root=overlay_root)`.
   - For `palace_petition_withdraw`: validates `petition_id`; calls `petitions.withdraw(petition_id=..., hc_root=hc_root)`.
   - Wraps each in `try/except petitions.PetitionError as e: return _err(req_id, -32603, str(e))` and a broader `except Exception as e: return _err(req_id, -32603, f"<tool> raised: {e}")`.
   - Wraps each through the log writer (`log.write_call_record(tool=name, request=arguments, response=<result-or-error>, duration_ms=<measured>)`) so petition calls land in the same JSONL as recall calls. Measure `duration_ms` via `time.monotonic()` deltas around the helper call (mirror what spec 005 does for `palace_recall`).
   - Returns `_ok(req_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})` on success.

   IMPORTANT: the `query` argument is required for recall tools but NOT for petition tools. Move the existing `if "query" not in arguments:` guard to live inside the recall/semantic branches only, OR gate it on `name in ("palace_recall", "palace_recall_semantic")`. Petition calls must not be rejected for missing `query`.

6. Update the module docstring at the top of `bin/honeycomb-mcp` to mention the petition tools and the additional env vars (`BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL`) introduced by the log writer.

**Tests (`tests/test_mcp_petitions.py`):**

Use stdlib `unittest`. Drive `bin/honeycomb-mcp` as a subprocess via `subprocess.Popen` with `stdin=PIPE, stdout=PIPE`, writing JSON-RPC lines and reading the responses (mirror any patterns already established in `tests/test_mcp_log_integration.py` from spec 005 — if no such file exists yet, structure each test as: set up tmp dirs and env, spawn subprocess with that env, send `initialize` + `tools/list` or `tools/call`, parse responses).

To inject a fake `petitions` module, create a temp directory, write a `honeycomb/petitions.py` stub that records calls to a file (or sets module-level state) and exposes `submit`, `list_pending`, `withdraw`, plus a `class PetitionError(Exception)` matching the real module. Set `HONEYCOMB_ROOT` to a directory whose `lib/honeycomb/` contains the stub. Set `BEES_REPO_ROOT` to a tmp dir; set `BEES_FEATURE_SLUG=test-spec-007`; set `BEES_ACTOR=scribe`, `BEES_STAGE=spec`, `BEES_MODEL=claude-sonnet-4-6`.

The four required tests:
- `test_tools_list_includes_petition_descriptors`: send `tools/list`; assert `len(tools) == 5` and the names match the expected set.
- `test_petition_submit_dispatches_to_helper`: stub returns `{"petition_id": "p123", "branch": "feat/petition-p123", "pr_url": "https://github.com/x/y/pull/1", "overlay_path": None}`; assert response parses to that dict.
- `test_petition_submit_logs_call`: after a `palace_petition_submit` call, read `$BEES_REPO_ROOT/.bees/test-spec-007/mcp-calls.jsonl`, parse one line, assert `tool == "palace_petition_submit"`, `actor == "scribe"`, `stage == "spec"`, `model == "claude-sonnet-4-6"`.
- `test_petition_error_returns_jsonrpc_error`: stub raises `PetitionError("gh CLI not found")`; assert response has `error.code == -32603` and `"gh CLI not found"` appears in `error.message`.
- `test_petition_list_no_consumer_passes_none`: stub records its kwargs; assert `consumer is None` when the request omits the field.

**Test run command (success check):**
```
python3 -m unittest discover -s tests
```

Must pass with the new tests included and no regressions in existing tests (recall, semantic, log).

**Constraints:**
- Do not import `lib/honeycomb/petitions.py` at module load time in `bin/honeycomb-mcp` — keep the lazy-load pattern.
- Do not change the existing `palace_recall` or `palace_recall_semantic` descriptors or their dispatch.
- Do not add new env vars.
- Keep the JSON-RPC response shape consistent with the existing tools: `{"content": [{"type": "text", "text": "<json>"}]}` for success; `error` object for failure.
- Mtime-free: do not use timestamps that vary between runs in any assertion.

## Success check

- `python3 -m unittest discover -s tests` passes, including all five new tests in `tests/test_mcp_petitions.py` and all pre-existing tests.
- `bin/honeycomb-mcp`'s `tools/list` returns five descriptors.
- A `tools/call` for `palace_petition_submit` with valid args invokes `petitions.submit` and returns its dict as JSON.
- A `tools/call` for `palace_petition_submit` raising `PetitionError` returns a JSON-RPC error with code -32603.
- The `mcp-calls.jsonl` log under `$BEES_REPO_ROOT/.bees/<slug>/` gains one record per petition call with the correct `tool` field and propagated actor identity.
- Diff review: only `bin/honeycomb-mcp` and `tests/test_mcp_petitions.py` are touched.

## Commit message

feat(mcp): register petition tools on honeycomb-mcp (#007)

Add palace_petition_submit/list/withdraw to the MCP server's tool
catalogue, dispatching to lib/honeycomb/petitions.py helpers and
wrapping each call through the JSONL log writer for actor-attributed
observability. Update tools/list to return all five descriptors.

Refs: .bees/honeycomb-v1-1/specs/007-register-petition-mcp-tools.md
