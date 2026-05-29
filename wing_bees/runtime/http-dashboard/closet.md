<!-- http-dashboard.md: migrated from arch-dashboard.md.

Hall: hall_architecture
-->

`bees dash` serves an HTTP dashboard at `127.0.0.1:7475` (localhost-only, no auth). Autospawns on `plan`/`spec`/`dispatch`. Read-only window onto `~/.bees/events.log` — never writes events. Routes: `/` (feature list, cost rollups), `/feature/<slug>` (timeline, per-spec status, ETA bars, artifact links), per-feature `plan`/`briefing`/`log`/`trace`/`spec/<NNN>`, `/events`, `/events.log/raw`, `/api/events/stream` (SSE).
