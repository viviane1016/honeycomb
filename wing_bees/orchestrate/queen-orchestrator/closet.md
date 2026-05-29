<!-- queen-orchestrator.md: migrated from role-queen-orchestrator.md.

Hall: hall_architecture
tools: [bees, gh, git, bash, mcp-honeycomb]
models: [claude-opus]
languages: [python, bash, json]
-->

Long-running queen launched by `bees queen-orchestrate <slug>`; drives spec → dispatch → accept → ship for one feature via `--json` envelope tool calls. Files `queen-filed` GitHub issues for unresolved failures (verify-reject, builder-timeout, ff-merge-conflict, etc.); soft-fails to `~/.bees/unfiled-issues/`. Exits clean with PR open or all failures filed. Safely restartable: status-first orientation, ship PR-exists no-op, no-double-queen gate.
