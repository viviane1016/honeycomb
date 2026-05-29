## Behaviour

**Dependency declaration.** Each spec in `## Scope` may include optional frontmatter:
```
depends-on: [NNN, ...]
```
The list names specs (by their NNN ordinal) that must complete and merge before this spec begins. Omitting the line means the spec has no dependencies and may run in wave 1.

**Graph construction.** After scribe produces all drafts, `_build_dispatch_graph` parses the `depends-on:` frontmatter from each draft, constructs a DAG, checks for cycles (fatal), and emits a wave schedule. Each wave is a list of NNNs with no inter-dependencies. Dispatch processes waves sequentially: wait for all builders in wave N to commit and merge successfully before starting wave N+1.

**Queen review of dependencies.** The queen receives the candidate wave structure computed over the drafts and a copy of each `## Scope` section. She is explicitly asked to verify that each spec's `depends-on` matches what the spec actually references (i.e., which other specs' outputs it imports or depends on). If a `depends-on` list is wrong, she emits `<<<DEPS NNN>>>` (frontmatter-only patch) containing the corrected line; the rest of the spec body is preserved verbatim. The harness applies DEPS patches before validating and writing specs.

**Wave conflicts.** When wave-siblings touch overlapping files, FF-merge detects the conflict: the second builder's cell branch is no longer an ancestor of the advanced feature branch tip, the merge fails, and the cell and branch are preserved while the dispatcher invokes the queen for diagnosis. See `arch-ff-merge` for the diagnosis flow, the three write locations, and the human-resolution options.

**Queen diagnosis.** When FF-merge returns `False`, the dispatcher calls `_queen_diagnose_conflict` with:
- The failed builder's diff (staged + unstaged changes)
- The commits that landed on `feat/<slug>` after the builder started (the "sibling commits")
- The spec body for context

The queen analyzes this data and emits a plain-text diagnosis: likely cause (e.g., "both specs edit `honeycomb/arch-locking.md`"), suggested manual resolution (e.g., "rebase cell branch on top of sibling commits and resolve conflict"), and expected files to check. This diagnosis is written to `.bees/<slug>/cells/NNN/.queen-diagnosis.md`, appended to `.bees/<slug>/log.md`, and printed to stderr for the operator to see.

**Human resolution.** The operator manually resolves the conflict by either:
1. Re-dispatching spec NNN after tightening its `depends-on` list to include the sibling spec(s) it actually conflicts with (so they no longer run in the same wave), or
2. Rebasing the cell branch on top of the sibling commits and resolving the conflict files in the cell (then waiting for the next dispatch attempt), or
3. Modifying one of the specs' `## Scope` so they no longer overlap.

Bees does not auto-rebase or auto-merge in v1.

**Manual implementation.** A spec may be implemented directly on `feat/<slug>` and then made visible to the dep graph by amending the commit body to include the `.bees/<slug>/specs/NNN-` reference line that `already_merged_nnns` keys off. See `bees-patch` for the full workflow and the canonical amend command.
