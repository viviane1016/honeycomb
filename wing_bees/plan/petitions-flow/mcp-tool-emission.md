## MCP tool emission

Three petition MCP tools are exposed by `bin/honeycomb-mcp`:

### `palace_petition_submit(target, content, rationale, context)`

Resolves the canonical drawer path from `target`, derives the override filename `<drawer>.queenfile_<scope>.md` from `context`, commits the file to a fresh feature branch in `$HONEYCOMB_ROOT` (`feat/petition-<slug>`), runs `gh pr create`, and returns `{branch, pr_url, overlay_path}`.

When `$BEES_REPO_ROOT` is set, also writes the override file to `$BEES_REPO_ROOT/.bees/honeycomb-overlay/` for immediate self-recall during the open-PR window.

### `palace_petition_list(consumer)`

Walks `$HONEYCOMB_ROOT/wing_*/**/queenfile_*.md` filtered by `consumer` (pass `null` to match all scopes), and merges files from the consumer overlay at `$BEES_REPO_ROOT/.bees/honeycomb-overlay/`. Returns a list of `{target, consumer, tool, tool_version, path, source, rationale}`.

### `palace_petition_withdraw(path)`

Removes the override file (identified by its relative path within canon) from its feature branch and closes the associated PR via `gh pr close`. Overlay copy is removed locally when `$BEES_REPO_ROOT` is set.

### Dependencies and errors

Requires `gh` CLI, installed and authenticated. Missing `gh` raises `PetitionError("gh CLI not found")`. Both MCP petition calls and `palace_recall` are logged to `$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl` (see ADR-0004).
