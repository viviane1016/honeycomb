<!-- commit-granularity.md: migrated from commit-granularity.md.

Hall: hall_rubric
tools: [git]
-->

On a feature branch, default to **one logical change per commit**: adding a module is one commit, the tests for it are the next, the doc updates are a third. Each commit message captures the *why* of that step. Don't batch unrelated edits into a single mega-commit. Review, revert, and `git bisect` all reward small commits; the narrative of the branch should read forward. PR squash-on-merge handles the public history — your in-branch history is for the operator.
