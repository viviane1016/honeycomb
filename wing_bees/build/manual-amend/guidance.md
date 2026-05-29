## Guidance

**Amend vs re-dispatch.** Prefer re-dispatch via bees when the builder note (`.bees-builder-note.md`) reveals a fixable spec problem — update the spec and re-dispatch. Reserve manual implementation + amend for cases where the spec itself is fundamentally correct but the builder cannot resolve an ancillary issue such as a pre-existing test fixture conflict that requires operator judgment.

**After manual implementation.** Run `bees mark-patched <slug> <NNN> [--note "…"]` to record a `dispatch/manual` event in `~/.bees/events.log`. This keeps the dashboard and `bees status` output consistent with the actual state of the feature branch.
