<!-- http-dashboard.md: migrated from arch-dashboard.md.

Hall: hall_architecture
-->

`bees dash` serves an HTTP dashboard at `127.0.0.1:7475` (localhost-only, no auth). Autospawns on `plan`/`spec`/`dispatch`. Primarily a read-only window onto `~/.bees/events.log`. When `BEES_BEEKEEPER=1`, brain-gated routes `/flags` and `/queue` surface beekeeper state with POST handlers for clear/approve/reject. Routes: `/` (feature list, cost rollups), `/feature/<slug>` (timeline, per-spec status, ETA bars, artifact links), per-feature `plan`/`briefing`/`log`/`trace`/`spec/<NNN>`, `/events`, `/api/events/stream` (SSE), brain-gated `/flags` and `/queue`.
