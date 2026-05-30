# Honeycomb

Agentic knowledge palace for development tools — wing/room/closet/drawer
structure with keyword + ChromaDB-backed semantic recall, served via MCP.

Honeycomb is a structured, text-canonical knowledge base that agentic
systems query at runtime via `palace_recall`. It uses the
[MemPalace](https://mempalaceofficial.com/concepts/the-palace.html)
vocabulary (wings, rooms, closets, drawers) with two extensions:

- **Halls** — intra-wing intent-based categories
  (`hall_architecture`, `hall_protocol`, `hall_procedure`,
  `hall_pattern`, `hall_antipattern`, `hall_rubric`). Encoded in
  each closet's frontmatter.
- **Scoped tunneling** — wings declare a scope (`universal`,
  `runtime`, `project:<name>`) so cross-wing recall returns only
  relevant context for the active project.

## Structure

Four-level hierarchy: **wing / room / closet / drawer**.

```
honeycomb/
  wing_bees/                      # runtime wing
    test/                         # room (topic-shaped, tunnels across wings)
      sapper/                     # closet (named lens on the topic)
        closet.md                 # mandatory: ≤500 char agentic summary
        index.md                  # mandatory: TOC of drawers
        behaviour.md              # drawer (verbatim ## section from source)
        heuristics.md             # drawer
        tunnels.md                # see-also references (manual)
```

Two mandatory files per closet (`closet.md` + `index.md`). All other
files are drawers carrying the original `## section` content
verbatim. Each wing has a `_manifest.yaml` declaring its scope,
version, mandatory drawers, and canonical rooms.

## Wings

| Wing | Scope | Purpose |
|---|---|---|
| `wing_bees` | runtime | Bees's runtime knowledge — operating prompts and contracts |
| `wing_repo_<project>` | project:`<project>` | Codebase knowledge per consumer repo |
| `wing_practices` | universal | Good patterns for any project's SSDLC |
| `wing_antipatterns` | universal | Known-bad patterns |
| `wing_tools` | universal | Tool catalog (pytest, lcov, gh, etc.) |
| `wing_models` | universal | Model catalog (claude family, gemma, etc.) |

## MCP server

`bin/honeycomb-mcp` is a stdio JSON-RPC 2.0 MCP server exposing five
tools to MCP-aware clients (Claude Code, etc.):

- **`palace_recall`** — keyword recall (always available, pure stdlib)
- **`palace_recall_semantic`** — vector recall via ChromaDB
  (optional; gracefully falls through to `[]` when chromadb is
  missing or no index exists)
- **`palace_petition_submit`** — write a drawer override to a feature branch and open a PR (v1.1)
- **`palace_petition_list`** — list pending override files for a consumer scope (v1.1)
- **`palace_petition_withdraw`** — close a petition PR and remove the override file (v1.1)

Both return the same shape, with a composite `room` field
(`"<room>/<closet>"`) for closet-level disambiguation:

```json
{
  "wing": "wing_bees",
  "room": "build/manual-amend",
  "hall": "hall_procedure",
  "path": ".../wing_bees/build/manual-amend/closet.md",
  "closet": "<closet text>"
}
```

Semantic recall surfaces matches keyword misses (and vice versa);
callers typically blend them with fallthrough on empty results.

## Consumer integration

Honeycomb is designed for one-time install + reuse across consumers
(bees, beetle-tool-suite, future agentic tools).

### Install

```bash
git clone --depth 1 --branch v1.1.0 https://github.com/viviane1016/honeycomb ~/.honeycomb
```

**Scope-aware install (v1.1):** pass `--tool`, `--tool-version`, and/or
`--consumer` to resolve drawer overrides for your context. Absent flags =
canonical-only (v1.0 behaviour):

```bash
# canonical-only (v1.0-compatible):
bash ~/.honeycomb/tools/install.sh

# scope-resolved for bees v1.18:
bash ~/.honeycomb/tools/install.sh --tool bees --tool-version v1.18 --consumer scarab
```

After an install that updates canon, a one-line petition manifest summary is printed:
`Petitions: N accepted, M declined, K pending since v<prev>`.

### MCP config

Add this to your consumer's `.mcp.json`:

```json
{
  "mcpServers": {
    "honeycomb": {
      "command": "/path/to/.honeycomb/bin/honeycomb-mcp",
      "env": {
        "HONEYCOMB_ROOT": "/path/to/.honeycomb"
      }
    }
  }
}
```

Or launch `claude` with `--mcp-config` pointing at it.

### Environment

- `HONEYCOMB_ROOT` — repo root containing `wing_*/`. Defaults to the
  parent directory of `bin/honeycomb-mcp` when unset.
- `BEES_FEATURE_SLUG` — when set by a bees consumer, `palace_recall`
  writes an audit trace to `.bees/<slug>/honeycomb-trace.md`.
- `BEES_REPO_ROOT` — used to locate `.bees/<slug>/` for trace writing and
  log destination; also controls the consumer overlay path
  (`.bees/honeycomb-overlay/`).

**Actor identity env vars (v1.1):**

| Var | Purpose |
|---|---|
| `BEES_ACTOR` | Role name propagated into MCP log records (e.g. `queen`, `scribe`) |
| `BEES_STAGE` | Bees pipeline stage (e.g. `plan`, `spec`, `ship`) |
| `BEES_MODEL` | Model ID driving the calling actor |

Missing values log as `"unknown"`. These are set by the bees harness; direct
`honeycomb-mcp` users can set them manually for annotated logs.

### Petition tools (v1.1)

Three MCP tools for consumer→canon content proposals:

| Tool | Purpose |
|---|---|
| `palace_petition_submit` | Write a drawer override to a feature branch in canon and open a PR |
| `palace_petition_list` | List pending override files matching a consumer scope |
| `palace_petition_withdraw` | Remove an override file from its feature branch and close the PR |

`submit` requires `HONEYCOMB_ROOT` (canon) and optionally `BEES_REPO_ROOT`
(writes a copy to `.bees/honeycomb-overlay/` for immediate self-recall before
PR merge). `gh` CLI must be installed and authenticated.

### Consumer overlay (v1.1)

Place override files at `$BEES_REPO_ROOT/.bees/honeycomb-overlay/wing_*/...`.
`palace_recall` and `palace_recall_semantic` merge the overlay into recall
results at query time; overlay files win over canon for matching drawer paths.
No ChromaDB reindex needed — the overlay is merged at read time via linear scan.

### Observability log (v1.1)

Every MCP tool call appends one JSONL record. Default destination:
`$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl` when `BEES_REPO_ROOT` and
`BEES_FEATURE_SLUG` are set; falls back to `$HONEYCOMB_ROOT/.calls.jsonl`.

Record schema (v1):

```json
{
  "schema_version": 1,
  "ts": "<ISO-8601 UTC>",
  "tool": "palace_recall",
  "slug": "<feature-slug or unknown>",
  "actor": "<BEES_ACTOR or unknown>",
  "stage": "<BEES_STAGE or unknown>",
  "model": "<BEES_MODEL or unknown>",
  "request": { ... },
  "response": [ ... ],
  "duration_ms": 42,
  "bytes": 1234,
  "content_sha": "<sha256 hex>"
}
```

### Semantic recall (optional)

The vector layer requires `chromadb`. Index is rebuilt from the
text-canonical source on demand:

```python
from honeycomb.semantic import index_closets
n, version = index_closets()  # writes to ~/.mempalace/honeycomb_v1/
```

Without chromadb installed or an index built, `palace_recall_semantic`
returns `[]` cleanly so callers fall through to keyword recall.

## Text-canonical, DB-optional

The `.md` files in `wing_*/` are the source of truth. The
ChromaDB-backed cache at `~/.mempalace/honeycomb_v1/` is derived
state — regenerable from text, never authoritative. Edit the text.

## Versioning

Two levels of semver:

- **Top-level** (`VERSION`) — overall release.
- **Per-wing** (`wing_*/_manifest.yaml: version:`) — wings move
  independently; top-level aggregates the highest bump kind.

Semver semantics: PATCH = content edit; MINOR = additive (new closet,
drawer, canonical room); MAJOR = removal/rename/scope/contract change.

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Drawer overrides (v1.1)

A drawer can have per-scope variants alongside the canonical file. The
filename encodes scope via a `queenfile_<tag>` suffix:

```
wing_bees/build/manual-amend/
  behaviour.md                         # canonical drawer
  behaviour.queenfile_bees-v1.18.md    # override for bees ≥ v1.18
  behaviour.queenfile_scarab.md        # override for the scarab consumer
```

Override files carry authoritative frontmatter:

```markdown
<!-- target: wing_bees/build/manual-amend/behaviour.md
     tool: bees
     tool_version: ">=v1.18"
     consumer: null
     rationale: "Updated amend guidance for v1.18 rebase workflow" -->
```

Specificity ranking at install time: axes-matched > version-specificity
(exact `==` beats range `>=`) > consumer-specificity (named beats null) >
mtime tiebreaker. The winner is materialized as `behaviour.md` in the
flattened install tree; the canonical file is unchanged in the source repo.

## Design references

- [ADR-0024 in the bees repo](https://github.com/viviane1016/bees/blob/main/decisions/0024-rooms-closets-drawers-realignment.md)
  — four-level structure, scoped tunneling, migration plan.
- `decisions/` — honeycomb-specific ADRs; see [decisions/INDEX.md](decisions/INDEX.md)
  for a short index of all four v1.1 ADRs.
