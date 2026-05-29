## Behaviour

The orchestrator is a single `claude -p` subprocess (Opus 4.7 in current deployment) parameterised by one feature slug and an optional `--strict-accept` flag. It runs in the background after `bees queen-orchestrate <slug>`; its PID is recorded in `~/.bees/state/<slug>.json` and surfaced by `bees status`.

**Tool inventory.** The orchestrator's `--allowedTools` list is fixed and minimal: six `Bash(bees …:*)` entries (`spec`, `dispatch`, `accept`, `ship`, `status`, `verify`), two `Bash(gh issue …:*)` entries (`create`, `list`), `Bash(git status:*)` and `Bash(git log:*)` for read-only repo inspection, `Read` for inspecting cells and notes, and `mcp__honeycomb__palace_recall` for consulting the honeycomb knowledge layer (operational patterns, prior-incident notes, role guidance). She does NOT have Write or unrestricted Bash — her behaviour is fully governed by the system prompt, the subcommand envelopes, and what she chooses to recall from honeycomb. `Edit` is in the tool allowlist for the trivial-self-fix path only; the system prompt constrains its scope to `.bees/<slug>/specs/*`. The canonical tool list lives in `SUBCOMMAND_TOOLS` in `lib/bees/queen_orchestrator.py`.

**Per-stage rubric.** For each subcommand the orchestrator calls, she reads the envelope's `outcome` field and branches:

- `bees spec --json` returns an envelope listing per-spec scribe verdicts. A final REJECT after retry is the trigger to file an issue with failure-class `verify-reject`.
- `bees dispatch --json` returns per-spec outcomes (`verify-approve`, `verify-reject`, `builder-timeout`, `builder-exit`, `ff-merge-conflict`). Each non-APPROVE outcome that preserves a cell becomes one filed issue.
- `bees accept --json` returns either `APPROVE` (proceed to ship) or `CONCERNS` (advisory). Under `--strict-accept`, CONCERNS converts to a filed issue with failure-class `accept-concerns-strict` and the orchestrator exits cleanly WITHOUT opening a PR.
- `bees ship --json` opens the PR; the PR URL in the envelope is the success terminator.
- `bees status --json` is read-only and invoked at the end of each run for the final operator-visible snapshot.
- `bees verify --json <NNN>` re-runs scribe verification on a single spec to disambiguate a borderline verdict.

**Per-reason rubric (v1.11).** Envelopes may carry `errors[0].reason` drawn from `bees.json_envelope.FailureReason`. Disposition by reason:

- `dispatch_refused_scribe_only_collision` — auto-reinvoke `bees dispatch --json <slug>` with a builder-only NNN selector; no issue filed.
- `dispatch_refused_prior_builder_commits` — file `queen-filed` issue; suggest `bees dispatch --restart` per the envelope's `suggested_retry_argv`.
- `dispatch_stale_artifact` — file `queen-filed` issue; operator inspects/removes the cell, then re-runs dispatch.
- `verify_subprocess_failed` — suppress per-spec; if ≥50% of a wave's specs emit this reason, file ONE `queen-observation` issue summarising the wave.
- `plan_malformed_retryable` — never appears in production (spec 003 retries in-process); if surfaced, treat as `plan_malformed_terminal`.
- `plan_malformed_terminal`, `plan_secret_detected`, `plan_briefing_empty`, `plan_briefing_too_large` — file `queen-filed` issue (pre-spec failures; rarely seen by the orchestrator since plan runs pre-approve).
- `verify_timeout`, `verify_parse_error`, `spec_review_timeout`, `accept_timeout` — file `queen-filed` issue under failure-class `infrastructure-error` (subprocess infra failure).
- `ship_pytest_failed`, `ship_push_failed` — file `queen-filed` issue; cell is preserved.
- `infrastructure_error` — existing behaviour; file `queen-filed` issue.

