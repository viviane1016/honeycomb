---
type: scribe-only
output-files:
  - wing_bees/plan/petitions-flow/closet.md
  - wing_bees/plan/petitions-flow/index.md
  - wing_bees/plan/petitions-flow/mcp-tool-emission.md
  - wing_bees/plan/petitions-flow/lifecycle.md
  - wing_bees/plan/queenfile-contract/closet.md
  - wing_bees/plan/queenfile-contract/index.md
  - wing_bees/plan/queenfile-contract/file-format.md
  - wing_bees/plan/queenfile-contract/specificity-ranking.md
  - wing_bees/plan/palace-petitions/closet.md
  - wing_bees/plan/palace-petitions/index.md
  - wing_bees/plan/palace-petitions/petition-shapes.md
  - wing_bees/plan/palace-petitions/parser-and-emitter.md
  - wing_bees/plan/palace-petitions/statuses.md
  - wing_bees/plan/palace-petitions/related-decisions.md
  - wing_bees/plan/palace-petitions/migration.md
---

# Spec 010 — New plan-room closets (3)

## Builder model

claude-sonnet-4-6

## Goal

Create two new `wing_bees/plan/` closets (`petitions-flow`, `queenfile-contract`) and rewrite the existing `palace-petitions` closet to describe the v1.1 block→MCP-tool migration and one-release backwards-compat window.

## Scope

**New files:**

- `wing_bees/plan/petitions-flow/closet.md` — ≤500 char summary of the MCP petition flow
- `wing_bees/plan/petitions-flow/index.md` — TOC
- `wing_bees/plan/petitions-flow/mcp-tool-emission.md` — `palace_petition_submit/list/withdraw` tool contracts
- `wing_bees/plan/petitions-flow/lifecycle.md` — submit → PR open → adopted/declined lifecycle
- `wing_bees/plan/queenfile-contract/closet.md` — ≤500 char summary of the override file format
- `wing_bees/plan/queenfile-contract/index.md` — TOC
- `wing_bees/plan/queenfile-contract/file-format.md` — naming pattern, frontmatter schema, example
- `wing_bees/plan/queenfile-contract/specificity-ranking.md` — resolution algorithm and tiebreaker order
- `wing_bees/plan/palace-petitions/migration.md` — NEW drawer: block→tool migration, one-release window

**Rewritten files:**

- `wing_bees/plan/palace-petitions/closet.md` — updated summary: block format deprecated; MCP tool primary
- `wing_bees/plan/palace-petitions/index.md` — updated TOC (adds migration drawer)
- `wing_bees/plan/palace-petitions/petition-shapes.md` — deprecated legacy shapes; deprecation notice added
- `wing_bees/plan/palace-petitions/parser-and-emitter.md` — v1.1 MCP path + legacy block translation layer
- `wing_bees/plan/palace-petitions/statuses.md` — adds petition manifest summary line
- `wing_bees/plan/palace-petitions/related-decisions.md` — updated to reference ADR-0001/0002/0004

**Non-goals:**

- No changes to `lib/`, `bin/`, `tools/`, or `tests/` (code work is in other specs)
- No changes outside `wing_bees/plan/` and the spec file itself
- No changes to `wing_repo_bees/` (covered by specs 011 and 012)

## Failing test

```
# Before this unit runs, these paths are absent:
test -f wing_bees/plan/petitions-flow/closet.md && echo FAIL || echo PASS  # → PASS (absent)
test -f wing_bees/plan/queenfile-contract/closet.md && echo FAIL || echo PASS  # → PASS (absent)

# After this unit runs, these must exist:
test -f wing_bees/plan/petitions-flow/closet.md
test -f wing_bees/plan/petitions-flow/mcp-tool-emission.md
test -f wing_bees/plan/petitions-flow/lifecycle.md
test -f wing_bees/plan/queenfile-contract/closet.md
test -f wing_bees/plan/queenfile-contract/file-format.md
test -f wing_bees/plan/queenfile-contract/specificity-ranking.md
test -f wing_bees/plan/palace-petitions/migration.md
# And palace-petitions/closet.md must contain "v1.1":
grep -q "v1.1" wing_bees/plan/palace-petitions/closet.md
```

