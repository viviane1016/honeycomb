## Status: DEFERRED

This stage/feature is not yet implemented in bees. Content is preserved here for future reference.

Reflective queen call when a feature goes sideways mid-pipeline. The queen analyzes what failed and emits a proposed-actions list: small inline fixes (a typo, a config tweak), backlog items, queen-file or petition updates, GitHub issues to file, or — for problems larger than debug should attempt — an escalate-to-plan action that hands off to a fresh plan stage with the debug report as briefing. This stage description covers the design for honeycomb consumption; the bees CLI does not yet implement debug.
