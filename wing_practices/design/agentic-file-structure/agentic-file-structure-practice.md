## Agentic file structure practice

**Size thresholds.** A file in the 300–500 line range sits in the sweet spot for both context windows and edit-safety: a builder can load it whole, reason over it, and make a focused change without exhausting the context budget. Once a file exceeds 800 lines it enters the yellow zone — not broken, but worth considering a split before you add the next feature. Past 1500 lines, it's red: future builders will load more context than they need, waste tokens on unrelated code, and any two specs that touch the same file cannot run in the same wave without risking an FF-merge conflict.

**One concern per file.** A file should answer one "what is this?" question. Mixed concerns force builders to load unrelated context to make a focused change. If a reviewer can't name the file's responsibility in a short phrase, it's probably carrying more than one.

**Test-file mirroring.** Test files inherit the structure of what they test. A sprawling test monolith is almost always a symptom of a sprawling source file; splitting the source naturally splits the tests, reducing the cognitive load on every future builder that needs to add or modify a case.

**Parallel-builder corollary.** In wave-parallel dispatch, files are the unit of concurrency. Two specs that touch the same file cannot safely run in the same wave — the second builder's FF-merge will fail when the first has already advanced the branch. Two specs that touch disjoint files can run in parallel without conflict. Prefer designs that give each builder its own file; cross-reference `parallelism-safety` for the mechanics.

**When to split proactively.** During planning, scan for files that are likely to exceed 500 lines after the feature lands, or any file that more than one builder will edit in the same wave. In either case, add a wave-0 pre-split spec so the source is in good shape before the parallel work begins.

**Motivating case.** As of this room's authorship, `bin/bees` stands at 6,279 lines and `tests/test_bees.py` at 7,977 lines. The former has produced repeated wave-internal merge conflicts when two specs both modify the main dispatch loop; the latter has caused context-window exhaustion during builder runs that needed to add or modify test cases. These are the costs of an unstructured monolith in an agentic workflow — not unique to bees, but visible there.
