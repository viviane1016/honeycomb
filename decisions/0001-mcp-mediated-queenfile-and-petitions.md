# ADR-0001: MCP-mediated queenfile, petition flow, and single-API access

**Date:** 2026-05-30
**Status:** Proposed

## Context

The honeycomb extraction (bees ADR-0024) split content from consumer
tooling. Honeycomb v1.0 ships the canonical knowledge base at
`viviane1016/honeycomb`; bees consumes it via a standalone MCP server
(`bin/honeycomb-mcp`) and a recall library (`lib/honeycomb/recall.py`).

The extraction works for **reads** — queens and scribes call
`palace_recall` over MCP and get content from the four-level structure.
But three connected problems remain unsolved:

### Problem 1 — Petition path is structurally broken

Today, queens emit `<<<PALACE PROPOSAL honeycomb/<wing>/<room>.md>>>`
blocks during plan/spec. Bees parses them and **applies them directly
into `bees/honeycomb/<wing>/<room>.md`** — the deprecated flat corpus.
That corpus is the in-tree fork that bees-cutover left intact only for
the static-prompt-injection path; after the planned excise it is
deleted.

Once excise lands, the petition-application path has nowhere to write.
Options considered in passing:

- **Apply petitions to `~/.honeycomb/wing_*/<room>/<closet>/closet.md`
  directly** — bees would have to translate the legacy flat path
  (`honeycomb/<wing>/<room>.md`) to the four-level closet path; mapping
  is non-trivial and lossy (one legacy room may map to multiple closets
  or none).
- **Open a PR against `viviane1016/honeycomb` per petition** —
  reasonable, but the consumer's queen does not have GitHub credentials
  to push to a repo she does not own, and the operator does not want a
  half-formed PR per petition.
- **Reject all petitions at the parse step** — operator hostility; the
  petition channel exists because consumers regularly identify real
  gaps in honeycomb content and the existing flow has been productive.

None of these compose with the agent's natural workflow ("emit a
petition during plan, carry on, see the new content reflected
eventually").

### Problem 2 — Direct-disk reads scattered across bees

`_compose_appended_prompt` in `lib/bees/honeycomb.py` reads
`closet.md` files directly from `~/.honeycomb/wing_<…>/<room>/<closet>/`.
That works post-cutover, but it bypasses the recall layer entirely.
Two consequences:

- **No queenfile awareness.** If a consumer has a pending petition
  proposing a new closet, the static-injection path will never see it —
  it reads only the on-disk canon. The queen has to manually consult
  her own queenfile to know whether her in-flight proposals affect the
  guidance she's about to follow.
- **Two access paths to maintain.** Future enhancements to recall
  (scoring metadata, content hashes, version-specific closet fallback,
  packageable selective install) have to be re-implemented in the
  direct-disk path, or the direct-disk path silently lags.

### Problem 3 — Queenfile semantics are operator-defined and informal

The queen-file (`.bees/queen.md`) holds project conventions that the
queen reads at plan/spec time. Today it is an unstructured markdown
document the operator edits by hand. It is not consulted by recall, has
no schema, and has no protocol for "this content is pending adoption by
honeycomb." Promoting it to a structured local-overlay layer requires
a contract.

## Decision

**Adopt MCP-mediated access for all honeycomb interactions, and make
the consumer's queenfile a structured overlay served by the same
recall API.**

The honeycomb MCP server gains three properties:

1. **Single API surface.** All honeycomb access — by queens, scribes,
   and the bees host process — goes through the recall library
   (`lib/honeycomb/recall.py`) or its MCP exposure. Nothing reads
   `closet.md` files directly. `_compose_appended_prompt` is rewritten
   to call `palace_recall(...)` with the same effective query targets.
2. **Queenfile-aware recall.** Each `palace_recall` query consults
   *both* the on-disk canon at `$HONEYCOMB_ROOT` *and* the consumer's
   queenfile at `$BEES_REPO_ROOT/.bees/queen.md`. Pending petitions in
   the queenfile surface in results alongside adopted content,
   indistinguishable to the caller.
