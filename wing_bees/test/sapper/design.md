# sapper — design

## Authority model

Single-tier issue-only. The sapper does not write code, does not open
PRs, and does not modify content. All output is diagnostic GitHub
issues. Rationale: sapper findings are advisory by nature — every
finding requires a human to judge whether the gap is real and how to
strengthen the test. Stubs go stale; clear diagnosis does not.

## Two-pass LLM design

Pass 1 (Haiku triage) reads coverage artifacts and source files,
identifies findings, and produces a top-N list to `/tmp/sapper/gaps.md`.
Pass 2 (Haiku diagnosis) reads only that list, not the raw artifacts,
and writes a diagnostic issue body per finding. The cap (default 20)
keeps Pass 2 cost bounded regardless of codebase size.

Both passes run on Haiku. Diagnosis is prose, not code generation, so
the smaller model is sufficient. Earlier design used Sonnet for Pass 2
when the output was code stubs; the issue-only authority change
(2026-05-28) made the smaller model viable.

## Activity guard

Prevents redundant runs when no relevant code has changed. Queries the
most recently created sapper issue, derives an anchor timestamp from
`createdAt`, and runs `git log --since=$anchor` over non-excluded
paths. Empty output means skip.

The guard uses *sapper issues* as the anchor, not commits to the
repo's main branch, because the sapper is interested in code activity
relative to its own previous analysis.

## Exclude mechanism

`.bees/sapper-exclude` is a gitignore-style file at repo root.
Excludes gate three things: the activity guard's `git log` filter, the
paths passed to coverage tools, and the source files visible to Haiku
triage. Absence means no exclusions.

The bees repo ships `.bees/sapper-exclude` with `honeycomb/` excluded
because honeycomb content quality is the auditor drone's remit, not
the sapper's.

## Heuristic categories

Three classes of findings (full rules in the `heuristics` drawer):

1. **Coverage gaps** — code paths not exercised by any test.
2. **Assertion-weakness** — tests with negative-only, trivially-true,
   or bare-swallow assertions.
3. **Doc-file anti-patterns** — tests asserting string-literal
   presence in `.md` files, or line-count limits on `.md` content,
   without an explanatory comment ("if you must" rule).

## Dedup

Before filing each issue, the sapper searches open sapper issues for
the same target file/function. If found, skip. If the target has a
*closed* sapper issue, also skip — closing is an operator signal that
the finding was reviewed and accepted (or deferred). The sapper
respects that decision; a new run on the same finding doesn't reopen
it.

## Failure mode

Issue-only and single-tier: if `gh issue create` fails for one
finding, the diagnosis is captured to `$GITHUB_STEP_SUMMARY` and the
workflow continues to the next finding. Partial filing is acceptable.
The operator re-triggers via `workflow_dispatch` to retry unfiled
findings.
