## claude-haiku-4-5

### Closet

Faster and cheaper per unit; p50 is lower than Sonnet; historically smaller sample count for dispatch events. ETA bars for Haiku dispatch units reach zero sooner — a zero `eta_remaining_s` is more likely to precede actual completion than for Sonnet. Fall back to the plan's `augmented_hours` prior when the Haiku baseline has fewer than three samples.

### Drawer

Haiku dispatch durations feed `dispatch_duration_baselines` under the `claude-haiku-4-5` key. Because Haiku processes specs faster and at lower cost, its p50 is lower than Sonnet's — the progress bar fills faster and `eta_remaining_s` drops to zero sooner. When `n` is small (fewer than 3 samples), the p50 and p90 may not be representative; treat the plan's `augmented_hours * 3600` prior from `feature_eta` as a more stable fallback.

Haiku scribe runs also contribute to `spec_duration_baseline` (no per-model split at the spec tier). The same nearest-rank p90 formula applies.

When the dashboard renders an in-flight Haiku dispatch unit:
- `pct` and `eta_remaining_s` are computed identically to Sonnet but against the Haiku p50.
- `tail` fires when elapsed exceeds the Haiku p90 — a lower absolute threshold than Sonnet.
- If no Haiku dispatch baseline exists yet (`base = None`), `pct = None` and `eta_remaining_s = None`; the progress bar is hidden and the feature-level prior is the only estimate available.
