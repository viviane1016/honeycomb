## Behaviour

Ref-update merges have two key properties: they're non-interactive (no merge conflicts to resolve) and non-disruptive (the user's working tree is never touched, even if they're on a different branch). This is distinct from a traditional `git merge` operation, which checks out the target branch, applies commits, and can produce conflicts demanding human resolution.

The preconditions for a successful FF-merge are:
- The cell branch exists and has commits.
- The cell branch is an ancestor of the current `feat/<slug>` tip (or `feat/<slug>` doesn't exist yet).
- The user's primary worktree is not checked out on `feat/<slug>` (enforced at dispatch time).

If any precondition fails, the merge refuses with an error message rather than succeeding in an inconsistent state. This is the safety invariant: merges either succeed completely or fail loudly.

See ADR-0003 for why ref-update merges were chosen over checkout-based merges and discussion of alternatives.
