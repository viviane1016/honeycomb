## Guidance

**One logical change per spec.** Each builder-sized spec produces exactly one commit on the feature branch. Don't squash commits inside the cell — that per-spec structure is intentional, linking each commit back to its spec.

**No force-push.** Don't rewrite history on the builder branch. Bees relies on the ancestor relationship for fast-forward merge. Rewriting would break that.

**Commit discipline.** Let the spec's `## Commit message` guide you. That message was authored by the scribe with Conventional Commits structure; use it as-is. Reference the spec file in the commit footer for traceability.

**Secret-scan hygiene.** Builders must not embed literal secret patterns in test fixtures, example outputs, or commit messages. Placeholder values — `sk-EXAMPLE-KEY`, `AKIA_EXAMPLE_KEY`, `ghp_EXAMPLE_TOKEN` — are fine. Real-shape patterns trigger the entry-gate scan and abort the dispatch. See `wing_practices/secret-handling`.
