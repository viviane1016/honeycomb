## Guidance

The dashboard is read-only. It never writes to `events.log`; it never modifies feature artifacts. If a value on the page looks wrong, the source of truth is `~/.bees/events.log` and the per-feature `.bees/<slug>/` directory — fix those, the dashboard reflects the next refresh.

**Share the URL with the user** as soon as a long-running stage (spec, dispatch) starts. The keeper would rather watch their dashboard than poll you for updates. The per-feature URL is `http://127.0.0.1:7475/feature/<slug>` — link directly, don't make them navigate from `/`.

**Don't autospawn in CI**: set `BEES_DASH_AUTOSPAWN=0`. The dashboard would bind a port and persist past the run.

**Privacy posture**: the dashboard binds to `127.0.0.1` only, no auth. Don't tunnel it to a public endpoint without adding auth — events.log contains briefings, plans, and commit refs.
