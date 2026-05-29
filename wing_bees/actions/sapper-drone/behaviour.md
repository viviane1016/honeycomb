## Behaviour

Test-quality is a slow-moving signal — coverage gaps accumulate gradually as code grows faster than tests. Daily weekday batching keeps proposals timely enough to be useful alongside active development while avoiding the noise of per-commit triggering. The cron fires at 05:00 UTC so results are available at the start of the operator's workday; weekday-only reflects that test-quality proposals are most actionable when development is active.

Single-tier PR-only authority is correct because sapper outputs are entirely generative. A test stub is a proposal — it does not mutate idempotent state the way a BACKLOG cleanup does. Every proposed stub requires a reviewer to judge whether the gap is real, whether the proposed assertion is the strongest available, and whether the stub belongs in the named test file. The PR tier is the right container for that judgement; auto-merge would bypass it.

### Trigger

- `schedule: cron "0 5 * * 1-5"` — weekdays 05:00 UTC. Fires before the operator's workday; weekday-only because test-quality proposals are most useful alongside active development.
- `workflow_dispatch` — manual escape hatch, bypasses the activity guard entirely.

### Activity guard

The activity guard prevents redundant runs when no relevant code has changed since the last sapper PR.

1. Query the most recently created sapper PR (any state): `gh pr list --label sapper --limit 1 --json number,state,createdAt,mergedAt`.
2. If the result is empty (no prior sapper PR exists), proceed unconditionally — this is a first-ever run.
3. Derive `anchor`: if the PR state is `MERGED`, use `mergedAt`; otherwise use `createdAt`.
4. Run `git log --since=$anchor --name-only -- <non-excluded-paths>`. If the output is empty, write a `no activity since $anchor` notice to `$GITHUB_STEP_SUMMARY` and exit 0. If non-empty, proceed.
5. A commit that touches only `honeycomb/**` (or other excluded paths) will produce an empty `git log` and correctly skip the run in the bees repo. `workflow_dispatch` bypasses this guard entirely.

### Exclude-file mechanism

`.bees/sapper-exclude` is a gitignore-style file (one path or glob per line, `#` comments allowed, blank lines OK) loaded from the repo root before the activity guard and coverage steps. Absence means no exclusions.

The exclude list gates three things: (a) the `git log` path filter in the activity guard, (b) the paths passed to coverage tools, and (c) the source files visible to the Haiku triage pass.

The bees repo ships `.bees/sapper-exclude` with `honeycomb/` excluded because honeycomb-content quality is the auditor drone's remit, not the sapper's.

### Inputs

All inputs are read-only:

- Non-excluded source files, as determined by the exclude-file mechanism.
- Coverage artifacts written to `/tmp/sapper/` by the language-detection step.
- `.bees/sapper-exclude` if present.
- Prior sapper PRs, via `gh pr list --label sapper`.
- Honeycomb rooms — read directly via the `Read` tool (no MCP in the runner).

### Language detection

| Language | Detection | Coverage tool | Output |
|---|---|---|---|
| Python | `*.py` present among non-excluded paths | `pip install pytest pytest-cov`, then `pytest --cov --cov-report=json` | `/tmp/sapper/python-cov.json` |
| C/C++ | `*.c` or `*.cpp` present | `apt-get install -y lcov`, then `gcov`/`lcov` | `/tmp/sapper/c-cov.info` |
| Fallback | No coverage tool available | Static pattern scan for uncovered branches (grep-based) | `/tmp/sapper/static-gaps.txt` |

Multiple languages may be detected in one run; all matching tools run. The fallback static path must be exercised (not skipped) when no coverage tool matches — this is important for polyglot or C-only repos where `pytest` is unavailable.

### Two-pass LLM

The two-pass design separates cheap triage from expensive proposal generation, keeping total cost bounded regardless of codebase size.

- **Haiku triage (Pass 1):** cheap, reads coverage artifacts and source files, identifies: (a) code paths not exercised by any test, (b) subprocess callsites with no integration test, (c) assertion-weak test functions (see § Assertion-weakness heuristics). Produces a prioritised gap list capped at 20 items, written to `/tmp/sapper/gaps.md`. The cap keeps Pass 2 cost bounded — without it, a large codebase could surface hundreds of gaps and make Sonnet prohibitively expensive.
- **Sonnet proposal (Pass 2):** reads `/tmp/sapper/gaps.md` only (not the full coverage report), writes concrete test stubs for each gap. Cost is bounded because the input is the top-20 list, not the raw coverage artifacts.

The default cap is 20, declared in this room. A workflow input `max_gaps` (integer, default 20) may override it at dispatch time.

### Assertion-weakness heuristics

Haiku is asked to flag test functions exhibiting:

- **Negative-only assertions:** the body contains only `assertNotEqual`, `assertIsNot`, `assertNotIn`, `assert x not in`, or `assert x != y` — proving what did not happen but not what did.
- **Trivially-true checks:** `assert True`, `assert x is not None` with no further assertion, `assert len(x) > 0` with no structural check on contents.
- **Bare exception swallowing:** a `try/except` block inside a test with an empty `except` or `pass` body.

These are heuristics, not theorems. Some negative assertions are correctly the strongest available statement (e.g. asserting an exception is NOT raised under a specific condition). All proposals are advisory; the reviewer judges whether each stub is genuinely stronger. This is the reason sapper is PR-only.

### Honeycomb-content test-file exclusion

The following test files are included in coverage measurement (they exercise real code) but excluded from assertion-proposal generation — improving them requires honeycomb-domain knowledge that is the auditor drone's remit:

- `tests/test_honeycomb_content.py`
- `tests/test_hc_*.py`
- `tests/test_adr_format_room.py`

This exclusion list is encoded in this room (not hardcoded in the workflow YAML) so it can evolve via a honeycomb edit without a workflow deployment.

### Outputs

At most one PR per run:

- Title: `sapper: test-quality proposals (YYYY-MM-DD)`
- Label: `sapper`
- Body: structured sections grouping proposals by module → gap type (coverage gap / assertion weakness / missing integration test) → proposed stub. Each stub includes the target test file path and function signature.

If the activity guard fires (no commits since anchor): zero PRs; write `no activity since <anchor>` to `$GITHUB_STEP_SUMMARY`.

### Dedup

Before opening a new sapper PR:

1. List open PRs with the `sapper` label: `gh pr list --label sapper --state open`.
2. For each open prior sapper PR, post a comment of the exact form:

   > Superseded by #NEW (based on commit `<sha>`).
   > This PR was based on commit `<old-sha>`. If you want the most current analysis, review #NEW and close this one.

3. Prior PRs are not auto-closed. Operator agency is preserved, along with any in-flight review comments on the older PR.
4. The new PR is opened with the `sapper` label applied at creation time.

### Failure mode

The sapper drone is single-tier so only the PR-soft half of the failure-mode contract applies — there is no cleanup pass. If `gh pr create` fails (rate limit, transient GitHub outage, auth issue), the unfiled diff is captured to `$GITHUB_STEP_SUMMARY` and the workflow exits 0. The operator re-triggers via `workflow_dispatch` when the underlying issue is resolved. The workflow does not retry inline.
