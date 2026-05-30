# ADR-0002: Drawer overrides with scope-keyed semantic indexes

**Date:** 2026-05-30
**Status:** Proposed

## Context

ADR-0001 ("MCP-mediated queenfile and petitions") established that all
honeycomb access goes through a single recall API and that consumer-
local content lives in a structured overlay. The petition mechanism
ships content from a consumer to canon via an upstream PR.

In follow-on design work, two observations forced a deeper structural
move:

### Observation 1 — The petition file is structurally a drawer override

When a consumer's queen proposes amending `wing_bees/build/manual-amend/
behaviour.md`, what she is submitting is a **variant of an existing
drawer**, scoped to a particular context. It is not a new artifact
alongside the canonical content; it is the canonical content,
customized for that scope.

Naming pattern that falls out: `<drawer-name>.queenfile_<scope>.md`,
e.g. `behaviour.queenfile_bees-v1.18.md` or
`behaviour.queenfile_scarab.md`. Multiple consumers can each have
their own override on the same canonical drawer without collision.

### Observation 2 — Override naming unlocks tool-version decoupling

If overrides can target `tool == bees, tool_version == v1.18`, then
the same honeycomb release can carry content for multiple in-flight
tool versions. Specifically:

- Bees v1.17 runs in production reading `behaviour.md` (canonical).
- Bees v1.18 development reads `behaviour.queenfile_bees-v1.18.md`
  (override), which lives in honeycomb canon as a shipped drawer.
- When bees v1.18 stabilizes, the override gets promoted to canonical
  (rename + content merge), and the old canonical content becomes
  archived or removed.

This **breaks the lock-step release coupling** that today forces bees
and honeycomb to ship together when bees introduces new
prompts/contracts. Honeycomb becomes a continuous-delivery substrate;
bees development happens in honeycomb PRs at the prompt/contract
level without a bees source-code change.

### Observation 3 — Semantic recall over a flat index can't honour overrides

With multiple variants of the same drawer in canon, a single ChromaDB
collection has three failures:

- Queries return canonical AND every override of the same drawer,
  even though only one applies to the caller's context.
- Embedding overlap between variants destabilises ranking.
- Index size scales with `tools × versions × consumers` even though
  most queries only need one slice.

Metadata filtering at query time helps but doesn't solve dedup (same
content surfaces under different metadata) and doesn't help with
ranking noise.

## Decision

### 1. Drawer overrides

A drawer file's name encodes its **scope** via a `queenfile_<tag>`
suffix. The base canonical drawer carries no suffix:

```
wing_bees/build/manual-amend/
  closet.md                                       # canonical
  behaviour.md                                    # canonical drawer
  behaviour.queenfile_bees-v1.18.md               # override for bees v1.18+
  behaviour.queenfile_scarab.md                   # override for scarab consumer
  guidance.md
  guidance.queenfile_bees-v1.18.md
```

Multiple overrides on the same canonical drawer coexist as long as
their suffixes differ. The filename is **a hint**; the authoritative
targeting rules live in the override file's frontmatter:

```markdown
<!-- behaviour.queenfile_bees-v1.18.md: bees v1.18 override.

target: behaviour
tool: bees
tool_version: ">=v1.18"
consumer: null
rationale: |
  v1.18 introduces the scoped recall context. Builders need to pass
  tool_version through queries; spec contract documents this.
-->

<override content body — replaces behaviour.md when this scope applies>
```

### 2. Override resolution

When recall asks for the `behaviour` drawer in a given closet under a
calling context `{tool: "bees", tool_version: "v1.18", consumer:
"scarab"}`, the resolution algorithm picks the **most-specific
matching variant**:

```
candidates = [behaviour.md,
              behaviour.queenfile_bees-v1.18.md,
              behaviour.queenfile_scarab.md]

# Filter to candidates whose frontmatter rules match the context.
matching = [c for c in candidates if context_matches(c.frontmatter)]

# Rank by specificity: more axes matched > version-pinned > consumer-pinned.
chosen = rank_by_specificity(matching)[0]
```

**Specificity ranking (tiebreaker order):**

1. **Number of axes matched.** An override targeting both `tool` and
   `consumer` beats an override targeting just `tool`.
2. **Version specificity.** A `==v1.18` pin beats `>=v1.18`. An exact
   version match beats a range.
3. **Consumer specificity.** A specific consumer name beats `null`
   (any consumer).
4. **File mtime (last resort).** When equally specific overrides
   exist (a curation error), the most recently written wins. Lint
   flags this case.

If no override matches, canonical wins. Canonical with no overrides
behaves identically to today.

### 3. Scope-keyed semantic indexes

Honeycomb v1.1 maintains **one ChromaDB collection per active scope**,
not a single global collection.

```
~/.mempalace/honeycomb_v1/
  canon.chromadb                          # canonical only (context-less recall fallback)
  scope_bees-v1.17.chromadb               # canon + bees-v1.17 overrides resolved
  scope_bees-v1.17_scarab.chromadb        # + scarab overrides resolved
  scope_bees-v1.18-dev.chromadb           # bees v1.18-dev overrides resolved
  scope_bees-v1.18-dev_scarab.chromadb
