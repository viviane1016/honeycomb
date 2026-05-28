# sapper — Readme

The sapper drone is a daily autonomous test-quality diagnostic. It runs
on a weekday cron, looks at non-excluded source code for gaps and
weaknesses, and files GitHub issues describing what it found.

## What it actually does

1. **Activity guard** — skips if no commits to non-excluded paths since
   the last sapper issue was filed.
2. **Coverage measurement** — runs the project's test suite with
   coverage tooling appropriate to the languages present (pytest for
   Python, lcov for C, etc.).
3. **Haiku triage** — cheap LLM pass identifying coverage gaps,
   assertion-weak tests, and doc-file anti-patterns. Caps at 20
   findings.
4. **Haiku diagnosis** — writes a clear prose description per finding:
   what's missing or weak, why it matters, what a good fix would look
   like.
5. **Issue filing** — one GitHub issue per finding, labelled `sapper`.
   Existing open issues for the same target are skipped (dedup);
   closed issues are not re-opened (operator agency preserved).

## What it does not do

- It does not write code. The output is diagnosis, not stubs.
- It does not open PRs.
- It does not modify code or honeycomb content.
- It does not propose changes to honeycomb content (that's the
  auditor drone's remit, deferred to BACKLOG).

## Why issue-only

Issues are lower friction to triage than PRs. Each finding gets its
own lifecycle — assignable, prioritisable, closeable independently. A
PR bundles findings together and couples their resolution; issues
decouple them. Diagnosis is also more durable than a code stub: a
stub goes stale as the surrounding code changes, while a clear
description of what is missing remains useful even after evolution.

## See also

- `wing_antipatterns/test/md-string-literals` — anti-pattern the
  sapper flags.
- `wing_antipatterns/test/md-line-counts` — anti-pattern the sapper
  flags.
- `wing_bees/test/verify` — different testing-related closet in the
  same room.
