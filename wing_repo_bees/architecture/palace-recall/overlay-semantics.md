## Overlay semantics and scope-aware behaviour

### include_pending

`palace_recall` accepts `include_pending=True` (default). When set, results from the consumer overlay are merged alongside canon results. Overlay results carry `source: "consumer-overlay"` in the response. Callers that want only canonical content pass `include_pending=False`.

### Consumer overlay precedence

When `$BEES_REPO_ROOT/.bees/honeycomb-overlay/` exists, drawer files placed there win over canon for matching drawer paths. Overlay drawers may be named with the `queenfile_<scope>` suffix (the standard override filename pattern) or as plain canonical names placed under the overlay tree — both forms are resolved at query time.

When the overlay is absent, `palace_recall` returns canon only — v1.0 behaviour, preserved exactly.

### Scope-aware behaviour

`palace_recall` accepts explicit scope params: `tool`, `tool_version`, `consumer`. When provided, recall selects the matching scoped index (built at install time by `tools/install.sh --tool <T> --tool-version <V> --consumer <C>`). When omitted, values are derived from env (`BEES_TOOL_VERSION`, `BEES_REPO_ROOT`), then fall back to canon.

**v1.1 scope note.** In honeycomb v1.1, one ChromaDB collection covers the install-time flattened view for the supplied scope. Per-scope collections (one collection per `tool × version × consumer` tuple) are planned for a later release; the v1.1 flattened-view approach is a stepping stone, not the final shape.

Result objects include a `source` field naming the collection that served the result (e.g. `"canon"`, `"scope_bees-v1.18_scarab"`, `"consumer-overlay"`).

See ADR-0001 §MCP tool surface and ADR-0002 §5 (recall API).
