<!-- taster-drone.md: migrated from role-drone-taster.md.

Hall: hall_architecture
tools: [github-actions, gh-cli, webfetch]
models: [claude-opus]
-->

Daily cron + `workflow_dispatch`. Single-tier PR-only authority labeled `taster`. Opus single-pass (no cheap-model pre-filter). Rate-limit: ≤1 successful run per UTC day; dispatch bypasses. Evidence: merged PRs (7d), open queen-diagnostic/queen-deferred issues, light model-card/Claude Code release-notes WebFetch. Advisory `<<<PALACE PROPOSAL>>>` blocks in PR body — not parsed by `parse_palace_proposal_blocks`. `.bees/taster-exclude` gitignore-style. Supersede-comment dedup.
