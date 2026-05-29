## Waves

Each spec in the work breakdown may declare optional `depends-on: [NNN, ...]` frontmatter lines listing other specs (by their NNN ordinal) that must complete before this spec begins. Bees parses these dependencies via `_build_dispatch_graph` (Kahn's topological sort algorithm), checks for cycles (fatal), and emits a wave schedule: a list of waves, where each wave is a list of NNNs with no inter-dependencies.

Dispatch processes waves sequentially. For wave N:
1. Create a cell for each spec in the wave.
2. Launch builders in parallel via `ThreadPoolExecutor(max_workers=parallelism)` (default 4, controlled by `--parallel N` or `BEES_DISPATCH_PARALLEL`).
3. Wait for all builders to commit (or timeout/fail).
4. For each builder, run scribe-verify against the spec and the builder's diff. The scribe runs automatically and emits `APPROVE` or `REJECT` with a reason. `APPROVE` proceeds to FF-merge; first `REJECT` triggers spec-revision and a second builder attempt; only a second `REJECT` (or revision failure) preserves the cell with feedback and skips the merge for that spec. Infrastructure errors proceed with FF-merge (advisory, not blocking).
5. For each builder, FF-merge the cell branch into `feat/<slug>` via ref update.
6. If all merges succeed, proceed to wave N+1. If any merge fails, bees classifies the failure mode before deciding whether to invoke `_queen_diagnose_conflict`:

   | `outcome` | `fail_reason` | Cause | Queen diagnoses? |
   |---|---|---|---|
   | `"conflict"` | `"non-ancestor"` | Content conflict — two specs edited the same file | Yes |
   | `"blocked"` | `"feat-branch-checked-out-elsewhere"` | `feat/<slug>` checked out in another worktree | **No** |
   | `"failure"` | `"<exception type>"` | Infrastructure error (lock, permission, I/O) | No |

   For `"blocked"`, bees emits a clear stderr message naming the extra worktree path and the `git worktree remove <path>` remediation, then exits without invoking Opus. For genuine `"conflict"` outcomes, the queen diagnoses and the operator resolves manually.

**Pre-wave output-files overlap check.** Before launching each wave, `cmd_dispatch` computes the union of `output-files` across the wave's specs. If any two specs in the same wave share at least one file without one depending on the other, dispatch refuses with a stderr error naming the overlapping pair, the shared file, and the remediation (add `depends-on` to the later spec). This is belt-and-suspenders relative to the spec-stage inference pass — it catches overlaps from hand-edited specs or retroactively added `output-files` declarations.
