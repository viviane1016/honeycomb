## Single API surface

All honeycomb access — by queens, scribes, builders, and the bees host process — goes through `lib/honeycomb/recall.py` or its MCP exposure (`bin/honeycomb-mcp`). No code reads `closet.md` or drawer files directly from disk at runtime.

**Rule:** if you find yourself calling `Path(something).read_text()` on a honeycomb path, replace it with `palace_recall(...)`.

`_compose_appended_prompt` (the bees host-process function that builds pre-prompt injections) was historically the main violator. Under v1.1 it issues `palace_recall` calls with targeted room names and concatenates the returned closet text. Queenfile-aware content and consumer overlays are automatically included as a side effect; no separate code path needed.

**Petition tools are additive.** `palace_petition_submit`, `palace_petition_list`, and `palace_petition_withdraw` extend the API surface; they do not bypass the recall path. Submitted overrides are immediately visible to subsequent `palace_recall` calls via the consumer overlay (see `palace-recall/overlay-semantics`).

**Why single-surface matters.** Recall-layer enhancements — scoring metadata, content hashes, scope-aware indexes, per-scope ChromaDB collections — apply automatically everywhere. A second direct-disk path would have to reimplement every enhancement separately, or it silently lags.

See ADR-0001 §Decision, point 1.
