## Semantic recall (`palace_recall_semantic`)

A second MCP tool, `palace_recall_semantic`, layers vector recall over the same honeycomb wing/room data. Backed by a chroma collection at `~/.mempalace/honeycomb/honeycomb_rooms` (built from honeycomb markdown by `tools/hc_index.py`), it surfaces conceptually-related rooms when keyword wording diverges.

**Signature:** `palace_recall_semantic(query, wings=None, halls=None, top_k=3)` — same `wings` and `halls` filter semantics as the keyword tool; no `drawer` flag (closets are returned, full bodies retrieved separately via direct file read of the canonical markdown).

**Return shape:** identical to keyword recall — `[{wing, room, hall, path, closet}]` — so callers can swap freely.

**Best-effort failure mode.** Semantic recall is additive, not load-bearing. When the index is missing, when the chroma collection can't be opened, or when chromadb isn't installed, the tool returns an empty list rather than a JSON-RPC error. Callers fall through to `palace_recall` (keyword) on empty without seeing a failure.

**When to prefer which.** Use `palace_recall` first for cheap deterministic matches when the query likely contains words present in the corpus. Use `palace_recall_semantic` when the query is paraphrased, when wording diverges from the corpus, or when keyword recall returns an empty list. Either tool can carry a `halls=[...]` filter to scope by intent (architecture, procedure, etc. — see `arch-halls`).

The markdown remains the system of record. The chroma collection is a regenerable derived cache — losing the directory costs a re-index, not data.
