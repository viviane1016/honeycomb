<!-- sapper-drone.md: migrated from role-drone-sapper.md.

Hall: hall_architecture
tools: [github-actions, pytest, gh-cli]
models: [haiku, sonnet]
languages: [python, cpp]
-->

Weekday daily cron (`"0 5 * * 1-5"` + `workflow_dispatch`). Single-tier PR-only authority. Activity guard: skips if no commits to non-excluded paths since last sapper PR. Two-pass LLM: Haiku triage → Sonnet proposal, top-20 gap cap. Detects coverage gaps and assertion-weakness heuristics (negative-only, trivially-true, bare-swallow). Dedup via supersede comments on prior open sapper PRs.
