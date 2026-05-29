<!-- palace-recall-api.md: migrated from arch-palace-recall.md.

Hall: hall_architecture
tools: [mcp]
languages: [python, markdown]
-->

`palace_recall(query, wings=None, halls=None, top_k=3, drawer=False)` keyword-scores honeycomb rooms and returns top-k as `[{wing, room, hall, path, closet}]`; add `drawer=True` for full body. Backed by `bin/bees_honeycomb_mcp` (JSON-RPC 2.0 stdio). Each call appends a timestamped block to `.bees/<slug>/honeycomb-trace.md`. Scribes inherit the queen's trace to avoid redundant recalls.
