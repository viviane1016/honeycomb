## Enforcement and operator override

Bees now enforces prior-commit detection with an escalated stderr message (naming the conflicting commit SHAs and pointing at `--restart`) rather than a silent skip. The silent re-run trap — where `bees dispatch` appeared to succeed but actually skipped all already-merged specs — has been closed. If you re-run `bees dispatch` after prior builder commits exist on the branch, you will see a clear error and be directed to use `--restart` for intentional rework.

Use `bees dispatch --restart <slug>` for intentional rework. The flag strips `feat/<slug>` back to its merge-base with `main` before launching, preserving commits whose subject matches `bees(plan|spec):`. Review what will be stripped before confirming.
