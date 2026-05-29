## local:qwen-3.5-35b-a3b

### Closet

Local builder; `duration_ms` may not be captured for local dispatches (CLAUDE.md: "local builders remain uncaptured"). Baseline is likely absent or thin (`n < 3`). Fall back to the plan's `augmented_hours` prior. Do not route to Qwen without a queen.md petition authorising it.

### Drawer

Local builder events may omit `duration_ms` or `model` entirely (the bees CLAUDE.md notes local builders are uncaptured for token and cost telemetry). As a result, `dispatch_duration_baselines` will either produce no entry for `local:qwen-3.5-35b-a3b` or an entry with very low `n`.

When the dashboard encounters an in-flight Qwen dispatch unit:
- `dispatch_baselines.get("local:qwen-3.5-35b-a3b")` returns `None` if no samples exist.
- `annotate_inflight` sets `pct = None` and `eta_remaining_s = None`; the progress bar is hidden.
- The feature-level prior from `feature_eta` (`plan_estimates["augmented_hours"] * 3600`) is the only estimate available.

Until Qwen dispatch events reliably carry `duration_ms`, do not treat a missing Qwen baseline as a data gap to be filled by Sonnet values. Use the plan prior directly. A queen.md petition authorising Qwen routing must document the expected duration regime if ETA accuracy matters.

**Phase roadmap:**
- Phase 0 (shipped): priors from plan estimate + global p50/p90 baselines; no runtime calibration write-back.
- Phase 1 (per-stage refinement) and Phase 2 (queen-learning calibration) are tracked in BACKLOG.
