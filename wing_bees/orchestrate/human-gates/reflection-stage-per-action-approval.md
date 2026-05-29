## Reflection-stage per-action approval

Retro and debug produce outputs beyond code changes. Some touch git (edits to BACKLOG.md, queen-file, petitions at `.bees/<slug>/`) and flow through normal PR review. Others bypass git entirely:

- **GitHub issues filed** via `gh` — visible immediately, no rollback.
- **External notifications** (Slack, email, etc.) — same.
- Anything that hits a shared system with side-effects.

For these, the two build-and-ship gates are insufficient. Once the queen files an issue, it's filed — there's no PR to review before it lands.

Per ADR-0012, retro and debug emit a **proposed-actions list** at `.bees/<slug>/proposed-actions.md`. The operator approves or declines each action. Bees executes only the approved subset.
