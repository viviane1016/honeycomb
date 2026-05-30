## Behaviour

**Server topology.** Single-threaded HTTP server bound to `127.0.0.1:7475`. No authentication, no remote bind — the security model is "your machine, your dashboard." Stop with `kill $(cat ~/.bees/dash.pid)` or by re-running `bees dash` to bounce. PID is recorded at `~/.bees/dash.pid`; `tools/install.sh` bounces a running dashboard so it picks up new code on upgrade.

**Autospawn.** `_ensure_dash_running` (in `lib/events.py`) is called at the entry of `cmd_plan`, `cmd_spec`, and `cmd_dispatch`. Read-only stages (`status`, `ship`, `retro`) deliberately don't autospawn. Disable with `BEES_DASH_AUTOSPAWN=0`; CI uses this.

**Routes.**

| Route | Purpose |
|---|---|
| `/` | Feature list grouped by repo (collapsible `<details>` per repo, state persists via localStorage). Per-repo subtotals; global footer "Across N features in M repos: spent $X, saved $Y vs Opus-always." Active features (started ≤30 min ago with no terminal event) pinned at top. Local-vs-cloud builder split rendered as SVG bars; first-attempt success rates per repo for scribe and builder stages. Version footer (installed snapshot or dev HEAD). Feature buckets whose every event has `stage="release"` (e.g. `bees release v1.15`) are excluded from the shipped-features table; they remain visible on `/events`. The dispatched-specs fraction also counts `stage=spec, mode=scribe-only, outcome=success` events so scribe-only units appear as delivered. |
| `/feature/<slug>` | Per-feature page. Summary card; grouped artifact links (plan/briefing/log/trace in one row, specs in a second, events log + PR in a utility row). Per-spec status section showing each spec's state. Timeline table collapsed behind `<details>` (fold state persists via localStorage). **Phase-0 ETA section** above the timeline whenever the feature has in-flight work or a plan estimate. **Compact wave-progress table** (`Wave | Status | Specs`) above the timeline whenever dispatch wave events exist for the active run; foundational marker appended to Opus specs in mixed-model waves. |
| `/feature/<slug>/plan` | Renders `.bees/<slug>/plan.md` as `<pre>`-block HTML (escaped). |
| `/feature/<slug>/briefing` | Renders `.bees/<slug>/briefing.md`. |
| `/feature/<slug>/log` | Renders `.bees/<slug>/log.md`. |
| `/feature/<slug>/trace` | Renders `.bees/<slug>/honeycomb-trace.md`. |
| `/feature/<slug>/spec/<NNN>` | Renders `.bees/<slug>/specs/NNN-*.md`. Slug validated by `_SLUG_RE`; NNN by `^\d{3}$`. |
| `/feature/<slug>/accept` | Renders `.bees/<slug>/accept.md` if present (queen-accept concerns). |
| `/feature/<slug>/verify/<NNN>/<attempt>` | Renders the verify sidecar at `.bees/<slug>/verify/NNN-attempt-<attempt>.md`. Attempt is optional and defaults to latest. |
| `/feature/<slug>/orchestrate-log` | Serves the tail (last 65 KB) of `~/.bees/orchestrate/<slug>.log`, HTML-escaped inside `<pre>`. Injects `<meta http-equiv="refresh" content="5">` while the orchestrator process is running; static otherwise. Returns styled 404 when the file is absent. An "orchestrate-log" link appears in the artifact row whenever the file exists. |
| `/api/state/<slug>` | JSON read-only feature-state snapshot (same projection used by `bees status --json`). Implemented since v1.x; this is the first documentation of the route. |
| `/events` | Recent events table (tail of `~/.bees/events.log`). |
| `/events.log/raw` | Serves the log as `text/plain`, capped at 65 KB. |
| `/api/events?feature=<slug>` | JSONL for the slug. |
| `/api/events/stream` | Server-Sent Events; emits `update` events at ~10s cadence whenever `events.log` mtime advances. Both HTML pages auto-reload on `update`. |
| `/flags` | Flags index. One row per entry in `~/.beekeeper/flags.json`, sorted by `raised_at` descending. Supports `?slug=<>&class=<>` to render a per-flag detail view assembling: primary action callout, events tail filtered to the slug (last 50 lines), `.bees/<slug>/accept.md` if present, decisions tail filtered to the slug, and a clear-flag `<form>`. Gated on `BEES_BEEKEEPER=1` or `~/.beekeeper/config.json` `enabled: true`; returns 404 when the brain is disabled. |
| `POST /flags/clear` | Validates `slug`, calls `flags.clear_flag(slug)`, appends a `cleared_at` line to `~/.beekeeper/decisions.log`, resets the per-slug entries in `~/.beekeeper/attempts.json` (so the brain's retry counter starts fresh on the next tick), and `302`-redirects to `/flags`. |
| `/queue` | Plan-approval queue. One row per `pending` or `approved` entry in `~/.bees/queue.json`, sorted priority-tagged first then FIFO by `enqueued_at`. Columns: slug, queen-emitted drift one-liner, queen-emitted briefing one-liner, view-plan link, approve/reject slider buttons. Gated on `BEES_BEEKEEPER=1` or `~/.beekeeper/config.json` `enabled: true`; returns 404 when the brain is disabled. |
| `/queue/<slug>/plan` | Server-side markdown render of the queued feature's `plan.md` (path from the queue entry's `plan_md_path` field). Opens in a new tab. Matches the per-feature artifact-render convention. |
| `POST /queue/<slug>/approve` and `POST /queue/<slug>/reject` | Flip the entry's `status` and atomically rewrite `~/.bees/queue.json` via `tempfile + os.replace`. Idempotent. Redirects to `/queue`. |
| (unknown) | Styled 404 with back-to-features link. |

