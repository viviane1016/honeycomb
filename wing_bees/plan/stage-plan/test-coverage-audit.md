## Test coverage audit

Before finalising the work breakdown, the queen audits how the planned changes interact with the existing test suite, and assigns the audit's output to the units that own the corresponding code.

1. **Identify tests that will break.** Reason about which existing tests in `tests/` assert specific content the planned changes will alter — hardcoded string literals, room-name lists, file-existence checks, always-injected closet strings. Name each breaking test explicitly in the plan and assign its update to the unit that makes the breaking change, not to a catch-all final unit. A spec that breaks a test without owning its repair is incomplete.

2. **Require acceptance tests for structural changes.** For any work unit that renames, moves, adds, or rewrites a honeycomb room: the unit's scope must include at least one `palace_recall` spot-check in `tests/test_honeycomb_content.py` asserting the affected room surfaces for its primary query term. The check ships with the structural change, not as deferred follow-up.

3. **Always-injected closet rewrites travel with their fixture updates.** For any work unit that rewrites the closet of an always-injected room (`stage-plan`, `stage-spec`, `role-queen`, `role-scribe`, `classifier-prompt`), the unit must also update the matching string assertion in `tests/test_honeycomb_content.py::test_compose_appended_prompt_*`. The injection contract is verified by literal substring assertions; closet edits and fixture edits are one atomic change.

The pattern generalises: whenever honeycomb itself is the subject of a bees feature, the queen treats the test suite as a first-class artifact alongside the rooms themselves.
