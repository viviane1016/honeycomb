## The six halls

### hall_architecture — "what is X and how does it work"

Descriptive structural knowledge. Rooms here describe how the system is built, what its components are, and what each actor's nature is.

- `arch-*` rooms: `arch-cells`, `arch-dashboard`, `arch-events-log`, `arch-ff-merge`, `arch-honeycomb`, `arch-locking`, `arch-palace-recall`, `arch-queen-file`, `arch-secret-scan`, `arch-halls` (this room).
- `role-*` rooms: `role-queen`, `role-queen-orchestrator`, `role-scribe`, `role-builder`, `role-drone`, `role-drone-cartographer`, `role-drone-scout`.
- `dependency-graph` — explains how dispatch dependencies are derived.

### hall_protocol — "what's the format / contract for Y"

Formal contracts, templates, and conventions between actors or between stages. Rooms here define interfaces, not behaviour.

- `*-template`, `*-format`, `*-conventions` files: `briefing-template`, `pr-body-template`, `petitions-format`, `proposed-actions-format`, `backlog-conventions`, `default-conventions`.
- Cross-cutting protocol docs: `scout-headers`, `slug-naming`, `classifier-prompt`, `human-gates`, `doc-update-contract`, `adr-format`, `conventional-commits`.

### hall_procedure — "how do I do Z, step by step"

Operational checklists and recipes. Rooms here are action-oriented — they describe steps to take, not facts to know.

- `stage-*` rooms: `stage-plan`, `stage-spec`, `stage-dispatch`, `stage-ship`, `stage-verify`, `stage-status`, `stage-accept`, `stage-debug`, `stage-design`, `stage-retro`, `stage-orchestrate`.
- Recovery and maintenance recipes: `release-ceremony`, `bees-patch`, `rework-at-pr`, `queen-review`, `retry-incremental-repair`, `release-map`.

### hall_pattern — "what's the right way to handle W"

Generalisable engineering practices that apply across projects. Mostly populated by `wing_practices/`.

- `testing-discipline`, `secret-handling`, `observability`, `parallelism-safety`, `v-model`, `agentic-file-structure`.

### hall_antipattern — "what's a known bad pattern to avoid"

Cautionary practices. Same shape as `hall_pattern` but opposite polarity, and retrievable as its own slice.

- `antipattern-*` files: `antipattern-long-polling-as-feature`, `antipattern-plaintext-credentials`.

### hall_rubric — "X or Y — which should I pick"

Decision tables and lookup references. Rooms here help an actor choose between options or look up environmental facts.

- `wing_models/` rooms: model-tier guidance per role (`role-builder`, `role-scribe`) and calibration (`eta-progress-estimation`).
- `wing_tools/` rooms: tool reference (`gh-cli`, `git-workflow`, `python-packaging`, `claude-code-runtime`).
- Safety and runtime references: `prompt-safety-multi-stage`, `claude-code-runtime` (cross-wing).
