<!-- runtime-tier-system.md: migrated from claude-code-runtime.md.

Hall: hall_rubric
tools: [mcp]
-->

Stages run at three tiers: `High` (planning/spec), `Med` (default builder), `Low` (classification). Skill content references tiers; your install config maps them to concrete models. MCP servers live in `~/.bees/install.toml`: `{"mcpServers": {"<name>": {"command": "...", "args": []}}}`. Plan/spec use read-only tools (`Read,Grep,Glob`); builder stage has broader access to edit and commit.
