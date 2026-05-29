## Behaviour

The queen-accept gate runs as a fresh `claude -p` Opus subprocess dispatched by the ship stage. It receives:

- The annotated `briefing.md` — the original briefing sections plus any `## Operator amendments` the operator appended.
- `plan.md` in full, with particular attention to the `## Acceptance` section.
- Every `.bees/<slug>/specs/NNN-*.md` body.
- The full `git diff feat/<slug>...<base>` — the complete change since the feature branch diverged from the base.

The queen emits exactly one output block:

- `APPROVE <one-line summary>` — the diff satisfies all acceptance criteria; proceed to `gh pr create`.
- `CONCERNS` followed by a numbered list, each item citing the plan section (`## Acceptance`) or spec section (`## Success check` or `## Scope`) it references.

The harness writes the CONCERNS body verbatim to `.bees/<slug>/accept.md`, prints it to stderr, and passes it to `build_pr_body`, which appends it as an `## Acceptance concerns` section in the PR body. Ship continues without exit-nonzero; the operator decides whether to address concerns before merge.

This gate is colony-internal and advisory. It is not a third human gate; the two build-and-ship human gates (plan approval, PR review) remain the only pauses in the main pipeline. The queen-accept step runs autonomously within `bees ship`, between dispatch completion and the PR open.
