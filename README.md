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

`bin/honeycomb-mcp` is a stdio JSON-RPC 2.0 MCP server exposing two
tools to MCP-aware clients (Claude Code, etc.):

- **`palace_recall`** — keyword recall (always available, pure stdlib)
- **`palace_recall_semantic`** — vector recall via ChromaDB
  (optional; gracefully falls through to `[]` when chromadb is
  missing or no index exists)

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
git clone --depth 1 --branch v1.0.0 https://github.com/viviane1016/honeycomb ~/.honeycomb
```

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
- `BEES_REPO_ROOT` — used to locate `.bees/<slug>/` for trace writing.

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

## Design references

- [ADR-0024 in the bees repo](https://github.com/viviane1016/bees/blob/main/decisions/0024-rooms-closets-drawers-realignment.md)
  — four-level structure, scoped tunneling, migration plan.
- `decisions/` — honeycomb-specific ADRs (to be populated as the
  project evolves independently).
