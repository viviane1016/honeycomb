<!-- drone.md: migrated from role-drone.md.

Hall: hall_architecture
tools: [github-actions, gh-cli, git, shell]
languages: [yaml, shell]
-->

Drones are the autonomous worker tier — workflow-triggered (GitHub Actions), running with no spec and no cell. They carry broader authority than builders: direct commits to `main` for verifiably idempotent cleanup; PRs for generative, forward-looking proposals. All direct-commit passes must be idempotent. If the PR step fails, the cleanup commits stay landed and the diff is written to the job summary; the workflow exits 0.
