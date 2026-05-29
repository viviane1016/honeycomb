## Plan amendments and in-flight work

Plan approval is a hard gate. Once approved, the plan is the contract for spec, dispatch, and ship; those stages do not pause for re-approval.

Queen-accept reads the plan as it stood at spec time — plan edits made after spec runs are not re-validated against in-flight work.

Minor intent changes the operator wants the queen to consider at accept time go into `briefing.md` under `## Operator amendments` — timestamped entries describing what changed and why. Queen-accept reads the annotated briefing as the reference for operator intent and surfaces concerns when the feature diff diverged from the briefing without a matching amendment note. See `briefing-template` for the format.

Full optimistic dispatch — concurrent plan amendment with in-flight specs that retarget builders already running — is a future direction recorded in BACKLOG, not a v1 supported pattern. In v1, an operator who wants to redirect material scope re-runs `bees plan`.
