## Approved recovery sequences for known bugs

Multi-step procedures that operator-Claude is approved to bake into `ScheduleWakeup` prompts when colony runs encounter known bees bugs. Each recovery names its target bug. On fix, apply the room's drop-pattern protocol below: strip the obsolete entry from this section, append a `vN (dropped <bug>)` sub-entry to `## Recipe-version history`, and audit any in-flight wakeup prompts so they no longer apply the recovery.

### bees#260 — spec post-check undercount on scribe-only units

**Symptom.** `bees spec` emits `outcome=parse_failure_final` (or `outcome=infrastructure_error`) with `parse_error: "expected exactly 1 spec file matching NNN-*.md, found 0"` — but the spec file IS on disk at `.bees/<slug>/specs/NNN-*.md`. The orchestrator may exit `queen_complete` (silent terminal) rather than `queen_failed`, so operator-Claude must detect this from `bees status` rather than relying on `queen_failed` to fire.

**Recovery (7 steps, all from the primary worktree).**

```bash
# 1. Save the on-disk spec content out of the way
cp .bees/<slug>/specs/NNN-*.md /tmp/<slug>-NNN.md

# 2. Stash any uncommitted work and switch to the feat branch
git stash --include-untracked
git checkout feat/<slug>

# 3-4. Restore the spec to the feat branch and commit it
mkdir -p .bees/<slug>/specs
cp /tmp/<slug>-NNN.md .bees/<slug>/specs/NNN-<rest>.md
git add -f .bees/<slug>/specs/NNN-<rest>.md
git commit -m "spec(<slug>): commit NNN-<rest> (bees#260 workaround)"

# 5. Switch back to main
git checkout main

# 6. CRITICAL — restore the feat branch's .bees/<slug>/ to working tree.
# Without this, `bees approve` dies silently because plan.md (tracked on
# feat, untracked on main) is removed from the working tree by step 5.
git checkout feat/<slug> -- .bees/<slug>/

# 7. Re-fire approve. Bees resumes correctly.
nohup bees approve <slug> > /tmp/bees-<slug>-approve.log 2>&1 < /dev/null &
disown
```

**Step 6 is load-bearing.** Skip it and the next `bees approve` exits silently because `plan.md` — tracked on the feat branch, untracked on `main` — is stripped from the working tree by the step-5 `git checkout main`. Discovered only after one silent-fail re-attempt during scarab dogfooding 2026-05-26 → 2026-05-27. Do not omit even if step 5 appears to leave the working tree intact.

**Cap.** If the same colony hits #260 a third time, stop polling and surface to the operator — three failures means something other than the standard undercount is in play, and continued automated retries will mask whatever the real failure is.

### bees#269 — verify rejects on missing Refs footer

**Symptom.** Dispatch cell completes; `bees verify` rejects with `Commit-message references spec path: ... no Refs footer ...`. Amending the cell's HEAD commit does NOT clear the reject — verify reads the spec template's `## Commit message` section, not the cell HEAD commit.

**Prevention (preferred).** Every spec template's `## Commit message` section should end with `Refs: .bees/<slug>/specs/NNN-<task>.md`. Scribes pre-populate this footer at spec stage. If a colony goes into spec without footers, the operator can amend each spec file before `bees dispatch` rather than waiting for the verify reject.

**Recovery (when prevention missed).**

```bash
# 1. Identify the cell branch tip
git -C .bees/<slug>/cells/NNN log -1 --format="%H %s"

# 2. Cherry-pick the cell commit onto feat
git checkout feat/<slug>
git cherry-pick <cell-tip-sha>

# 3. Tear down the orphaned cell worktree
git worktree remove .bees/<slug>/cells/NNN --force
git branch -D bees/<slug>/NNN-<branch-suffix>

# 4. Ship directly
bees ship <slug>
```

The verify reject remains in `~/.bees/events.log` historically; the recovery bypasses it at ship.

### bees#223 — orchestrator silent no-op on existing PR with concerns

**Symptom.** `bees approve` on a colony whose PR is already open exits `outcome=queen_failed, reason=silent_exit_no_pr` after ~3 min. The orchestrator emitted `stage=ship, outcome=success, reason=pr_already_open` mid-run but never addressed the concerns recorded in `.bees/<slug>/accept.md`. The feat branch is unchanged.

**Recovery.** Manual progression. Do NOT re-fire `bees approve` against a colony in this state — that will silent-no-op again on the next attempt.

```bash
# 1. Read the concerns
cat .bees/<slug>/accept.md
gh pr view <num> -R viviane1016/<repo> --json body --jq .body

# 2. If concerns are advisory only, merge the PR as-is
gh pr merge <num> -R viviane1016/<repo> --merge --delete-branch

# 3. If concerns require a real fix, mechanical edit on feat then merge
git checkout feat/<slug>
# ... edit, commit ...
git push origin feat/<slug>
gh pr merge <num> -R viviane1016/<repo> --merge --delete-branch
```
