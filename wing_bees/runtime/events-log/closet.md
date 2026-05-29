<!-- events-log.md: migrated from arch-events-log.md.

Hall: hall_architecture
tools: [bees-status, bees-dash]
-->

`~/.bees/events.log` is JSONL, one record per line. Core fields: `ts`, `feature` (slug), `stage` (plan/spec/dispatch/ship/status/retro/debug), `outcome` (success/failure/timeout/started), `model`, `duration_ms`, `repo` (absolute path). Plan, spec, and dispatch records carry `tokens_in`, `tokens_out`, `cache_read`, `cache_write`, `cost_usd` for cloud paths; local builders uncaptured. Consumed by `bees status` and `bees dash`. Optional: `source` (provenance; e.g. `operator-repair`).
