<!-- queen-accept-gate.md: migrated from stage-accept.md.

Hall: hall_procedure
-->

Within `bees ship`, the queen accept gate verifies the full feature delivery before `gh pr create`. The queen receives the annotated briefing (including `## Operator amendments`), plan, all spec bodies, and the full `git diff`. Four evaluation areas: per-spec success checks, cross-spec gap detection, plan acceptance-criteria coverage, and regression-in-multi-touch-files. Output: APPROVE or CONCERNS. Advisory, not blocking.
