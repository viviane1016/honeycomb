## Briefing structure

A briefing has seven required sections. Write them in order; the queen reads them to understand scope, motivation, and success criteria.

### Required sections

1. **`## Goal`** — one-sentence statement of what you're building. Outcome-oriented ("Add OAuth login"), not process-oriented ("Implement OAuth library integration"). ≤ 72 chars.

2. **`## Motivation`** — why this work matters. Who needs it? What problem does it solve? 2–4 sentences.

3. **`## Expected outcome`** — how will the system behave differently after this work lands? What should be testable? 2–3 sentences.

4. **`## In scope`** — what will the work touch? Be specific: "authentication service", "login UI", "session middleware", "OAuth provider integration". One item per line.

5. **`## Out of scope`** — what *won't* this work do, even if it seems related? Prevents scope creep. Examples: "Refreshing OAuth tokens" (if you're only doing initial login), "Migrating existing sessions to OAuth" (if you're adding OAuth as an option, not replacing).

6. **`## Issue references`** — links to related GitHub issues. Use:
   - `Closes #N` — this work closes the issue (auto-close on merge)
   - `Fixes #N` — synonym for `Closes`
   - `Resolves #N` — synonym for `Closes`
   - `Refs #N` — this work references the issue but doesn't close it
   One per line.

7. **`## Operator amendments`** — timestamped notes about plan/spec/implementation intent changes the operator decides on *after* plan approval. Initially empty; the operator appends entries as work progresses. Each entry uses a `### YYYY-MM-DD — <one-line summary>` heading followed by a short paragraph describing what changed and why. The queen-accept stage (see `wing_bees/stage-accept`) reads this section as the reference for current operator intent — if the plan or specs diverge from the briefing without a corresponding amendment entry, the queen surfaces a concern. Leave this section empty when first writing the briefing.
