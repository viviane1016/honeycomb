## Guidance

**When to declare deps.** Declare a dependency if your spec's implementation reads or depends on the output of another spec. For instance, if spec 005 introduces a new field to a config, and spec 007 code that reads it, then 007 should list `depends-on: [005]`. If specs don't actually interact (they edit disjoint files), omit the dependency; bees will run them in parallel, which is faster.

**Interpreting a conflict diagnosis.** If the queen's diagnosis names specific files, open those files in both the cell branch and the sibling commits to understand the overlap. The diagnosis suggests which spec's changes should take precedence or how to merge them manually. Always reason about the conflict yourself rather than blindly picking a merge strategy.

**Testing concurrent builds locally.** Before landing specs with non-trivial dependencies, test them locally via `bees dispatch <slug> --parallel 4` to exercise the wave-based flow. Catch dependency errors before they hit CI.
