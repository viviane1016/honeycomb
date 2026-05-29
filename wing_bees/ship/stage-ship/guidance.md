## Guidance

**PR title format.** Use `<type>(<scope>): <imperative description>`. Type ∈ {feat, fix, refactor, docs, test, chore}. Scope is optional (e.g. `auth`, `dashboard`). Description in present imperative, ≤72 chars total. Example: `feat(auth): add OAuth login flow`.

**PR body structure.** The PR body is templated; see `pr-body-template.md` for the exact layout. Sections: Summary (one paragraph, context-only), Work (bullet list of specs), Test plan (consolidated from specs), Linked issues (auto-extracted from briefing), Risks (from plan), footer (version + links to plan and honeycomb trace).

**Merge strategy.** Recommend rebase-and-merge or merge commit. Squashing destroys the per-spec commit traceability bees maintains. Each spec produces one commit referencing its spec file; that's a feature, not noise. If your org mandates squash-and-merge, preserve spec references in the squashed commit message footer.

**Branch protection.** For operators: configure required status checks (pytest, bandit, secret-scan). This ensures code quality gates run before merge.
