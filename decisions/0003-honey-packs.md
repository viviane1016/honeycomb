# ADR-0003: Honey packs — à la carte content modules

**Date:** 2026-05-30
**Status:** Proposed

## Context

ADR-0002 established the **drawer-override + scoped-resolution**
mechanism for evolving honeycomb content without lock-stepping with
consumer tool releases. ADR-0001 (revised) recast petitions as a
special case of overrides — submitting an override file to canon.

Both ADRs assume **all honeycomb content lives in one canon repo**.
That model has a hard ceiling:

### Problem 1 — Canon size scales with universe

If every model family (Gemma, Claude Sonnet, Claude Haiku, Llama,
Mistral, etc.), every tool (pytest, lcov, gh, cargo, npm, etc.), and
every consumer's project-meta content all live in canon, the
maintenance burden scales with the universe of agentic tools and
models — not with any single operator's use.

A consumer using only Claude Sonnet + pytest doesn't need to download
or index content about Gemma + Llama + Cargo + Rust. Today's
canon-only model forces them to.

### Problem 2 — Content authorship doesn't centralise well

The honeycomb maintainer can't be the authority on every model and
tool. The Gemma community knows Gemma's prompting traits better than
anyone else; the Rust community knows Rust testing patterns better
than the bees maintainer.

Forcing all content through a single canon repo creates a curation
bottleneck and produces content that's accurate-by-committee at best.

### Problem 3 — Ecosystem participation has no shape

Today there's no mechanism for a third party to contribute content
that operators can opt into. The only path is "PR to viviane1016/
honeycomb." That works for small-scale curated growth; it doesn't
scale to a community ecosystem.

## Decision

**Introduce honey packs — independently-versioned content modules
that extend canon at install time.**

```
┌─────────────────────────────────────────────────────────────┐
│  HONEYCOMB LIBRARY                                            │
│  ~/.honeycomb/bin/honeycomb-mcp + lib/honeycomb/             │
│  Versioned in lock-step with recall/override semantics.       │
└─────────────────────────────────────────────────────────────┘
                       │
                       │  contains
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  CANON CONTENT (shipped with the library)                     │
│  ~/.honeycomb/wing_bees/, wing_practices/, wing_antipatterns/ │
│  wing_tools/ (catalog stubs), wing_models/ (catalog stubs)    │
└─────────────────────────────────────────────────────────────┘
                       │
                       │  extended by
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  HONEY PACKS (à la carte, opt-in)                             │
│  ~/.honeycomb/honey/<pack>/ (staged sources)                  │
│    honey-gemma-4/        → wing_gemma_4 + deepens wing_models │
│    honey-claude-haiku/   → wing_claude_haiku                  │
│    honey-pytest-deep/    → drawers extending wing_tools/test/ │
│    honey-rust/           → wing_repo patterns for Rust        │
│  Each pack independently versioned + maintained.              │
└─────────────────────────────────────────────────────────────┘
                       │
                       │  resolved into
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  CONSUMER VIEW                                                │
│  ~/.honeycomb/wing_*/ (flattened canon + active honey packs)  │
│  ~/.mempalace/honeycomb_v1/ (semantic index over view)        │
└─────────────────────────────────────────────────────────────┘
```

### 1. Honey pack structure

A honey pack is a directory (or repo) carrying:

```
<pack-name>/
  VERSION                    # the pack's own version (e.g. v2.1.0)
  pack.yaml                  # manifest: name, depends-on, provides
  wing_<X>/                  # content following the four-level structure
    <room>/
      <closet>/
        closet.md
        index.md
        <drawer>.md
        <drawer>.queenfile_<scope>.md     # overrides allowed
```

Packs may **introduce new wings** (e.g. `honey-gemma-4` provides
`wing_gemma_4`), **extend existing wings** (e.g. `honey-pytest-deep`
adds rooms/closets/drawers to `wing_tools`), or **override canon
content** (e.g. via override drawers on wings the pack does not own).

### 2. Pack manifest (`pack.yaml`)

```yaml
name: honey-gemma-4
version: 2.1.0
description: |
  Deep content for Gemma 4 family — prompt traits, cost/benchmark
  data, per-tool adaptations.

depends_on:
  honeycomb_library: ">=1.1"
  canon: ">=1.0"
  # Other honey packs this one depends on (rare; e.g. honey-pytest-async
  # might depend on honey-pytest-deep).
  honey_packs: []

provides:
  wings: [wing_gemma_4]
  extends_wings: [wing_models]            # adds content to canon wing
  override_drawers: []                    # no overrides on canon

# Trust hint for the install UI; operator is the authority.
maintainer: gemma-community
homepage: https://github.com/gemma-community/honey-gemma-4
license: MIT
```

