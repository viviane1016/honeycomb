<!-- role-scribe.md: migrated from role-scribe.md.

Hall: hall_architecture
models: [claude-opus-4-7]
-->

One scribe instance runs per work-breakdown item; model is resolved per-unit (Opus default, overridable via `[scribe:<m>]` tag or `--scribe-model`). She reads the plan plus a single-unit instruction, calls `palace_recall` if needed, and emits exactly one `<<<SPEC NNN-…>>>` block with seven required sections. Parse failures retry once; cross-spec consistency is enforced by the queen's review pass. She also runs in Verify mode, evaluating builder diffs to emit APPROVE or REJECT verdicts.