**Repo resolution.** Per-feature artifact routes resolve the repo path from the latest event's `repo` field. Events also carry `cwd` (the runtime worktree root) only when it differs from `repo` — secondary-worktree runs (e.g. `.claude/worktrees/*`) resolve correctly because dashboard artifact lookups prefer `cwd` over `repo`. Pre-existing events without `cwd` fall back to `repo`.

**Per-spec status enum.** `pending`, `building`, `merged`, `failed`, `approved`, `rejected`. Shown on `/feature/<slug>` in the per-spec status section. A verify-verdict column displays: ✓ `approve`, ↺ `revised-and-re-running`, ✗ `rejected-final`, — `pending`.

**Accept badge.** The feature header renders an accept badge showing the latest `bees accept` verdict:
- **green APPROVE** when `outcome="success"`
- **amber CONCERNS (N)** when `outcome="concerns"` (N = concerns count), linking to `/feature/<slug>/accept`
- **red REJECT (N unmet)** when `outcome="rejected"` (N = unmet count from `## Unmet briefing items`), linking to `/feature/<slug>/accept`
- **amber "accept: error"** when `outcome="error"`, linking to `/feature/<slug>/accept` if the file exists
- **muted "not yet run"** when no accept event exists for the feature

**Warning band.** The per-feature page renders a warning callout above the "Approve & orchestrate" button when `bees ship` would be blocked. RED band (`bk-warning-band--reject`) when the latest accept event has `outcome="rejected"` — "Ship blocked: REJECT verdict. N unmet briefing items." AMBER band (`bk-warning-band--petitions`) when `.bees/<slug>/petitions/*.md` contains one or more `status: pending` files — "Ship blocked: N pending petition(s)." No band when neither condition holds.

