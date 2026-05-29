## Evaluation criteria

The queen evaluates four areas:

**Per-spec success-check satisfaction.** Each spec declares a `## Success check` section. The queen reads the diff and verifies that each spec's observable success criteria are met by the delivered code. A spec whose success check is unmet becomes a concern.

**Cross-spec gap detection.** Symbols and files declared as output by one spec and consumed by another must be wired correctly. The queen traces these contracts across spec `## Scope` sections and checks the diff for completeness. See `## Cross-spec gap detection` below.

**Plan acceptance-criteria coverage.** Every bullet in the plan's `## Acceptance` section must be observable in the delivered diff. Items that are unaddressed or only partially addressed surface as concerns.

**Regression-in-multi-touch-files.** When multiple specs edit the same file, the final state of that file must preserve each spec's contributions. A later spec that accidentally undid an earlier spec's changes (e.g., by overwriting rather than merging) surfaces as a concern.
