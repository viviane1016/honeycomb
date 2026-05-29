## Plan amendments in v1

In v1, queen-accept reads the plan as it stood at ship time. The plan is treated as fixed from the moment the operator approved it; the queen does not account for amendments to plan content that occurred after approval.

Optimistic dispatch — running spec or dispatch stages concurrently with in-flight plan amendments — is recorded in `BACKLOG.md` as a future direction, not a supported v1 pattern. In v1, amend the plan before running the spec stage, or after all specs are complete; do not amend mid-flight.

The `## Operator amendments` mechanism in `briefing.md` covers minor in-flight intent changes without requiring a plan re-approval cycle. Use it for changes in intent that do not invalidate the overall work breakdown.