3. **Petition flow via MCP tools.** Queens emit petitions through a
   new MCP tool (`palace_petition_submit`) instead of `<<<PALACE
   PROPOSAL>>>` blocks for the host to parse. The submission writes to
   the consumer's queenfile (status: pending) and optionally opens a
   PR against `viviane1016/honeycomb`. Adoption is detected
   automatically by comparing queenfile-pending entries against the
   currently-installed honeycomb version; adopted entries are removed
   from the queenfile on the next install.

### MCP tool surface (additions)

```
palace_petition_submit(
    target: str,           # e.g. "wing_bees/build/manual-amend" or
                           #      "wing_practices/test"  (room-level for new content)
    content: str,          # the proposed closet body (≤500 chars) or
                           # full closet+drawers payload
    rationale: str,        # one-paragraph why
    issue_refs: list[str], # optional GitHub issue refs
) -> { petition_id, queenfile_path }


palace_petition_list(
    status: "pending" | "adopted" | "all" = "pending",
) -> [ { petition_id, target, content, rationale,
         submitted_at, status, adopted_in_version } ]


palace_recall(
    query, wings, halls, tools, models, project, top_k, drawer,
    include_pending=True,  # NEW: default behaviour merges queenfile pending
) -> [ ... ]  # results now may carry `source: "pending" | "canon"` marker
```

### Queenfile schema (structured)

The queenfile becomes a markdown document with YAML frontmatter blocks
for petitions:

