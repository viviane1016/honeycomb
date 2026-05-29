## Behaviour

Bees reads the plan and specs from disk, inventories cells and their status, queries the open PR via `gh`, polls CI status, and reports the ahead-count over the base branch. It also surfaces recent events from `~/.bees/events.log` filtered to this feature, showing token usage, cost, and stage transitions. The full feature state is visible without any new work being triggered.
