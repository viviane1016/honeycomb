## Guidance

**Scribe tier rubric.** The queen should tag each work-breakdown item with the appropriate scribe tier:

- **`claude-haiku-4-5`** — mechanical work: docs-update, backlog-sweep, release-ceremony, content seeding, single-file find-and-replace. Use `[scribe:claude-haiku-4-5, <builder>]`.
- **`claude-sonnet-4-6`** — moderate implementation specs with bounded scope where Opus-grade reasoning is overkill but Haiku would be thin. Use `[scribe:claude-sonnet-4-6, <builder>]`.
- **`claude-opus-4-7`** (default) — architecture-heavy work, parsers/regex, security-relevant specs, or units introducing ≥5 new public symbols. Bare `[<builder>]` tag resolves here.

**Conventional Commits format.** The `## Commit message` section should follow this structure:

```
<type>(<scope>): <description>

<why this change is needed>
<what tradeoffs were considered>

Refs: <spec file path>
```

Type ∈ {feat, fix, refactor, docs, test, chore, build, ci, perf, style, revert}. Description in imperative mood, ≤72 chars. The body explains *why*, not *what*. Footer references the spec file for traceability.

**Failing test section.** Write this as a reviewer would verify it: concrete test cases, command-line invocations, or before/after comparisons. A good failing test lets a reviewer understand success without reading the entire diff. This section directly feeds the PR body's test plan.

**File footprints and parallel-builder safety.** Each spec should imply a clear primary file footprint — note in `## Scope` which files the builder writes or edits. Two specs in the same wave that touch the same file must serialise via `depends-on: [NNN]` in the dependent spec's frontmatter, or one of them must move to a different wave. When the work could plausibly land in either a new module or as an extension to an existing file, prefer the new focused file: builders work in parallel more safely on disjoint paths, and small files keep future scribe and builder context windows lean. Extending an existing file >500 lines should be a deliberate, called-out decision.
