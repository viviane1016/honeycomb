## Behaviour

Estimation drift is a slow signal — individual timing noise washes out over weeks, not days. Weekly batching amortises the cost of the analysis (one Claude call per week) against the signal value (meaningful drift visible after several merged features accumulate). The cron fires at Monday 06:00 UTC so the run completes before the operator's Monday standup.

Single-tier authority is correct for the retro drone because there is no idempotent cleanup analogue for estimation analysis. Striking a BACKLOG item is safe to repeat; proposing an updated model-calibration room is not — each proposal is a fresh generative act. All retro drone outputs therefore require operator review before landing, and the PR tier is the right container for that review.

`workflow_dispatch` serves as an escape hatch for high-cadence projects where weekly batching is too infrequent, and for operators who want to re-run after correcting data.

### Trigger

- `schedule: cron "0 6 * * 1"` — weekly Monday 06:00 UTC. Chosen so the run completes before the operator's Monday morning standup. Weekly cadence is the v1 default with `workflow_dispatch` as escape hatch — too long for high-cadence projects, too short for low-cadence; v2 may switch to a release-published or hybrid trigger.
- `workflow_dispatch` — manual escape hatch. The rate-limit guard is bypassed for manual triggers.

### Inputs

All inputs are read-only:

- Committed `.bees/*/plan.md` files, specifically the `## Delivery estimates` section.
- Committed `.bees/*/log.md` files, specifically the stage-transition timestamps.
- `gh pr list --state merged --limit 50 --json title,createdAt,mergedAt,labels` for wall-clock PR timing.
- Honeycomb rooms — read directly via the `Read` tool. The `palace_recall` MCP is not wired into this runtime; honeycomb is consulted as plain files in the repo.

`~/.bees/events.log` lives on the operator's local machine and is not available inside the GitHub Actions runner. The drone optimises for shipped (merged) features; features dispatched but never merged are invisible.

### Outputs

At most one PR per run:

- Title: `retro-drone: estimation-gap petition (YYYY-MM-DD)`
- Label: `retro-drone`
- Body: petition fenced block(s) using the `<<<PALACE PROPOSAL honeycomb/wing_models/<room>.md>>>...<<<END>>>` shape from `petitions-format.md`, plus an evidence table mapping feature slugs to estimated-vs-actual hours.

If no drift above threshold: zero PRs; write `no drift detected` to `$GITHUB_STEP_SUMMARY`.

### Dedup

Before opening a new estimation-gap PR, the retro drone enumerates open prior retro-drone PRs and notifies them:

1. List open PRs with the `retro-drone` label: `gh pr list --label retro-drone --state open`.
2. For each open prior retro-drone PR, post a comment of the exact form:

   > Superseded by #NEW (based on commit `<sha>`).
   > This PR was based on commit `<old-sha>`. If you want the most current analysis, review #NEW and close this one.

3. Prior PRs are not auto-closed. Operator agency is preserved, along with any in-flight review comments on the older PR.
4. The new PR is opened with the `retro-drone` label applied at creation time.

### Failure mode

The retro drone is single-tier so only the PR-soft half of the failure-mode contract applies — there is no cleanup pass. If `gh pr create` fails — rate limit, transient GitHub outage, auth issue — the unfiled petition diff is captured to the workflow's `$GITHUB_STEP_SUMMARY`; the workflow exits 0. The operator re-triggers via `workflow_dispatch` when the underlying issue is resolved. The workflow does not retry inline.
