## Colony-internal advisory gates

Bees has two colony-internal advisory gates run by other bees rather than the operator: scribe-verify (in stage-dispatch, between builder commit and FF-merge) and queen-accept (in stage-ship, before `gh pr create`).

These are not additional human gates. The two-gate model — plan approval and PR review — is preserved.

**scribe-verify:** The scribe (running in verify mode) evaluates the builder's diff against the spec and emits APPROVE or REJECT. REJECT preserves the cell for re-dispatch; APPROVE proceeds to FF-merge.

**queen-accept:** The queen evaluates the full feature diff against the annotated briefing, plan, and all spec texts, emitting APPROVE or CONCERNS. CONCERNS is written to `.bees/<slug>/accept.md` and surfaced on stderr; the operator decides whether to ship anyway. Queen-accept is advisory, not blocking.

Both stages run automatically and are advisory by default — neither adds a third human gate. The two human gates (plan approval, PR review) remain authoritative.
