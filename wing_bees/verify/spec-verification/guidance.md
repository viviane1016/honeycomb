## Guidance

**Evaluates, not re-implements.** The verifier reads the diff against the spec the scribe authored. She does not re-derive what the diff *should* have been; she checks whether the diff honors what the spec asked for. If either side is ambiguous — the spec underspecifies, the diff is unreadable, the connection between them is unclear — that is itself grounds for REJECT, because the next step (ff-merge into the feature branch) is irreversible without rewriting history.

**Failure modes.** Common REJECT scenarios:
- Empty diff — the builder committed but produced no content changes.
- Out-of-scope files — diff touches paths not declared in `## Scope`.
- Missing required symbols — `## Scope` enumerated outputs that are absent from the diff.
- Commit message missing spec path — traceability to the spec is lost or unclear.
