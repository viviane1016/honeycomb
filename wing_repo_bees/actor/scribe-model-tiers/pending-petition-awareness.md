## Pending-petition awareness

During spec writing, scribes issue `palace_recall` with `include_pending=True` (the v1.1 default). Results may include drawers with `source: "consumer-overlay"` — these are pending petitions that have not yet been adopted into canon.

**Handling rules:**

1. **Canon over overlay.** When both a canon result and an overlay result exist for the same drawer path, prefer the canon result. The overlay represents a proposal, not an authority.
2. **Overlay-only results.** When only overlay content exists for a queried target, treat it as provisional guidance and follow it. Note the pending status in the spec body if the content materially shapes the design.
3. **No verbatim transcription.** Do not copy overlay content into the spec body as if it were adopted canon. Reference the target path and note that the content is pending adoption.
4. **Gap → petition.** A scribe that encounters a genuine gap (neither canon nor overlay covers the queried target) may emit one `palace_petition_submit` call with proposed content, rationale, and target. Limit: at most 1 petition per spec. Scribes have a narrower mandate than the queen; do not emit speculative petitions based on hypothetical future needs.

**Source markers.** The `source` field in each recall result is `"canon"`, `"consumer-overlay"`, or `"honey-<name>@<ver>"`. Scribes can inspect this field when deciding how to weight a result. In practice, Opus-tier scribes can infer provisional status from context without mechanically checking the field.
