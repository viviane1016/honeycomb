## claude-sonnet-4-6

### Closet

Primary dispatch tier and largest sample pool. Sonnet-tagged dispatch events feed `dispatch_duration_baselines`; Sonnet scribe runs feed `spec_duration_baseline`. Baselines are most reliable here. ETA bars and `eta_remaining_s` values for Sonnet units are the best-calibrated estimates the dashboard can produce.

### Drawer

**Dispatch baseline (per-model) — `lib/dash.py:449`**

`dispatch_duration_baselines(events)` accepts the full global event log (not a single feature's slice) so that p50/p90 are grounded across all features. It filters to `stage=dispatch, outcome=success` records with a valid `duration_ms` int and non-empty `model` string, converts to seconds (`duration_ms / 1000.0`), groups by `model`, and returns:

```
{model: {"p50_s": statistics.median(sorted_durations), "p90_s": sorted_durations[p90_idx], "n": count}}
```

Nearest-rank p90 formula: `p90_idx = max(0, min(n-1, int(round(0.9*(n-1)))))` — falls back to the max for small n. Models with few samples are still included so callers can decide whether to trust them.

**Spec baseline (model-agnostic) — `lib/dash.py:485`**

`spec_duration_baseline(events)` filters to `stage=spec, outcome=success` records that carry a `"scribe"` field. The `"scribe"` field distinguishes per-scribe records from the aggregate `spec` event written after queen review (which has no `scribe` field and would inflate the baseline by summing all scribes' work). Returns `{"p50_s": ..., "p90_s": ..., "n": ...}` or `None` when no samples exist.

No per-model split — the spec-stage baseline is global across all model tiers.

**Progress formula — `lib/dash.py:553`**

`annotate_inflight(units, dispatch_baselines, spec_baseline, now)` computes for each in-flight unit:

- `elapsed_s = max(0.0, (now - started_ts).total_seconds())`
- For dispatch units: `base = dispatch_baselines[unit["model"]]`; for spec units: `base = spec_baseline`.
- `pct = min(1.0, elapsed_s / p50_s)` — capped at 1.0; bar cannot overflow past p50.
- `eta_remaining_s = max(0.0, p50_s - elapsed_s)` — reaches zero before the unit completes when the unit takes longer than the median; zero means "past the median estimate", not "finished".
- `tail = elapsed_s > p90_s` — True when the unit is in the slowest-decile bucket.
- Bar colour: amber when `pct` is near or at 1.0; red when `tail` is True.

**Feature-level prior — `lib/dash.py:585`**

`feature_eta(events, plan_estimates, now)` uses `prior_s = plan_estimates["augmented_hours"] * 3600.0` as the phase-0 estimate before per-feature dispatch data accumulates. `over_s > 0` when elapsed wall-clock already exceeds the prior.

### Plan estimate calibration (empirical)

**Observed bias (n=4, 2026-04-26 to 2026-05-08):** Actual augmented wall-clock time (plan-draft → PR-open) averaged approximately 50% of the plan mid-point estimate for same-day features. The gap is largest for small features (release-ceremony: 0.2x; dash-oversight: 0.46x) and closes as feature size grows (honeycomb-0-2: 0.88–1.31x within range). The planning prompt's fixed-overhead assumption appears generous: the queen's model for per-feature setup cost (plan review, spec generation, ship steps) runs high relative to observed timing.

**Implication for phase-0 ETA:** `feature_eta` uses `plan_estimates["augmented_hours"] * 3600` as the prior before per-feature dispatch data accumulates. With a 2x systematic overestimate, the ETA bar will signal "over budget" (positive `over_s`) while the feature is still proceeding normally. Operators should treat phase-0 ETA bars with appropriate skepticism; the bar becomes reliable once several per-unit dispatch events have accumulated.

**Recommended calibration (pending more data):** Apply a 0.6x scaling factor to `augmented_hours` for the phase-0 prior until `bk-delivery-timings` lands per-stage latency data that enables a model-specific calibration. This narrows false-positive over-budget signals without materially underestimating large features (where the ratio approaches 1.0 anyway).

Sample size caveat: n=4 same-day features is a slow signal. The calibration factor should be revisited once `bk-delivery-timings` (per-stage latency tracking, currently in BACKLOG) provides richer per-stage data. The retro drone surfaces updated evidence on subsequent runs (see issue tracker for `retro-drone:` titles).

Provenance: applied from retro-drone petition #190, accepted 2026-05-25.