**Wave events.** Dispatch emits `stage="dispatch_wave_started"` and `stage="dispatch_wave_completed"` records carrying `wave=N`, `specs=[NNN, …]`, and a per-wave `outcome` field: `success`, `partial` (some specs in the wave merged but at least one didn't), or `fail`. The completed event also carries `skipped=[NNN, …]` — specs not launched because their declared deps include a failed NNN. Per-spec dispatch records use `outcome="interrupted"` (SIGINT), `outcome="skipped"` with `reason="already_merged"` or `reason="failed_dep"`, and `outcome="failure"` with `fail_reason="unexpected exit"` (terminal-event fallback when a builder dies without emitting its own outcome).

**Filed issues panel.** `/feature/<slug>` renders a collapsible `<details>` panel below the accept badge showing issues filed by the queen during the run. `queen-deferred` issues (ship-blocker semantics per v1.13 label split #232) are listed in amber with a ⛔ prefix; `queen-diagnostic` issues (advisory, non-blocking) are listed in muted text. Each row links to the GitHub issue URL returned by `gh issue list`. When `gh` is unavailable, times out, or returns malformed output, the panel shows "Filed issues unavailable (<reason>)" in muted text instead of hard-failing. Empty buckets render nothing so the default state stays quiet. The same two-bucket view is available via `bees status <slug>` in the CLI.

**Phase-0 ETA rendering.** `/feature/<slug>` renders an ETA section above the timeline when in-flight work or a plan estimate is present.
- **Feature-level rollup**: wall-clock elapsed (from `bees_delivery_hours`) vs. the plan's `augmented_hours`, tagged with the plan's confidence. An "over by N" line appears when elapsed exceeds the prior.
- **Per-in-flight-unit progress bars**: each in-flight dispatch or parallel-spec scribe gets its own bar baselined against the global p50 for its model tier (`dispatch_duration_baselines` / `spec_duration_baseline`, computed across the whole events log). Bars turn amber past p50, red past p90.
- **Longest pole**: the unit with the greatest expected remaining time is marked. The same progress bar appears in the Progress column of the in-flight `started` row in the timeline table.
- Pre-feature plans lacking a `## Delivery estimates` section render "estimates unavailable" — no breakage.

**Beekeeper status strip.** When the daemon is running with `BEES_BEEKEEPER=1`, every dashboard route (`/`, `/feature/<slug>`, `/consumers`, `/flags`) renders an always-visible status strip below the `dash-nav` paragraph showing five cells: mode (`disabled` / `degraded` / `Idle` / `Driving` / `Intervening` / `Flagged`), last decision summary (slug + action from the tail of `~/.beekeeper/decisions.log`), decisions-today count, flags-raised count (from `~/.beekeeper/flags.json`), budget remaining (`n/a (v1)` until Colony 5 lands the LLM-spawn). State is **read from disk on every render** — no in-memory coupling to the brain thread — so the strip survives daemon restart and renders correctly when the brain is disabled. When `BEES_BEEKEEPER` is unset or `=0`, no strip is rendered (the dashboard is byte-identical to colony 2). When the brain has crashed (presence of `~/.beekeeper/brain-crash.log` newer than the daemon's start mtime), the strip renders `degraded — restart daemon` and other cells are suppressed. The `flags: <N>` cell counts every entry in `flags.json`; `bees status` separately emits `flags: N raised (H high, L low)` when N > 0.

**Attention banner.** A red `.bk-flags-banner` is rendered above the status strip on every chrome route (`/`, `/consumers`, `/feature/<slug>`, `/flags`) whenever at least one currently-raised flag in `~/.beekeeper/flags.json` resolves to effective severity `high` (per `resolve_severity(flag_class, config)`). The banner persists until the flag is cleared and links to `/flags`. Low-severity flags contribute to the status-strip `flags:` count but do not raise the banner.

**Flag-class severity overrides.** Per-class severity defaults live in `lib/bees/beekeeper/notifier.py:DEFAULT_SEVERITIES`. Operators override via `~/.beekeeper/config.json` keys `flag_severities: {<class>: "high"|"low"}` and `notification_sound: "<name>"` (default `Glass`). The effective severity returned by `resolve_severity(class, config)` gates both the NotificationCenter ping and the dashboard attention banner contribution.

**Plan-approval queue.** `/queue` is the operator's surface for cross-feature scheduling: when `bees plan --queue` enqueues a plan instead of auto-approving, it lands in `~/.bees/queue.json` and surfaces on this page. The brain reads the same file on every tick and pops the head `approved` entry on its current colony's `completed` handler. The dashboard, brain, and `bees plan --queue` all coordinate through `lib/bees/queue.py`'s atomic write helpers (`tempfile + os.replace`); there is no in-memory coupling between the three call sites.

**Cost display.** The `/` view computes per-feature "Saved vs Opus" — the delta between actual model usage (cloud tokens × cloud rates) and a counterfactual Opus-everywhere baseline. Per-repo subtotals and a global footer aggregate across all repos. A `plan+spec only` caveat footnote appears when dispatch events lack usage data (legacy dispatches from before token capture, or local-builder dispatches not yet instrumented).

**Model attribution.** When the queen's `requested_model` differs from the actually-routed `model` (e.g., local-builder routing), the Model cell renders `requested → actual` instead of splitting into a separate column.

**Timestamps.** All visible timestamps on `/` and `/feature/<slug>` wrap in `<time datetime="…">…</time>` so client-side JS renders them as locale-formatted strings. The canonical UTC ISO is preserved as the `datetime` attribute. The timeline sort key for same-second events is the composite tuple `(ts, stage, spec|scribe)` for deterministic stage-then-spec order across reloads.

**Possibly-stuck marker.** Features with orphaned `started` events (no terminal event after them) are marked `● possibly stuck` on `/` and styled distinctly on `/feature/<slug>`. `stale` outcome rows get a separate style.

**SSE fallback.** Set request header `X-Bees-NoSSE: 1` to opt into `<meta http-equiv="refresh" content="10">` HTML refresh instead of SSE. Useful in environments that don't reliably hold long-lived HTTP connections.

**Events-fold persistence.** The `<details class="bk-events-details">` element on `/feature/<slug>` preserves its open/closed state via localStorage (key `bk-events-details:<slug>`). Toggling the events fold open persists across page reloads and SSE-triggered refreshes. This mirrors the repo-fold persistence already present on `/` (key prefix `bk-details:<repoKey>`).
