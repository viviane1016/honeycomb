## Behaviour

**When to use the pattern.** A spec must sometimes be hand-implemented rather than dispatched — for example:
- The spec has an internal inconsistency the builder would reject.
- The operator needs to patch a test fixture alongside the production change.
- The required change demands operator judgment that a builder cannot exercise.

**The problem — the dep-detection mechanism.** `already_merged_nnns` in the dispatch harness detects satisfied dependencies by scanning `git log --format=%B feat/<slug>` for lines matching `.bees/<slug>/specs/NNN-`. A manual commit that lacks this reference line is invisible to the dep graph. When you subsequently dispatch a spec that declares `depends-on: [NNN]` for the manually-implemented spec, bees raises:

```
dep references unselected spec: NNN
```

even though the work is done.

**The fix — amend to embed the spec-path reference.** Before dispatching any spec that depends on the manually-implemented one, amend the manual commit to add the reference line to its body:

```bash
git checkout feat/<slug>
git commit --amend -m "$(git log -1 --format=%s)

Implements .bees/<slug>/specs/NNN-<task-name>.md"
git checkout -   # return to previous branch
```

After the amend, `bees dispatch <slug> NNN+1` will see NNN in the satisfied set and proceed normally.

**The lookup rule.** The `Implements …` reference line is the only thing bees looks for — the rest of the commit body is irrelevant to dep detection.
