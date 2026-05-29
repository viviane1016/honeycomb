## Scribe-only mode

Work units tagged `[scribe-only:<model>]` run in a dedicated cell within the spec stage. The scribe receives a similar one-spec-per-unit instruction as in normal spec mode, but instead of emitting a spec block, she receives the spec body pre-written and applies file changes directly: Edit and Write for content, narrowed git for commits (status, add, commit), pytest for verification. **No queen review.** The scribe is treated as editorial authority — she drafts, applies, and commits in one pass. This model trades queen oversight for fast turnaround on purely editorial work (docs-updates, release-ceremony housekeeping).

**Tool allowlist:** Edit, Write, Bash(git:status, git:add, git:commit, git:reset), Bash(python3 -m pytest). No file deletion, no destructive operations. Read-only on the feature branch state; each cell is transient and discarded post-merge.

**Limitation:** Scribe-only specs cannot reference code added later by builder specs in the same plan. Any cross-unit dependency must be encoded in the plan's dependency graph (e.g., a scribe-only docs spec depending on a builder spec that implements the documented feature).

**Secret-scan mitigations:** Scribe-only specs are secret-scanned at the draft boundary (before execution) and the commit boundary (after FF-merge), matching builder-stage protections.
