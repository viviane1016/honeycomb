<!-- role-drone-cartographer.md: migrated from role-drone-cartographer.md.

Hall: hall_architecture
tools: [github-actions, gh-cli]
-->

The cartographer drone is workflow-triggered (`release: published` + `workflow_dispatch`). Two-tier authority: idempotent direct commits to `main` for cleanup (close shipped issues, strike shipped BACKLOG items, normalise structure) and PR-only `RELEASE_MAP.md` proposals labeled `cartographer`. Reruns on identical state are no-ops. Multi-release races resolve via supersede comments on prior open `cartographer` PRs; the prior PRs stay open.
