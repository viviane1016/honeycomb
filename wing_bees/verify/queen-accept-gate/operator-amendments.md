## Operator amendments

The queen reads the annotated `briefing.md` — the original briefing sections plus any `## Operator amendments` entries — as the primary reference for operator intent. The plan is the colony's interpretation of the briefing, not the authoritative source of truth. If the plan or any spec diverged from the briefing in ways that are not covered by an amendment note, the queen surfaces that divergence as a concern.

The `## Operator amendments` section is the mechanism for mid-flight intent changes. When the operator's intent shifted after plan approval — for example, a spec was changed in scope, or a design decision was reversed — the operator appends an amendment note explaining the change. The queen reads these notes and treats the amended briefing as reflecting current intent.

`bees mark-patched` (the operator implements a spec manually instead of via a builder bee) does not require an amendment note when the spec was followed faithfully. An amendment is only needed when operator intent diverged from what the colony produced. See `briefing-template.md` for the convention operators use to write these notes.
