<!-- prompt-injection-invariants.md: migrated from prompt-safety-multi-stage.md.

Hall: hall_rubric
languages: [python]
-->

Four invariants protect multi-stage workflows from prompt injection: (1) untrusted input (briefings, specs, builder notes) wrapped in boundary markers; (2) core instructions end-loaded after injected content to prevent override; (3) structured output in consistent fences for machine parsing and retry; (4) queen explicitly instructed that briefing is data, not commands.
