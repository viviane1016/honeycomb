## Parser and emitter

The petition parser is `parse_palace_proposal_blocks` in `lib/bees/plan.py`. It scans queen output for the three opener shapes and returns `list[dict]` with discriminator `shape` ∈ `{single, bundle}`. Single dicts carry `path`, `kind` (`amendment`|`new-room`), `body`; bundle dicts carry `constituents: list[{path, kind, body}]` and a top-level `paths` convenience list. Both shapes carry an optional `adr` key.

Artifacts are written to `.bees/<slug>/petitions/`:
- Single: `NNN-<room-basename>.md`
- Bundle: `NNN-bundle-<first-room-stem>.md`

Secret-pattern scan applies to the full body before writing. A hit writes `<filename>.suspect` and flags on stderr; the operator must review before merging.
