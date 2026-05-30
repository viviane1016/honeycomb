<!-- palace-recall.md

Hall: hall_architecture
-->

`palace_recall(query, wings, top_k, drawer, include_pending, tool, tool_version, consumer)` is the single recall entry point for all honeycomb content. Consumer overlay files take precedence over canon for matching drawer paths. Scope params select the matching scoped index; absent params derive from env or fall back to canon. Every call appends a JSONL log record synchronously.
