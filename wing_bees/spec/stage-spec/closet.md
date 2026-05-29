<!-- stage-spec.md: migrated from stage-spec.md.

Hall: hall_procedure
models: [claude-haiku-4-5, claude-sonnet-4-6, claude-opus-4-7]
-->

The spec stage fans out N parallel scribes (one per work-breakdown unit); each scribe's model is resolved per-unit via `cli_override > [scribe:<m>] tag > default (Opus)`. Scribes assign per-spec file footprints and use `depends-on:` when wave-mates share files. A single queen-review pass runs over all drafts; the queen emits per-NNN APPROVE or REWRITE blocks and all spec files are written atomically. Parallelism: `BEES_SPEC_PARALLEL` (default 4) / `--parallel N`.