### 3. Install integration

Bees install (or `honeycomb install`) orchestrates:

```
1. Honeycomb library check (per ADR-0002):
     if installed_hc < bees_required_hc: upgrade honeycomb library

2. Canon pull:
     git fetch in ~/.honeycomb; check out canon at the resolved tag

3. Honey pack reconcile:
     For each pack in active profile:
       if not staged at ~/.honeycomb/honey/<pack>: clone/download
       if staged version mismatch: pull update
     For each staged pack not in active profile:
       remove from ~/.honeycomb/honey/<pack>/

4. Resolve consumer view:
     Walk canon + all active honey packs:
       Apply override resolution (ADR-0002 specificity rules)
       Apply scope filter (this consumer, this tool version)
     Write flattened result to ~/.honeycomb/wing_*/

5. Reindex semantic store

6. Show petition manifest + honey-pack change report
```

### 4. Active profile

The operator's `active profile` declares which honey packs are
installed. Two places it can live:

**Per-consumer (preferred):**
- `<consumer_repo>/.bees/honey.yaml` — checked into the consumer's
  repo. Travels with the project; teammates get the same view.

**Per-machine (fallback / global default):**
- `~/.bees/honey.yaml` — operator-machine-wide defaults.

Active profile = per-consumer overlaid on per-machine.

```yaml
# .bees/honey.yaml
honey_packs:
  - name: honey-claude-sonnet-4-7
    version: "^1.0"
  - name: honey-claude-haiku-4-5
    version: "^1.0"
  - name: honey-gemma-4
    version: "^2.0"
  - name: honey-pytest-deep
    version: "^1.2"
```

Version syntax follows npm/cargo-style semver ranges.

### 5. Discovery

For honeycomb v1.2 launch, **convention-based discovery**:

- Honey packs live under a known prefix on GitHub: any repo named
  `honey-*` is conventionally a honey pack
- Bees install resolves a pack name to a repo URL by trying a
  configured list of GitHub orgs (default: `viviane1016/honey-*`,
  expandable via per-machine config)
- Operators can also point at explicit URLs in `honey.yaml` for
  unconventional locations

**Deferred — central registry.** A registry service (like PyPI for
honey) is BACKLOG. Convention is enough for an early ecosystem; a
registry adds infrastructure burden that isn't justified until many
packs exist.

### 6. Trust

Honey packs are external code the operator opts into. Trust model:

- **Default deny** — install requires explicit declaration in
  `honey.yaml`. No auto-install based on environment-detection
  unless operator explicitly enabled `auto_suggest: true`.
- **Source visibility** — `honeycomb honey show <pack>` displays
  the pack's manifest, source URL, and content tree before install.
- **Signed releases (deferred)** — future versions may require
  signed tags; BACKLOG.
- **Capability scope** — packs can only write into wing
  directories. They cannot ship MCP server code, cannot mutate
  library code, cannot read consumer files. Honeycomb library
  enforces this at install time (reject pack contents outside
  `wing_*/` paths).

### 7. Smart suggestion (opt-in)

When `auto_suggest: true` is set, honeycomb install can detect
patterns and **suggest** packs to install (operator confirms):

```
Detected `BEES_MODEL=gemma-4-31b-it-4bit` in environment.
Suggest installing honey-gemma-4@^2.0? [y/N]

Detected `pytest` in your project's dependencies.
Suggest installing honey-pytest-deep@^1.2? [y/N]
```

Detection sources: env vars, consumer repo's `pyproject.toml` /
`package.json` / `Cargo.toml` / `Gemfile`, bees model config.

### 8. Pack interaction with overrides

Honey packs interact with ADR-0002's override mechanism in three ways:

- A pack may **contain override files** (e.g. `honey-pytest-deep` ships
  `wing_tools/test/pytest/behaviour.queenfile_pytest-async.md` —
  alternate-paradigm content for users using pytest-async). These
  overrides participate in normal resolution.
- A pack may **be the target of overrides** in canon. E.g. canon
  could ship `wing_gemma_4/traits/closet.queenfile_bees-v1.18.md`,
  overriding the honey-gemma-4-provided content for bees v1.18+.
  Operators see the override layered correctly.
- Pack-vs-pack collisions are resolved by **declared dependency
  order**. If two packs provide content at the same path, the pack
  with later `pack.yaml` `priority` wins (or pack name alphabetical
  tiebreak if `priority` unset).

### 9. Resolution algorithm extension

