<!--
Hall: hall_architecture
Scout: 2026-05-28T00:00:00Z
-->

The sapper drone runs daily on a GitHub Actions cron and files one
issue per finding labelled `sapper`. Detects coverage gaps,
assertion-weak tests (negative-only, trivially-true, bare-swallow),
and doc-file anti-patterns (string-literal presence in `.md`,
line-count limits on `.md`). Two-pass LLM: Haiku triage → diagnosis,
top-20 finding cap. Single-tier issue-only authority; no PRs, no
direct commits. Each finding contains diagnostic prose, not runnable
code stubs.
