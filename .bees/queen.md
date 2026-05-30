# Queen file — <project>

## Project context

This file is per-project memory for the bees workflow. Its contents are
injected into the queen (plan), queen (review), and scribe (spec)
subprocess prompts under a `## Project context (queen file)` heading,
and take precedence over generic honeycomb guidance when the two
conflict. Edit it freely: capture architectural decisions, recurring
patterns, prior failure modes, project-local conventions, and
model-selection notes (`.bees/queen.md > wing_models/role-* > default`).