ADR-0002's resolution algorithm walks canon. ADR-0003 extends it to
walk canon + each active honey pack's wing_* tree, treating all of
them as candidate sources for any given drawer. Specificity ranking
applies across the union.

A pack's content is **conceptually equivalent to canon content**
once installed — overrides, frontmatter targeting, scope filtering
all work the same. The pack-source attribution is preserved in
result metadata (`source: honey-gemma-4@2.1.0` vs `source: canon`)
so the operator can tell where content came from.

## Consequences

**Positive**

- **Canon stays small.** Maintainer focuses on bees-runtime and
  universal-pattern content. Domain-specific depth lives in
  community-maintained packs.
- **Ecosystem participation has a shape.** Anyone can publish a
  pack. Operators choose what to trust and install.
- **Install scales with usage.** A consumer using only Sonnet doesn't
  install Gemma/Llama content.
- **Independent versioning.** A pack maintainer can release at their
  own cadence without coordinating with the honeycomb maintainer.
- **Composable with overrides.** Honey packs ship overrides too;
  packs can be customized by consumer queenfile drawers same as canon.

**Negative**

- **Trust burden moves to the operator.** Operators have to evaluate
  packs before installing. Source visibility helps; signing later.
- **Pack-vs-canon collisions.** Two packs (or a pack + canon) might
  provide content at the same path. Resolution rules handle it but
  the precedence is something the operator has to reason about.
- **Discovery is convention-based at launch.** No central index;
  operator has to know which packs exist. BACKLOG'd central registry
  is the long-term answer.
- **Install machinery grows.** Three layers to keep coherent
  (library, canon, packs). Reconcile step at install becomes the
  biggest new code path.

## Alternatives considered

- **Canon-only forever.** Already rejected by Problems 1–3 above.
- **Tool-specific repos (no honey pack abstraction).** Each
  consumer tool ships its own honeycomb (`bees-honeycomb`,
  `beetle-honeycomb`). Rejected because content overlap is huge —
  most tools use Claude, most tools use pytest. Honey packs let the
  same content serve every consumer.
- **Pip extras.** `pip install honeycomb[gemma,pytest]`. Pythonic
  but requires PyPI publishing for every honey author. Convention-
  based discovery is lighter weight for early ecosystem.
- **Packs as honeycomb-library plugins (Python modules).** Would
  let packs ship behaviour, not just content. Rejected (for v1.2)
  because the security model is much heavier and most packs only
  need content. Revisit when a real plugin use case shows up.

## Sequencing

**v1.1 ships ADR-0001 + ADR-0002.** Canon + overrides + petitions
+ scoped install-time resolution. No honey packs.

**v1.2 ships ADR-0003.** Adds:

- `pack.yaml` schema + parser
- Honey pack install / reconcile in `tools/install.sh`
- Resolution extended to walk canon + active packs
- `honeycomb honey list / show / install / remove` CLI commands
- Convention-based discovery (configurable org prefixes)
- Trust UI (`honeycomb honey show` before install)
- Smart suggestion (opt-in via `auto_suggest`)

**Deferred (post-v1.2):**

- Central pack registry
- Signed pack releases
- Plugin-style packs (behaviour, not just content)
- Cross-pack interaction rules beyond simple priority

## Open questions

1. **Pack release artifact format.** Git tags (clone + checkout) is
   simplest and matches today's honeycomb library install. Tarball
   releases on GitHub Releases give immutable artifacts. For v1.2,
   git tag is sufficient.

2. **Pack content layout — owns-wing vs extends-wing.** A pack that
   provides a wing (`honey-gemma-4` → `wing_gemma_4`) has clear
   ownership. A pack that extends an existing wing
   (`honey-pytest-deep` adds content to `wing_tools/test/pytest/`)
   has shared ownership. Lint rule needed: pack `provides.wings`
   vs `extends_wings` should match its directory tree.

3. **Multi-tool consumer sharing packs.** If both bees and beetle
   use Claude content, do they share one `honey-claude-sonnet-4-7`
   install? Likely yes — honey packs are tool-agnostic. The
   resolved view differs per (tool, consumer), but the staged pack
   sources can be shared at `~/.honeycomb/honey/`.

4. **Pack removal hygiene.** When a pack is removed from the active
   profile, its content disappears from the resolved view (good)
   but the staged sources at `~/.honeycomb/honey/<pack>/` could
   linger. Auto-clean or `honeycomb honey prune` command?

5. **Pack update cadence.** Packs that haven't been updated in a
   long time may carry stale content. Should `honeycomb install`
   warn about packs whose latest release is >N months old?
   BACKLOG; depends on real ecosystem usage patterns.
