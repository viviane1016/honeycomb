## Guidance

**Watching progress.** `~/.bees/orchestrate/<slug>.log` captures the orchestrator's stdout/stderr in real time. `bees status` surfaces the current stage, the PID, and the count of issues filed this run. The dashboard's per-feature view (`bees dash`) is the operator's preferred read-out.

**Inspecting unfiled-issues.** If `bees status` reports any soft-failed issues, look at `~/.bees/unfiled-issues/<slug>-*.md` — those are ready-to-paste issue bodies with the dedup-key footer already in place. The operator files them by hand via `gh issue create` or the GitHub web UI.

**Aborting.** Send SIGTERM to the orchestrator PID surfaced by `bees status`. The orchestrator catches the signal at stage boundaries and exits cleanly, leaving the state file consistent for a future `bees queen-orchestrate <slug>` resume.

**When to use `--strict-accept`.** Pre-release branches, compliance-gated features, anything where a CONCERNS should pause for operator review rather than ship-and-discuss.

<!-- additional content from stage-orchestrate.md -->

## Guidance

**`bees status` is your read-out.** Once `bees queen-orchestrate` launches, `bees status <slug>` is the canonical view: it surfaces the orchestrator PID, the current stage, the count of issues filed this run, and any entries in `unfiled-issues/`. The dashboard (`bees dash`) renders the same data live per-feature.

**Aborting a run.** The orchestrator's PID is in `~/.bees/state/<slug>.json` and surfaced by `bees status`. Send SIGTERM to that PID; the orchestrator catches it at stage boundaries, exits cleanly, and leaves the state file in a consistent shape for a future `bees queen-orchestrate <slug>` resume.

**When to use `--strict-accept`.** Pre-release branches and compliance-gated features where a CONCERNS verdict should pause the pipeline and surface as a tracked issue instead of becoming a PR-body section. Without `--strict-accept` the operator still sees the concerns at PR review, but the PR is open.

**Reading `unfiled-issues/`.** Each file in `.bees/<slug>/unfiled-issues/<NNN>.md` is a ready-to-paste GitHub-issue body, with the dedup-key footer already present. File them by hand via `gh issue create --label queen-filed --body-file <path>` or the GitHub web UI.
