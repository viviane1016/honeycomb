<!-- manual-amend.md: migrated from manual-amend.md.

Hall: hall_procedure
tools: [bees, git]
-->

Manual implementation + amend pattern: implement a spec by hand on `feat/<slug>` and amend the commit to include `Implements .bees/<slug>/specs/NNN-<task>.md` in its body. This reference is the only signal `already_merged_nnns` scans for — without it, bees treats the spec as unmerged and raises an error when dispatching dependents. After implementing, run `bees mark-patched <slug> <NNN>` to emit the dispatch event so the dashboard and dep graph reflect the completed state.
