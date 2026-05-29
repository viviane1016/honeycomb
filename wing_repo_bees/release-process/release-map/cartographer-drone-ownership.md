## Cartographer drone ownership

`RELEASE_MAP.md` is updated **only via pull request** — the cartographer never commits it directly to `main`. This PR-only constraint ensures the operator reviews the forward plan before it is updated.

- **PR label:** `cartographer`
- **PR title form:** `cartographer: release map refresh (YYYY-MM-DD, release <tag>)`
- **PR body:** references the triggering release tag and, when one exists, links to the prior release-map state for diff context
- **Triggers:** `release: published` (automatic, fires on every published release) and `workflow_dispatch` (for manual bootstrap runs or re-triggers after transient failures)

The cleanup-commit pass (closing shipped issues, striking shipped BACKLOG items) runs as direct commits to `main` on the same trigger; only the release-map update is gated behind a PR.
