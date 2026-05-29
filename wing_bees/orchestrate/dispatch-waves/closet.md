<!-- dispatch-waves.md: migrated from stage-dispatch.md.

Hall: hall_procedure
models: [builder-selection]
-->

Specs may declare `depends-on: [NNN, ...]` frontmatter. Bees constructs a DAG via `_build_dispatch_graph` and dispatches wave-by-wave. Within a wave, builders run in parallel in isolated cells. Each builder produces one logical change with no squashing. Between waves, all must commit and FF-merge successfully. On FF-merge failure, the queen diagnoses; the operator resolves.
