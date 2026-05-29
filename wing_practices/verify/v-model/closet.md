<!-- v-model.md: migrated from v-model.md.

Hall: hall_pattern
-->

The v-model pairs requirements descending (briefing → plan → spec → code) with verification ascending. The requirement-author-verifies principle: the role that authored a level verifies the implementation at that level, catching intent mismatches literal review would miss. In bees: queen accepts plan against briefing, scribe verifies builder's diff against spec, builder verifies code with tests. Human PR review remains the outermost gate.
