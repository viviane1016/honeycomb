<!-- ff-merge-dispatch.md: migrated from arch-ff-merge.md.

Hall: hall_architecture
tools: [git]
-->

After a builder commits to its cell branch, `bees dispatch` fast-forward-merges into `feat/<slug>` by direct ref update: `git branch -f feat/<slug> <cell-branch>` after verifying the cell branch is an ancestor of the feature branch. No checkout, no working-tree changes. If the cell branch isn't an ancestor (a non-ancestor conflict), the merge fails, the cell is preserved, and the queen diagnoses the conflict for manual resolution.