```markdown
# Project conventions for <repo>

<free-form operator notes — preserved as today>

---

## Pending honeycomb petitions

```yaml
- petition_id: 20260530-001
  target: wing_bees/build/manual-amend
  status: pending
  submitted_at: 2026-05-30T14:22:00Z
  rationale: |
    Builders frequently hit `Implements .bees/<slug>/...` typos.
    Worth a closet entry documenting the exact substring.
  issue_refs: [bees#400]
  content: |
    <closet body proposed here, ≤500 chars>
```

When the next honeycomb install pulls a release whose content matches a
pending petition (heuristic: identical target path + substantial
content overlap with canon), the install script marks that petition
adopted and removes it from the queenfile, emitting a one-line note.

### Adoption detection

Two viable heuristics:

1. **Path + content-hash match.** On install, the script computes a
   normalised hash of each pending petition's `content` field and looks
   for a matching closet at the petition's `target` path. Cheap and
   deterministic, fails when the operator subtly edits the petition
   text before adoption.
2. **PR-link tracking.** When `palace_petition_submit` opens a PR, it
   stores the PR URL in the queenfile entry. On install, the script
   queries the PR's merge state and matches by URL.

The MVP uses heuristic #1; heuristic #2 layers on as a follow-on when
the auto-PR path lands.

### `_compose_appended_prompt` migration

The function stops calling `Path.read_text` on closet files. Instead it
issues three `palace_recall` calls (room=`stage-<stage>`,
`role-<role>`, `classifier-prompt`), reads the returned closet text,
and concatenates. Same prompt shape, queenfile-aware as a side effect.

Bees imports the recall library directly (`from honeycomb.recall import
palace_recall`); no separate MCP subprocess is needed for the host
process's compose-time reads. The same library underpins the
queen/scribe MCP server.

### Bees-side excise becomes simple

With recall as the only access path, the bees-side excise feature
reduces to mechanical deletion:

- `bin/bees_honeycomb_mcp`, `lib/bees/bees_honeycomb.py`,
  `lib/bees/hc_index.py`, `tools/hc_index.py`,
  `tools/install_honeycomb.sh`, `bees/honeycomb/` — all gone.
- `_compose_appended_prompt` rewritten as described above.
- Petition parser in `lib/bees/plan.py` (`parse_palace_proposal_blocks`)
  rewritten to invoke `palace_petition_submit` instead of writing
  files. Queen prompts updated to call the MCP tool directly when
  available; legacy `<<<PALACE PROPOSAL>>>` blocks remain accepted at
  parse time for backwards compatibility for one release.
- `LEGACY_HONEYCOMB_ROOT` constant deleted; `read_honeycomb_version`
  reads from `$HONEYCOMB_ROOT/VERSION` (which is also what
  `bees --version` should report post-cutover).

## Consequences

**Positive**

- One access path. Recall-layer enhancements (scoring metadata,
  content hashes, version fallback, packaging) automatically apply
  everywhere honeycomb is consumed.
- Petitions become transparent. The queen sees her own pending
  proposals reflected in recall results immediately; she doesn't
  manage two information sources.
- Adoption is signal-driven, not poll-driven. The operator stops
  hand-checking which petitions landed.
- Queenfile gains a schema. Pending-petition entries are
  machine-parseable; operator notes remain free-form.
- Excise becomes clean. No path-translation machinery to write, no
  legacy-target fallback to maintain.

**Negative**

- Coordination overhead. Honeycomb-side ships first (with the new MCP
  tools and queenfile-aware recall) before bees-excise can wire into
  it. Bees petition handling is broken during the gap unless a stub
  rejection or staging mechanism is implemented.
- Honeycomb MCP server gains complexity. It now writes to the consumer
  filesystem (queenfile) on `palace_petition_submit`; previously it was
  read-only. Permission model needs care.
- Adoption heuristic #1 is fragile. Operator edits to a pending
  petition's text break content-hash match. PR-link tracking
  (heuristic #2) is more robust but adds the auto-PR machinery as a
  dependency.
- Queenfile schema is now a contract between honeycomb and consumers.
  Format changes become breaking changes that ripple to every consumer.

## Alternatives considered

- **Petition → direct application to `~/.honeycomb`.** Bees translates
  the legacy flat path to the four-level closet path and writes
  directly. Rejected: path translation is lossy; consumer is editing
  a separate repo's working tree without proper PR review; conflicts
  with the goal of a single API surface.

- **Petition → auto-PR against viviane1016/honeycomb at submit time.**
  Cleaner audit trail, but requires GitHub credentials in the
  consumer's queen context, requires honeycomb-side PR review
  workflow, and loses the "queen sees her own pending content
  immediately" property unless we *also* mirror to the queenfile.
  Folded in as a future option for adoption detection (heuristic #2).

- **Reject petitions entirely; operator amends honeycomb manually.**
  Hostile to operators and to queens, both of whom have used the
  petition channel productively. The cost of building MCP-mediated
  flow is bounded; the cost of removing the channel is open-ended.

- **Keep direct-disk reads in `_compose_appended_prompt`; only the
  petition flow goes through MCP.** Marginal benefit, splits the
  access model in two. Recall enhancements would have to be applied
  to both paths separately.

## Sequencing

1. **honeycomb-mcp-queenfile (this ADR's main feature):**
   - Implement `palace_petition_submit`, `palace_petition_list` MCP tools
   - Extend `lib/honeycomb/recall.py` to consume the queenfile
   - Extend `lib/honeycomb/semantic.py` similarly
   - Adoption detection (heuristic #1: content-hash match) in install
     script
   - Queenfile schema documentation + format validation
   - Ships as honeycomb v1.1.0
2. **bees-excise:**
   - Wire `_compose_appended_prompt` through `palace_recall`
   - Wire petition parser through `palace_petition_submit`
   - Delete legacy MCP infra + corpus
   - Ships as the next bees minor version

## Open questions (to resolve before status → Accepted)

1. **Queenfile location authority.** The MCP server needs
   `$BEES_REPO_ROOT/.bees/queen.md` write permission. Is this exposed
   via `BEES_REPO_ROOT` env (already passed) or via a separate
   `BEES_QUEENFILE_PATH` for flexibility?
2. **Petition target granularity.** Today's petition targets a room
   (flat). Post-MCP, does it target a *closet* (the new addressable
   unit), or stay room-level with the MCP choosing the closet?
   Closet-level is more precise but requires queens to know the
   four-level structure; room-level keeps queen prompts simple.
3. **Backwards compatibility for `<<<PALACE PROPOSAL>>>` blocks.** Do
   queens emit the new tool call directly, or do we keep the
   block-emission protocol and have bees parse + translate? One
   release of overlap, or hard cut?
4. **Adoption heuristic #1 robustness.** Operators routinely edit
   pending content; a strict hash match will mark them never-adopted.
   Loose match (token overlap > 80%) is fuzzy. Worth deferring to
   heuristic #2 (PR-link tracking) before promoting to default?
5. **Multi-consumer queenfile model.** A single MCP server may serve
   multiple consumer repos. Does each consumer have its own queenfile?
   How does the server discover them — env vars per invocation,
   registry file, prompt context?