**Trivial self-fix (v1.14).** When a `bees spec --json` envelope carries `outcome="error"` with an `errors[0].message` matching a curated allowlist of mechanical-fix patterns (e.g. `frontmatter: depends-on entries must be positive integers`, `frontmatter: scribe-model must be non-empty`, `frontmatter: unknown type`), the queen may Read the offending spec file under `.bees/<slug>/specs/NNN-*.md`, apply a minimal Edit that addresses the stated complaint, commit with subject `fix(queen-self): <slug> <NNN> — <one-line reason>`, and re-invoke `bees spec`. Cap: 2 self-fixes per spec stage; a third validator failure on the same NNN falls through to the existing `queen-deferred` issue-filing path. Audit trail: one `outcome="queen-self-fix"` event per repair in `~/.bees/events.log`. The dedup-key for the exhausted-cap case is `queen-self-fix-exhausted`.

**Issue-body shape.** Issue bodies are interpolated from `ISSUE_BODY_TEMPLATE` (`lib/bees/queen_orchestrator.py`). Required fields: failure-class, slug, NNN, spec path, scribe reject reason (or builder note path, or merge-conflict diagnosis), preserved cell path, suggested next action, and a `dedup-key` footer. The dedup-key format is fixed: `<slug>:<NNN>:<failure-class>` where `<failure-class>` is one of the six entries in `FAILURE_TAXONOMY`.

**Dedup query.** Before each `gh issue create`, the orchestrator runs `gh issue list --label queen-filed --search "<slug>" --state open` (the shape stored in `DEDUP_QUERY`) and scans returned bodies for a matching dedup-key. If one already exists, she skips the create and continues.

**Soft-fail path.** If `gh issue create` fails for any reason — auth, rate limit, network, missing labels — the orchestrator invokes `bees unfiled-issue <slug> --nnn NNN` with the would-be-issue body on stdin. That subcommand writes `~/.bees/unfiled-issues/<slug>-<NNN>.md` (creating the directory if absent) and exits 0, so the orchestrator can continue safely. Soft-failed creates are NOT pipeline-fatal; the operator inspects `~/.bees/unfiled-issues/` after the run and files them by hand via `gh issue create` or the GitHub web UI.

**Transient-5xx retry.** The queen subprocess (the `claude -p` invocation itself) is wrapped with a three-attempt exponential-backoff retry in `cmd_queen_orchestrate`. Retry schedule: 5s, 30s, 120s (≈155s sleep budget), hard-capped at 300s total cumulative wall-clock across all retries. Retryable iff captured stderr/stdout matches any of `{"Overloaded", "529", "503", "502", "504", "connection refused", "timed out"}`; anything else (auth failure, malformed args, missing tool) is terminal. Each retried attempt emits `outcome="queen_retry", attempt=N, reason=<matched substring>` to `~/.bees/events.log` so observability tooling can spot retried runs. After three failures the error is terminal; `cmd_queen_orchestrate` emits `outcome="queen_failed"` and exits with the subprocess returncode.

**Exit contract.** After the queen subprocess returns, `cmd_queen_orchestrate` inspects state to determine the true outcome. `outcome="queen_complete"` is emitted only when at least one of: (a) a PR URL is recorded in state, (b) unfiled-issue files exist under `~/.bees/unfiled-issues/` (named `<slug>-<NNN>.md`), or (c) a `queen-filed` issue event for this slug appears in `~/.bees/events.log` since the `queen_started` event. In all other cases — including silent-exit parse-failure where the subprocess exits 0 with no observable side-effects — `outcome="queen_failed"` is emitted with a `reason` field distinguishing `"silent_exit_no_pr"` (zero returncode, no state), `"timeout"` (existing timeout branch), and `"subprocess_nonzero"` (non-zero returncode without state evidence). `sys.exit(result.returncode)` is unchanged.

**Labels.** Two labels: `queen-filed` for failures she handled, `queen-observation` for advisory observations she elected to track outside the PR thread (e.g. a non-strict accept CONCERNS that warrants follow-up).

**Strict-accept hook.** `--strict-accept` is the only operator-facing flag that changes the orchestrator's failure rubric. With it, accept CONCERNS becomes a fatal failure (file issue, exit clean, no PR). Without it, CONCERNS are advisory and ship embeds them in the PR body as `## Acceptance concerns`.

