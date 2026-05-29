## Scribe-reuses-queen-trace optimisation

After the queen completes the plan stage, her `palace_recall` queries are logged to `honeycomb-trace.md`. Scribes run after the queen and inherit this trace as context via the always-injected prompt.

Scribes may skip recalling rooms the queen already retrieved for shared concerns. They may still call `palace_recall` when their assigned work-breakdown item needs context the queen did not query — for example, a specialised antipattern room relevant only to a domain-specific spec. The queen's trace is informational, not prescriptive; scribes exercise their own judgment about what additional rooms to fetch.
