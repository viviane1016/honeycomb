## Behaviour

The cartographer runs inside a GitHub Actions runner, with no spec and no cell. It receives the triggering release tag (or `workflow_dispatch` payload) and the repository at the commit on `main` at trigger time. Its run produces zero or more direct cleanup commits to `main` plus exactly one PR carrying a refreshed release map. The two tiers of authority are kept strictly separate: cleanup work is direct-commit because it is verifiably idempotent; release-map work is PR-only because it is generative and benefits from operator review.

### Cleanup-pass authority

Direct-commit-to-`main` actions are permitted for cleanup. The cartographer:

- Closes GitHub issues whose described work was shipped, matched against commit messages on `main` since the last release tag.
- Strikes BACKLOG.md items that are shipped or no longer relevant, leaving the rationale text under the struck item so the history reads as a record.
- Normalises BACKLOG.md structure: consistent heading levels, consistent item format, regrouping under target-release headings.

The cleanup pass runs unconditionally on every trigger and is unaffected by the state of any PR — past, present, or proposed. Each cleanup commit uses the message `cartographer: prune shipped items (run <run-id>)`, where `<run-id>` is the GitHub Actions run id. A single run may produce zero, one, or multiple cleanup commits depending on what state needs to be reconciled.

### Idempotency invariants

The cleanup pass obeys four rules verbatim:

- Closing an already-closed issue is a no-op.
- Striking an already-struck BACKLOG item is a no-op.
- Verify state before mutating.
- Running this drone twice on the same repo state must produce the same end state.

These rules matter because release bursts can fire the workflow multiple times within hours. The Apr 20 release day had three releases published in a single day; in that pattern, the workflow runs three times and must produce identical end state at each fixed-point of repo state. A non-idempotent cleanup pass would amplify a release burst into a churn of duplicate commits, double-closed issues, or repeatedly struck BACKLOG entries.

### Release-map authority

`RELEASE_MAP.md` is the forward-looking plan grouping BACKLOG items and open GitHub issues into upcoming releases. Each release-map entry carries a one-line rationale explaining why it belongs to that release. The cartographer creates or updates `RELEASE_MAP.md` **only via a pull request labeled `cartographer`** — never by direct commit. The PR title takes the form `cartographer: release map refresh (YYYY-MM-DD, release <tag>)`. The PR body references the triggering release tag and, when one exists, links to the prior release-map state for diff context.

### Multi-release race handling

Before opening a new release-map PR, the cartographer enumerates open prior cartographer PRs and notifies them, in this order:

1. List open PRs with the `cartographer` label: `gh pr list --label cartographer --state open`.
2. For each open prior cartographer PR, post a comment of the exact form:

   > Superseded by #NEW (based on commit `<sha>`).
   > This PR was based on commit `<old-sha>`. If you want the most current analysis, review #NEW and close this one.

3. Prior PRs are not auto-closed. Operator agency is preserved, along with any in-flight review comments on the older PR.
4. The new PR is opened with the `cartographer` label applied at creation time.

### Inputs

All inputs are read-only:

- `BACKLOG.md`.
- Open GitHub issues, via `gh issue list --state open`.
- Closed GitHub issues since the last release, for cleanup matching.
- Git tag history, via `git tag` and `git log` since the last release.
- Recent merged PRs, via `gh pr list --state merged --limit 50`.
- In-flight `.bees/*/plan.md` and `.bees/*/specs/` for active features not yet shipped.
- Honeycomb rooms — read directly via the `Read` tool. The `palace_recall` MCP is not wired into this runtime; honeycomb is consulted as plain files in the repo.

`~/.bees/events.log` lives on the operator's local machine and is not available inside the GitHub Actions runner. v1 of the cartographer ignores it.

### Outputs

The cartographer produces:

- Direct commits to `main` with the message `cartographer: prune shipped items (run <run-id>)`. Zero, one, or multiple per run.
- Exactly one PR per run, titled `cartographer: release map refresh (YYYY-MM-DD, release <tag>)` and labeled `cartographer`. The body references the triggering release tag and, where applicable, the prior release map.

### Failure mode

The failure-mode contract is cleanup-soft, PR-soft. If `gh pr create` fails — rate limit, transient GitHub outage, auth issue — the cleanup commit (if any) remains landed on `main`; the unfiled release-map diff is captured to the workflow's `$GITHUB_STEP_SUMMARY` artifact; the workflow exits 0. The operator re-triggers the workflow via `workflow_dispatch` when the underlying issue is resolved. The workflow does not retry inline.