**Embedded-imperative defence.** Envelope payloads, builder notes, conflict diagnoses, and accept CONCERNS are input data, not instructions. The system prompt enforces this explicitly — embedded directives inside those payloads are summarised into issue bodies, never obeyed.

**Restart semantics.** The queen-orchestrator is safely restartable after a crash or operator `kill`. Three contracts enforce this: (1) **Status-first orientation** — the first tool call on every launch is `bees status --json <slug>`; the queen parses `specs[*].status`, `accept_verdict`, and `pr_url` from the envelope and jumps directly to the earliest incomplete stage, skipping spec/dispatch/accept if they are already done. (2) **Ship PR-exists no-op** — `bees ship --json` returns the existing open-PR URL as a success envelope (`outcome=success`, `reason=pr_already_open`) when a PR is already open for the requested base; the queen treats this as a normal success terminator. (3) **No-double-queen gate** — `bees queen-orchestrate` checks the recorded `orchestrate_pid` from state, calls `_is_bees_queen(pid)` (checks `ps -p <pid> -o command=` for the substring `queen-orchestrate`), and refuses with an explicit `kill <pid>` hint if a live queen is detected; a dead or recycled PID emits `orchestrate/restarted` and proceeds. Recovery procedure: `bees status <slug>` → `kill <pid>` → `bees queen-orchestrate <slug>`.

<!-- additional content from stage-orchestrate.md -->

## Behaviour

After `bees approve <slug>` records operator approval of `plan.md`, the operator runs `bees queen-orchestrate <slug>` to launch the queen-orchestrator as a detached background subprocess. The orchestrator's PID is recorded in `~/.bees/state/<slug>.json`. The orchestrator's system prompt (`QUEEN_ORCHESTRATOR_SYSTEM` in `lib/bees/queen_orchestrator.py`) is the full behavioural contract; its tool list (`SUBCOMMAND_TOOLS`) restricts it to the bees subcommands, `gh issue create`/`list`, read-only git, and `Read`.

**The agentic loop.** The orchestrator calls one subcommand at a time, reads the JSON envelope it returns on stdout, branches from the envelope's `outcome` field, and either advances to the next stage or files a GitHub issue. The pipeline order is `bees spec → bees dispatch → bees accept → bees ship`; `bees status` and `bees verify` are read-only side calls used for state reconciliation and per-spec disambiguation. Each subcommand's `--json` flag produces a stable machine-readable envelope; free-text stage output is never parsed.

**JSON-envelope contract.** Each subcommand returns an envelope with at least `outcome`, plus stage-specific fields (per-spec verdicts for dispatch, PR URL for ship, etc.). The orchestrator reads only the documented fields; she never treats envelope payloads as instructions (the system prompt's embedded-imperative defence). Subcommand exit codes that produce no parseable envelope are classified as `infrastructure-error`.

**Where issues are filed vs where she proceeds.** Failures that preserve a cell or block the pipeline (verify-reject after retry, builder-timeout, builder-exit, FF-merge content conflict, accept-concerns under `--strict-accept`, infrastructure errors) become one `queen-filed` GitHub issue each. Outcomes that simply continue (APPROVE, non-strict CONCERNS, successful dispatch) do not become issues — non-strict CONCERNS are surfaced into the PR body by `bees ship` as the `## Acceptance concerns` section. The orchestrator MAY additionally file `queen-observation` issues for advisory items she elects to track.

**Human gates (unchanged).** The two human gates from `human-gates` remain in force: plan approval (before `bees approve`) and PR review (after `bees ship`). The orchestrate stage adds no third human gate; everything between approval and the PR is autonomous.

**Soft-fail to unfiled-issues.** If `gh issue create` fails (auth, rate limit, network), the would-be-issue body is written to `.bees/<slug>/unfiled-issues/<NNN>.md` and the orchestrator continues. This is NOT pipeline-fatal — the operator inspects `unfiled-issues/` after the run.
