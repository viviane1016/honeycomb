<!-- long-polling-antipattern.md: migrated from antipattern-long-polling-as-feature.md.

Hall: hall_antipattern
tools: [polling, sse, websockets]
-->

Long polling is a workaround, not a design. When you reach for polling (client asking "status?" every N seconds), ask whether SSE (Server-Sent Events), WebSockets, or native push (e.g. platform notifications) is the right tool. Bees switched from polling to SSE in the dashboard: polled the mtime of `~/.bees/events.log` every 5 seconds (wasted cache, tied up server threads), then replaced it with `/api/events/stream` (SSE, one connection per client, event-driven updates, zero polling overhead).
