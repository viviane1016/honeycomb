## MCP server

`palace_recall` and `palace_recall_semantic` are exposed to the queen and scribe as MCP tools backed by `bin/bees_honeycomb_mcp`, a pure-Python JSON-RPC 2.0 stdio server.

**Lifecycle:** the server is launched per-stage via a per-stage config file written by the bees harness (`lib/honeycomb._build_honeycomb_mcp_config`):

- Scribes: `.bees/<slug>/.mcp.NNN.json` (one config per scribe subprocess)
- Queen review pass: `.bees/<slug>/.mcp.review.json`

**Environment:** the server reads two env vars set by the bees harness:

- `BEES_REPO_ROOT` — absolute path to the repo root; used to locate `honeycomb/`
- `BEES_FEATURE_SLUG` — the current feature slug; used to locate the trace file at `.bees/<slug>/honeycomb-trace.md`

**Exposure:** the server exposes two tools: `palace_recall` (keyword, always available) delegates to `lib/bees/bees_honeycomb.palace_recall`; `palace_recall_semantic` (vector, best-effort) delegates to `lib/bees/hc_index.palace_recall_semantic`. Neither writes to the honeycomb directory — honeycomb is read-only at runtime. The chroma index lives outside the repo at `~/.mempalace/honeycomb/`.
