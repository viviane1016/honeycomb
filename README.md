# Honeycomb

Agentic knowledge palace for development tools.

Honeycomb is a structured, text-canonical knowledge base that
agentic systems query at runtime via `palace_recall`. It uses the
MemPalace vocabulary (wings, rooms, closets, drawers) with two
extensions:

- **Halls** — intra-wing intent-based categories
  (`hall_architecture`, `hall_protocol`, `hall_procedure`,
  `hall_pattern`, `hall_antipattern`, `hall_rubric`). Encoded in
  each closet's frontmatter.
- **Scoped tunneling** — wings declare a scope (`universal`,
  `project:<name>`, `tool:<name>`) so cross-wing recall returns
  only relevant context for the active project.

## Structure

Four-level hierarchy: **wing / room / closet / drawer**.

```
honeycomb/
  wing_bees/                      # singleton runtime wing for bees
    test/                         # room (topic-shaped name)
      sapper/                     # closet (named lens on the topic)
        closet.md                 # mandatory: ≤500 char agentic summary
        index.md                  # mandatory: TOC of drawers
        design.md                 # mandatory: design rationale
        Readme.md                 # mandatory: human-targeted overview
        yml.md                    # drawer: operating prompt (BUILD_INLINE target)
        heuristics.md             # drawer
```

Each wing has a `_manifest.yaml` declaring its scope and mandatory
drawers. The **taster drone** validates compliance on every release.

## Wings

| Wing | Scope | Purpose |
|---|---|---|
| `wing_bees` | tool:bees | Runtime knowledge consumed by the bees orchestrator. |
| `wing_repo_<project>` | project:`<project>` | Codebase knowledge per consumer repo. |
| `wing_practices` | universal | Good patterns for any project's SSDLC. |
| `wing_antipatterns` | universal | Known-bad patterns. |
| `wing_tools` | universal | Tool descriptions (pytest, lcov, gh, claude CLI, etc.). |
| `wing_models` | universal | Model selection rubric. |

## Text-canonical, DB-optional

The `.md` files in `wing_*/` are the source of truth. The MCP server
serves recall in two modes:

- **Text-only mode** — reads files directly per query. Zero infra.
- **Indexed mode** — reads from a Chroma collection at
  `~/.mempalace/honeycomb/`. Built from the same text files via the
  install script.

## Status

v1.0 in progress. See [ADR-0024 in the bees repo](https://github.com/viviane1016/bees/blob/main/decisions/0024-rooms-closets-drawers-realignment.md)
for the design and migration plan.