## Builder prompt

This is a scribe-only unit; the scribe acts as builder.

Create the following closets under `wing_bees/plan/`. Each new closet follows the established structure (canonical HTML-comment header in `closet.md`, `index.md` TOC, 1-2 drawer `.md` files). All content is derived from the plan (honeycomb v1.1) and ADR-0001 / ADR-0002.

### wing_bees/plan/petitions-flow/ (NEW)

`closet.md` (≤500 chars): summary of the MCP petition flow — `palace_petition_submit` writes a scope-keyed drawer override file to a canon feature branch + PR, mirrors to consumer overlay. Adoption = merge, rejection = close.

`index.md`: TOC listing `mcp-tool-emission` and `lifecycle` drawers.

`mcp-tool-emission.md`: contracts for all three petition MCP tools (`palace_petition_submit`, `palace_petition_list`, `palace_petition_withdraw`), including parameter shapes, return values, `gh` CLI dependency, and `PetitionError` on missing `gh`.

`lifecycle.md`: five-step lifecycle (submit → in-flight → adopted/declined/withdrawn) with manifest summary note.

### wing_bees/plan/queenfile-contract/ (NEW)

`closet.md` (≤500 chars): summary of the `<drawer>.queenfile_<scope>.md` naming pattern, HTML-comment frontmatter schema, and specificity ranking.

`index.md`: TOC listing `file-format` and `specificity-ranking` drawers.

`file-format.md`: naming pattern, frontmatter field reference (`target`, `tool`, `tool_version`, `consumer`, `rationale`), annotated example from ADR-0002.

`specificity-ranking.md`: resolution algorithm (filter → rank), four-tier ranking order (axes matched > version pin > consumer name > mtime), note that canonical wins when no override matches.

### wing_bees/plan/palace-petitions/ (REWRITE)

`closet.md`: rewrite to state that v1.1 uses `palace_petition_submit` MCP tool; `<<<PALACE PROPOSAL>>>` blocks deprecated for one release post-excise; block parsing removed afterward.

`index.md`: update TOC to add `migration` drawer.

`petition-shapes.md`: prepend deprecation notice; keep legacy shape documentation for operator reference during the compat window.

`parser-and-emitter.md`: update to describe both v1.1 MCP path (primary) and legacy translation path (one-release window).

`statuses.md`: add note that petition manifest summarises accepted/declined/pending counts at install time.

`related-decisions.md`: update to reference ADR-0001, ADR-0002, ADR-0004.

`migration.md` (NEW): comparison table (v1.0 vs v1.1), backwards-compat window details, and operator action required to update queen prompts.

## Success check

1. All 15 output files exist at their declared paths within the cell.
2. `wing_bees/plan/petitions-flow/closet.md` is ≤500 chars.
3. `wing_bees/plan/queenfile-contract/closet.md` is ≤500 chars.
4. `wing_bees/plan/palace-petitions/closet.md` contains "v1.1" and "deprecated".
5. `wing_bees/plan/palace-petitions/migration.md` exists and contains "one-release" or "backwards-compat".
6. All files committed in a single commit with the prescribed subject line.
7. Spec path referenced in commit body.

## Commit message

```
bees scribe-only: honeycomb-v1-1 010 — New plan-room closets (3).

Add wing_bees/plan/petitions-flow/ and wing_bees/plan/queenfile-contract/
as new closets, and rewrite wing_bees/plan/palace-petitions/ to document
the v1.1 block→MCP-tool petition migration and one-release compat window.

Refs: .bees/honeycomb-v1-1/specs/010-new-plan-room-closets-3.md
```