```

Each scope's collection contains the **post-resolution** drawer set
for that scope — override-selection has already happened at index
time. Query-time logic is simple: pick the collection, query it.

Scope keys are composed deterministically:

```
canon                                     # no scope
scope_<tool>-<version>                    # tool + version
scope_<tool>-<version>_<consumer>         # + consumer
```

(Multiple consumers per scope require their own collections; not
multiplexed.)

### 4. Scope discovery for indexing

Install enumerates **only active scopes** based on:

- **Tool versions** from the installed tool(s). Bees reports its
  version via `bees --version`; future tools the same.
- **Consumers** from `~/.bees/consumers.json` registry (and analogous
  registries for future tools).

For each `(tool, tool_version, consumer)` tuple in the active set,
plus the universal `canon` baseline, the index builder materializes
a scope collection.

Triggers for reindex:

- `tools/install.sh` (full reindex on update)
- `bees init <new-consumer>` (incremental — adds new scopes)
- `bees --upgrade-tool-version` or equivalent (incremental — adds
  new tool-version scopes)
- Explicit `bash ~/.honeycomb/tools/build_index.py --force`

### 5. Recall API: scope is a first-class parameter

```python
palace_recall(
    query,
    wings=None, halls=None,
    tools=None, models=None, languages=None,
    project=None,
    # NEW: explicit scope inputs
    tool=None, tool_version=None, consumer=None,
    top_k=3, drawer=False,
    include_pending=True,
) -> [ { wing, room, closet, content, source, ... } ]
```

When called without `tool` / `tool_version` / `consumer`, the library
derives them from the MCP env (`BEES_FEATURE_SLUG`, `BEES_REPO_ROOT`,
`BEES_TOOL_VERSION`). Explicit args win over env-derived.

Result objects gain a `source` field marking which collection served
the result (e.g. `source: "scope_bees-v1.17_scarab"` vs
`source: "canon"`).

### 6. ADR-0001 collapses into a special case

Under ADR-0002, the petition mechanism in ADR-0001 simplifies to:

- **Petition = submitting an override file.** A consumer's queen calls
  `palace_petition_submit(target_drawer, content)` which writes
  `<target>.queenfile_<consumer>.md` to canon (via auto-PR) and
  optionally to the consumer's local overlay (for self-recall during
  the PR-open window).
- **Adoption = promotion of an override to canonical.** Honeycomb
  maintainer edits canonical drawer to incorporate the override's
  content, deletes the override file. One PR.
- **Rejection = override file deleted without promotion.** One PR.

ADR-0001's "queenfile schema with YAML pending-petition blocks" is
gone. The override file IS the petition. ADR-0001 should be updated
to reference ADR-0002 as the underlying mechanism.

## Consequences

**Positive**

- **Version decoupling.** Bees prompt/contract changes ship as
  honeycomb PRs, independent of bees source-code releases. Multiple
  bees versions coexist in a single honeycomb release.
- **Petition mechanism dissolves into the override mechanism.** One
  concept, one machinery, one set of tooling.
- **Recall results are clean.** Scoped indexes return only variants
  that apply; no metadata-filter noise.
- **Consumer customization is structural.** A consumer overriding a
  drawer for their project's needs uses the same mechanism as a
  tool-version development branch — both write override files.
- **Local development of overrides is straightforward.** Operator
  writes an override file in `~/.honeycomb` working tree, reindexes,
  queens read it. When ready to ship, commit + PR.

**Negative**

- **Significant new machinery.** Override resolution, scope enumeration,
  per-scope index build, scope-aware recall API — all new code in the
  honeycomb library and install path.
- **Install becomes stateful about scopes.** New consumer or new tool
  version requires reindex. Today's install is "pull + reindex
  globally"; v1.1 install needs to know what scopes exist.
- **Storage scales with active scopes.** A consumer with 3 tool
  versions × 5 consumers = 15 scope collections plus canon. Each
  collection is small (most drawers don't have overrides), but the
  fixed overhead adds up.
- **Override curation discipline required.** Overlapping/conflicting
  override targets need lint to catch curation errors before they
  cause "most recently written wins" surprises.

## Alternatives considered

- **Metadata filtering on a single index.** Simpler infrastructure but
  noisy dedup, ranking instability, and growing index size. Rejected
  because the noise problem only worsens as overrides accumulate.

- **Views over a single index.** ChromaDB doesn't natively support
  filtered views. Could simulate at the library layer, but every
  query incurs the filter cost and the dedup problem remains.

- **Tool-version coupling preserved.** Bees and honeycomb continue to
  ship in lock-step; new prompts require new bees releases.
  Rejected: the user's stated requirement is decoupling. Without
  override files, bees development would have to fork honeycomb canon
  every time it wanted to test new content.

- **Consumer overlay only, no canon overrides.** All overrides live in
  consumer overlay; nothing override-shaped ever lands in canon.
  Rejected because tool-version development needs a place to ship
  prompts that all consumers using that version see — that's canon,
  not consumer overlay.

## Open questions

1. **Scope key format stability.** Once a scope key is materialized
   (`scope_bees-v1.18_scarab`), is it stable across honeycomb
   releases, or can it be renamed? Stability is desirable for cache
   reuse, but tool-version naming conventions might evolve.

2. **Lint at index time vs commit time.** Override frontmatter / file
   name agreement should be enforced. Does the linter run at install
   time (catching late, in production), or at commit time on canon
   PRs (catching early)? Likely both, with different severity.

3. **`canon`-only fallback semantics.** When a scoped index doesn't
   exist (e.g. brand new consumer, no reindex yet), recall falls back
   to canon. Should the fallback be silent (operator may not know
   their scope is missing), or should it surface a warning?

4. **Multi-tool consumer.** A consumer that uses bees AND a future
   tool needs scopes for both. Scope key composition needs to handle
   `(bees-v1.18, beetle-v0.5, scarab)` cleanly without combinatorial
   explosion (don't materialize bees-v1.18 × beetle-v0.5 cross-product
   unless needed).

5. **Override depth.** Should overrides themselves be overridable?
   E.g. `behaviour.queenfile_bees-v1.18.queenfile_scarab.md` — scarab's
   variant of the bees-v1.18 override. Probably no — this gets
   semantically muddy fast. Single-layer overrides only.

## Sequencing

ADR-0002 must ship in the same release as ADR-0001 (honeycomb v1.1.0).
The override + scope machinery is the foundation that the simplified
petition flow stands on. ADR-0001's H1-H8 work list expands:

- H2 (`palace_petition_submit`) is now "writes an override file"
- H3 (`palace_petition_list`) is now "walks override files matching
  consumer scope"
- H4 (queenfile schema) is now "override file frontmatter schema"
- H5 (queenfile-aware recall) is now "scoped-index recall" — much
  larger work item
- **NEW H5a** — override resolution algorithm in `lib/honeycomb/recall.py`
- **NEW H5b** — scope-keyed index builder in `tools/build_index.py`
- **NEW H5c** — scope discovery + reindex triggers in
  `tools/install.sh`
- **NEW H5d** — scope-aware MCP server (env-derived scope params)

ADR-0001 should be updated to reference ADR-0002 and have the
overlapping sections retitled or removed.

---

## Post-v1.1.0 supersession note

**Petition identity is the override file path, not a date-sequenced id.**

The v1.1.0 implementation shipped `petition_id` (a `YYYYMMDD-NNN-<scope>` string)
in `PetitionResult` and `PendingPetition`, generated via `git log` date and a
`rglob`-based counter. The retro identified this as unnecessary complexity: the
override file's path within canon (e.g.
`wing_bees/build/manual-amend/behaviour.queenfile_scarab.md`) is already a unique,
stable, human-readable identity.

**Changes in the v1.1.0 fixup (shipped on the `honeycomb-v1-1-fixups` branch):**

- `petition_id` field removed from `PetitionResult` and `PendingPetition` dataclasses
  in `lib/honeycomb/petitions.py`.
- `palace_petition_withdraw` now takes `path: str` (the override file's relative path
  within canon) instead of `petition_id`.
- Branch names are derived deterministically from the override file path
  (e.g. `feat/petition-<sha1(rel_path)[:12]>`); no date or counter logic.
- `palace_petition_submit` returns `{branch, pr_url, overlay_path}` — no `petition_id`.
- `palace_petition_list` entries carry `{target, consumer, tool, tool_version, path,
  source, rationale}` — no `petition_id`.
- The HTML-comment frontmatter written into override files no longer contains a
  `petition_id:` line.

**Backwards compatibility:** The frontmatter parser ignores unknown fields, so any
`petition_id:` lines in override files written by v1.1.0 are silently ignored by
v1.1.1+. No migration script is needed.
