## Guidance

**Interpreting output.** The status report includes:
- Plan status: approved or pending.
- Spec summaries: count and names.
- Cell status: active, completed, or failed (with preservation reason if failed).
- Open PR: URL and CI check status.
- Ahead-count: commits ahead of the base branch.
- Recent events: stage transitions, timings, costs.

Use this between stages to verify progress or after ship to check CI state before merging.

**CI polling.** If CI is still running after ship, re-run `bees status` to see updated check results. No need to wait — bees doesn't block on CI; it reports state as-is.
