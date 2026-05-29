<!-- retro-drone.md: migrated from role-drone-retro.md.

Hall: hall_architecture
tools: [github-actions, gh-cli]
-->

The retro drone is workflow-triggered (`schedule: cron "0 6 * * 1"` + `workflow_dispatch`). Single-tier authority: PR-only — no cleanup pass in v1 since all retro outputs are generative. Petitions target `honeycomb/wing_models/*.md` per `petitions-format.md`. Dedup via supersede comments on prior open `retro-drone` PRs; prior PRs stay open.
