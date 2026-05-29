## Behaviour

### Why it happens

`bees dispatch` skips specs whose NNN appears in any commit body on `feat/<slug>`
matching `.bees/<slug>/specs/NNN-`. Old builder commits that follow the convention
(e.g. `Implements .bees/my-feature/specs/003-revise-foo.md`) leave NNN `003` in the
scan. When you `bees spec --force` and rename specs, the new spec `003-something-new.md`
has a different filename but the same NNN — so dispatch sees `003` as "already merged"
and skips the new builder entirely.

Result: `bees spec --force` correctly writes new spec files, but `bees dispatch` runs
only the specs whose old builder commit happened to use a non-standard ref format. The
rest silently ship the old implementation.

### How to detect the problem

After dispatch completes, check for unexpected "already merged, skipping" lines in
output when you expected fresh builds:

```
dispatch: 003 already merged, skipping   ← suspicious if you just re-specced
```

Verify by inspecting what's actually on the branch vs what the new specs required:

```bash
git log --oneline feat/<slug> ^main        # look for old builder commit messages
git diff --name-only main feat/<slug>      # check which files are actually changed
```

If key files (e.g. new honeycomb rooms, updated workflow) are missing or contain old
content, old builder commits are blocking the dispatch.

### The fix: strip and re-dispatch

Before re-dispatching a revised feature, strip the old builder commits from the
branch. Preserve only the new plan commit and new spec commit, then re-dispatch fresh.

**Step-by-step:**

```bash
# 1. Find the new plan commit (the one from bees plan --force)
git log --oneline feat/<slug> ^main
# Identify NEW_PLAN_SHA (the bees plan commit from the revision)

# 2. Create a clean branch from the new plan commit
git checkout NEW_PLAN_SHA -b temp/rework-<slug>

# 3. Cherry-pick the new spec commit on top
git cherry-pick NEW_SPEC_SHA   # the 'bees spec: <slug> (N specs)' commit

# 4. Force-push to the feature branch (updates the open PR in place)
git push origin temp/rework-<slug>:feat/<slug> --force

# 5. Return to main and clean up the temp branch
git checkout main
git branch -D temp/rework-<slug>

# 6. Re-dispatch — now all specs have no prior builder commits
bees dispatch <slug> --ignore-untracked
```

The open PR is updated in place (force-push rewrites the branch). No need to close
and reopen.

### Which commits to preserve

Keep:
- The new `bees plan` commit (written by `bees plan --force`)
- The new `bees spec` commit (written by `bees spec --force`)
- Any new builder commits you want to keep (cherry-pick individually)

Drop:
- The old `bees plan` commit
- The old `bees spec` commit  
- All old builder commits

### Variant: partial re-dispatch

If only some specs changed (e.g. you revised specs 003–005 but 001–002 were correct),
keep the old builder commits for the unchanged specs and strip only the ones you
want to re-run. Identify which old builder commits correspond to which NNNs via
`git log --format="%H %s" feat/<slug> ^main` and drop only the ones for the
NNNs you're revising.

### If the branch has already been force-pushed

If you force-pushed to update an open PR and then discovered the dispatch was stale,
the fix is the same — re-run the strip procedure from the new state. The PR just
updates again on the next force-push.
