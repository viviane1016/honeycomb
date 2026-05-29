## Behaviour

The review runs as a fresh `claude -p` subprocess on Opus 4.7 with read-only tools (Read, Grep, Glob, palace_recall). She receives the approved plan, every draft spec body fenced for clarity, and the candidate wave structure computed via `_build_dispatch_graph` over the drafts. Her job is three-fold:

- **Per-spec quality**: clarity, completeness, builder-implementability of each draft.
- **Cross-spec consistency**: no two specs touching the same file in conflicting ways, shared symbols named consistently, ordering correct.
- **Dependency correctness**: for each spec, verify that its `depends-on:` declaration matches what its `## Scope` actually references. If a spec reads a file produced by spec NNN, it should list `depends-on: [NNN]`. If the declaration is wrong, emit a `<<<DEPS NNN>>>` block instead of REWRITE.

For every NNN in the input, she emits exactly one block:
- `<<<APPROVE NNN>>>...<<<END APPROVE>>>` — keep the draft as-is.
- `<<<REWRITE NNN-kebab-slug>>>...<<<END REWRITE>>>` — replace the full body (closet, behaviour, guidance, everything).
- `<<<DEPS NNN>>>...<<<END DEPS>>>` — frontmatter-only patch, containing only a single `depends-on:` line; the rest of the spec body is preserved.

Coverage failures (missing, surplus, duplicate blocks) are fatal. Markers must be flush-left, on their own lines.

The harness then applies DEPS patches to drafts (merging the frontmatter line with the draft body), re-validates each REWRITE body via `validate_spec_body` (required H2 sections, non-empty Builder prompt) and `scan_for_secrets`. APPROVE bodies pass through unchanged but are still secret-scanned defence-in-depth at the merge step.

**Absolute-path rejection.** `validate_spec_body` hard-rejects specs whose `## Builder prompt` or `## Scope` sections contain absolute paths (`/Users/`, `/home/`, `/root/`, or any leading `/` followed by a path segment). The validation error flows into the REWRITE pathway: the harness treats the draft as if the queen emitted a REWRITE and re-queues it with an instruction to replace absolute paths with relative equivalents. The REWRITE body is re-validated before acceptance. The dispatch-time warn-and-proceed path for absolute paths has been removed; enforcement is now exclusively at spec-stage.

**Depends-on inference pass.** Before the queen review runs, `_infer_depends_on_from_output_files` examines the `output-files` frontmatter of every draft. For each pair of specs sharing at least one file where neither already declares the other in `depends-on`, the spec with the larger NNN receives a programmatic DEPS patch adding the smaller NNN as a dependency (deterministic by-numeric-order tie-break). These patches flow through the same machinery as queen-emitted DEPS verdicts. A log line is emitted per inferred patch: `bees spec: inferred depends-on: NNN -> [MMM] from output-files overlap on <file>`. When a spec is missing `output-files` entirely but the overlap heuristic detects it shares files with another spec (mentions in `## Scope` section), spec-stage hard-fails with `bees spec: depends-on inference failed: spec NNN must declare output-files (or depends-on: [...]) before <other-NNN> can be ordered against it`. Operators add the missing frontmatter and rerun `bees spec`.

The review emits a `stage="spec_review"` event with `outcome` ∈ `started, success, error, timeout, parse_failure_final, secret_detected, rewrite_invalid` and (on success) `rewrite_count`.
