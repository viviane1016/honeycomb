## Behaviour

The taster is the master-winemaker of the honeycomb. Where the cartographer mechanises release housekeeping and the sapper mechanises test-quality, the taster brings expert reasoning to bear on honeycomb-content quality itself: is the guidance in this room still right? Has merged work falsified a claim a room makes? Has an open `queen-diagnostic` revealed a gap a room should have closed but does not? Has an upstream model or runtime change moved the ground under our feet? The drone tastes the honeycomb daily and proposes petitions where it can name a real, evidenced gap. Real authority, expert reasoning, daily cadence — that is what makes the analogy hold.

Single-tier PR-only authority is correct because honeycomb-content judgements are entirely generative. A proposed amendment to a room is a fresh act of writing, not an idempotent reconciliation. Every petition requires a reviewer to judge whether the gap is real, whether the proposed wording is the strongest available formulation, and whether the petition belongs in the named room at all. The PR tier is the right container for that judgement; the taster never direct-commits to `main`.

Opus single-pass execution is the right shape because quality assessment of natural-language guidance is reasoning-heavy work that the two-pass cost-optimisation trick used by the sapper does not apply to. The sapper's cheap first pass filters a large search space of source files and coverage artifacts down to a top-20 list before invoking the more expensive model; the taster's input is already small (one week of merged PRs, a handful of open queen-flagged issues, two external feeds) and the judgement at every step is the kind of cross-room synthesis that the cheap-pass model cannot reliably perform. So the taster runs Opus once, end to end, and bounds cost via the rate-limit guard instead.

### Contrast with hc-auditor-drone

The taster is the daily precursor that fills the gap until `hc-auditor-drone` ships. The two drones sit at different cadences and depths:

