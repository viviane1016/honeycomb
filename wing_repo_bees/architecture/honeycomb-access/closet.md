<!-- honeycomb-access.md

Hall: hall_architecture
-->

All honeycomb reads go through `palace_recall` (or the MCP server that wraps it); no bees process reads closet files directly from disk. `BEES_ACTOR`, `BEES_STAGE`, and `BEES_MODEL` propagate actor identity into each MCP call. Every tool call appends a JSONL record to `.bees/<slug>/mcp-calls.jsonl` (dev fallback: `$HONEYCOMB_ROOT/.calls.jsonl`).
