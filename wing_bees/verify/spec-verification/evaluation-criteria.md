## Evaluation criteria

The verifier checks the diff against the spec along four axes:

- **Scope-file containment** — no diff hunks touch files outside those declared in the spec's `## Scope`. Out-of-scope edits indicate the builder strayed from the agreed contract.
- **Required-symbols presence** — symbols, identifiers, section names, or outputs that the spec's `## Scope` explicitly lists appear in the diff.
- **Failing-test scenario addressed** — the failing test or scenario described in the spec's `## Failing test` is now satisfied by the diff.
- **Commit-message references spec path** — the commit footer contains the spec file path (e.g., `Refs: .bees/<slug>/specs/NNN-<task>.md`), preserving traceability to the spec.
