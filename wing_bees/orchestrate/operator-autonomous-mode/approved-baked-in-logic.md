## Approved baked-in logic

The following behaviours are approved to be baked into operator-Claude's `ScheduleWakeup` prompts for the bees autonomous phase. No other logic should be silently introduced.

- **Status-table on wakeup (#200).** On each wakeup, run `bees status <slug>` and surface a compact status table to the user showing current stage, orchestrator PID, specs complete/total, and issues filed. Do not skip this even if the prior wakeup already showed a table.
- **Plan → spec → dispatch auto-cascade on success.** After plan succeeds and the operator approves, automatically run `bees approve <slug>` (foreground, ~instant) followed by `nohup bees queen-orchestrate <slug>` (background). The approve gate is the only required pause.
- **FF-merge surfacing in operator updates.** When `bees status` reports FF-merge completions, include the merged spec NNNs in the wakeup update to the user so they know which units have landed.
- **Wave-progress table format.** When wave events are present, `bees status <slug>` auto-includes a `Wave | Status | Specs` table. Surface this table verbatim in the wakeup update; do not reformat it.
- **Dogfood via `bees approve` + `bees queen-orchestrate` for new bees-self features.** When running a bees feature against the bees repo itself, run `bees approve <slug>` (foreground gate) then `nohup bees queen-orchestrate <slug>` (background orchestrator).