- **Cadence.** Taster runs daily; `hc-auditor-drone` will run monthly.
- **Dependency.** Taster has no `hc-meta` dependency — it judges quality against the evidence in front of it. `hc-auditor-drone` will depend on `hc-meta` (the honeycomb's self-description) and audit against it.
- **Output.** Taster emits petition-only PR bodies — at most one PR per run, advisory only. `hc-auditor-drone` will produce a full audit-briefing document.
- **Depth.** Taster is Opus single-pass on the last week's evidence. `hc-auditor-drone` will run a deeper multi-pass audit against OWASP/CIS/CVE feeds, the Anthropic model-card history, and the full corpus of merged PRs since the last audit.

When `hc-auditor-drone` lands, the taster keeps the daily slot; the auditor takes the monthly deep dive. Until then, the taster is the only daily quality signal on honeycomb content.

### Trigger

- `schedule: cron "0 6 * * *"` — daily 06:00 UTC, before the operator's workday. The exact cron expression is set in the workflow YAML; this room fixes the cadence as daily.
- `workflow_dispatch` — manual escape hatch. Bypasses the rate-limit guard entirely.

### Rate-limit guard

The rate-limit guard bounds cost in the absence of a cheap-model pre-filter pass. At most one successful taster run per UTC calendar day is permitted.

1. Query the most recent successful workflow run: `gh run list --workflow taster.yml --status success --limit 1 --json createdAt --jq '.[0].createdAt // empty'`.
2. Extract the UTC date prefix (`YYYY-MM-DD`) from the returned timestamp.
3. If that date matches today (UTC), write `rate-limited: last successful run at <ts>` to `$GITHUB_STEP_SUMMARY` and exit 0.
4. Otherwise, proceed.

`workflow_dispatch` bypasses this guard — operators may force a manual run after correcting an evidence source or after a model-card update lands mid-day.

### Evidence sources

All inputs are read-only:

- **Merged PRs in the last 7 days:** `gh pr list --state merged --search "merged:>=$(date -u -d '7 days ago' +%Y-%m-%d)"`. Read titles, bodies, and diffs for signals that current honeycomb guidance is wrong, stale, or absent.
- **Open queen-flagged issues:** `gh issue list --label queen-diagnostic,queen-deferred --state open`. These are queen-emitted signals about gaps the planning stage had to improvise around; an open issue that points at a missing honeycomb room is the strongest possible evidence for a petition.
- **External feeds (one light check each):** the Anthropic model-card changelog and the Claude Code release notes, fetched via a single `WebFetch` each. Failure is non-fatal — log the failure to `$GITHUB_STEP_SUMMARY` and continue. The external feeds catch upstream changes (a new model retiring, a Claude Code feature affecting a workflow contract) that local evidence cannot surface.

Honeycomb rooms themselves are read directly via the `Read` tool — the `palace_recall` MCP is not wired into this runtime; honeycomb is consulted as plain files in the repo.

### Exclude-file mechanism

`.bees/taster-exclude` is a gitignore-style file (one path or glob per line, `#` comments allowed, blank lines OK) loaded from the repo root before the assessment. Absence means no exclusions. The exclude list gates which honeycomb rooms the taster may target with a petition.

The bees repo ships `.bees/taster-exclude` listing `honeycomb/wing_bees/role-drone-taster.md` to prevent self-referential petition loops — evolving the taster's own contract is a deliberate human edit, not a drone proposal. Operators may add other rooms (e.g. mid-flight rewrites) to suppress petitions during a known-unstable window.

### Confidence threshold

A petition fires only when the taster can name both of the following, in the petition body:

- (a) the specific room whose guidance is wrong, stale, or absent; and
- (b) the specific PR, issue, or external source that demonstrates the gap.

Vague impressions — "this room feels thin," "this seems out of date" — do not qualify. If the taster cannot point at a concrete piece of evidence and a concrete target room, no petition is emitted for that observation.

The v1 rubric is deliberately provisional. It may tighten in v1.x once we have operator feedback on petition acceptance rates; for now, "named room + named evidence" is the bar.

### Output

At most one PR per run:

- Title: `taster: honeycomb-quality petitions (YYYY-MM-DD)`
- Label: `taster` (applied at creation time)
- Body: zero or more `<<<PALACE PROPOSAL honeycomb/<wing>/<room>.md>>>...<<<END>>>` fenced blocks rendered inside the PR body, each accompanied by the evidence citation (PR number, issue number, or external URL) that triggered it.

**These petition blocks are advisory PR-body content.** They are not parsed by `parse_palace_proposal_blocks` in `bin/bees` — that parser is specifically scoped to queen plan output captured at the spec stage of the bees pipeline, and the taster runs outside that pipeline. The taster's petitions live as text inside a reviewer-visible PR body; operators read each block, judge it on the merits, and apply accepted petitions to the named honeycomb room by hand. There is no auto-extraction, no auto-merge, no programmatic lifecycle. The PR body is the artefact.

### No-PR-on-nothing

If no observation clears the confidence threshold — that is, every candidate petition the taster considered failed to name both a specific target room AND a specific piece of evidence — the run produces zero PRs. The taster writes a short assessment summary to `$GITHUB_STEP_SUMMARY` (what it surveyed, why nothing qualified) and exits 0. A no-petition run is a normal outcome, not a failure.

### Supersede protocol

Before opening a new taster PR, the drone enumerates open prior taster PRs and notifies them:

1. List open PRs with the `taster` label: `gh pr list --label taster --state open`.
2. For each open prior taster PR, post a comment of the exact form:

   > Superseded by #NEW (based on commit `<sha>`).
   > This PR was based on commit `<old-sha>`. If you want the most current analysis, review #NEW and close this one.

3. Prior PRs are not auto-closed. Operator agency is preserved, along with any in-flight review comments on the older PR.
4. The new PR is opened with the `taster` label applied at creation time.

### Failure mode

The taster drone is single-tier so only the PR-soft half of the failure-mode contract applies — there is no cleanup pass to land first. If `gh pr create` fails (rate limit, transient GitHub outage, auth issue), the unfiled petition text is captured to `$GITHUB_STEP_SUMMARY` and the workflow exits 0. The operator re-triggers via `workflow_dispatch` when the underlying issue is resolved. The workflow does not retry inline.
