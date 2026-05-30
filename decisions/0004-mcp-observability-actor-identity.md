# ADR-0004: MCP-side observability + actor-identity logging

**Date:** 2026-05-30
**Status:** Proposed

## Context

ADR-0001 establishes MCP-mediated access as the single API surface
for honeycomb. ADR-0002 introduces drawer overrides with scoped
resolution. ADR-0003 adds honey packs.

What none of these address: **how do we know if honeycomb is doing a
good job?**

The palace is curated content. Curators (honeycomb maintainers, honey
pack maintainers, consumer queens via petitions) make assumptions
about what content actors need, how much depth, what shape. Those
assumptions are wrong in three known patterns:

### Pattern 1 — Bloat (cheap-to-detect, statistical)

A closet ships 1.2KB of content, but the actor consuming the result
typically uses ~300 bytes of it. Repeated across many features, this
shows the closet is oversized for actual use. Splitting / trimming
opportunities.

> "I wanted this one line, you sent me 100."

### Pattern 2 — Miss (cheap-to-detect, per-use)

The actor recalls, gets results, doesn't find what they need, calls
recall again with a refined query. Or worse: enters a recovery loop
and never finds the right content. Each retry costs tokens and time.

> "I asked twice; the second query worked. The first was wasted."

### Pattern 3 — Prescription failure (expensive-to-detect, highest-leverage)

The actor recalls procedural guidance, follows the prescribed steps,
they fail. The actor improvises a different sequence; it works. The
documented procedure is wrong or incomplete; the working procedure
isn't yet captured anywhere.

> "You told me to try this recovery protocol, it sucked, I did this."

These patterns can only be detected by observing what happens **after**
the recall returns — what the actor used, what failed, what worked
in the end. The MCP server alone can't see this; only the consumer
tool (bees) has the full picture of actor outcomes.

But the MCP server is where the data is **born**. Without
actor-identity propagation and per-call logging at the MCP layer, the
consumer-side correlation has nothing to correlate against.

## Decision

**Honeycomb MCP server v1.1 logs every recall call with actor
identity propagated via env. Consumer (bees) correlates the log with
actor outcomes to detect the three signal patterns and feed them into
the retro stage.**

This ADR captures the honeycomb-side contract — env vars, log schema,
log destination. The consumer-side analysis (correlation, signal
heuristics, retro-petition emission) lives in a parallel
BACKLOG/feature on the bees side.

### 1. Env contract — actor identity propagation

The honeycomb MCP server reads four env vars at invocation:

```
BEES_FEATURE_SLUG    # already set per ADR-0001 — the in-flight feature
BEES_REPO_ROOT       # already set per ADR-0001 — consumer repo root
BEES_ACTOR           # NEW — "queen" | "scribe" | "builder" | "drone-<name>"
BEES_STAGE           # NEW — "plan" | "spec" | "dispatch" | "verify" | "accept" | "ship" | "retro" | "debug"
BEES_MODEL           # NEW — model identifier (e.g. "claude-sonnet-4-7")
```

Missing actor / stage / model is non-fatal (logged as `unknown`), but
the bees harness is expected to set them for every spawn. The MCP
server does not validate the values against an allowlist — that would
couple honeycomb to the bees actor taxonomy. The values are opaque
labels.

### 2. Per-call log schema

Every `palace_recall` call (and any future tool that returns content)
emits a JSONL record:

```jsonl
{
  "ts": "2026-05-30T14:22:00.123Z",
  "tool": "palace_recall",
  "slug": "honeycomb-cutover",
  "actor": "queen",
  "stage": "plan",
  "model": "claude-sonnet-4-7",
  "request": {
    "query": "manual amend",
    "wings": ["wing_bees"],
    "halls": ["hall_procedure"],
    "tools": null,
    "models": null,
    "top_k": 3,
    "drawer": false,
    "engine": "semantic"
  },
  "response": {
    "result_count": 2,
    "results": [
      {
        "wing": "wing_bees",
        "room": "build",
        "closet": "manual-amend",
        "drawer": null,
        "bytes": 1248,
        "score": 0.87,
        "source": "canon",
        "content_sha": "ab12cd34..."
      },
      {
        "wing": "wing_bees",
        "room": "orchestrate",
        "closet": "manual-amend",
        "drawer": null,
        "bytes": 980,
        "score": 0.71,
        "source": "canon",
        "content_sha": "ef56gh78..."
      }
    ],
    "fallback_engine": null
  },
  "duration_ms": 42
}
```

Key properties:

- **One record per call**, not per result. Results are an array
  inside the record.
- **`bytes` is the rendered bytes of the closet + drawers returned**
  (what the actor saw), not the raw file size.
- **`content_sha` is the hash of the returned content.** Lets bees
  correlate "this returned content" with "this content showed up in
  actor's output" even if the closet path is consistent.
- **`source`** marks where the content came from — `canon`, a honey
  pack (`honey-gemma-4@2.1.0`), or `consumer-overlay` (per ADR-0001
  / ADR-0002).

### 3. Log destination

Records are written to:

```
$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl
```

Per-feature, append-only, owned by the consumer repo. Bees harness
reads it during retro to correlate with actor transcripts and
outcomes.

If `BEES_REPO_ROOT` or `BEES_FEATURE_SLUG` is unset (e.g. dev-mode
MCP server invocation outside a bees stage), records fall through to:

```
$HONEYCOMB_ROOT/.calls.jsonl
```

A best-effort dev log. Not consumed by anything in production; useful
for honeycomb development.

### 4. Write semantics

- **Synchronous append**. Each record is `flush()`-ed before the MCP
  response returns. Cheap (single line of JSONL); guarantees the log
  is durable even if the actor subprocess crashes mid-recall.
- **No rotation at the MCP layer.** Per-feature logs are small (most
  stages do <50 recall calls). Cross-feature rollup is the consumer's
  problem (the existing `bees retro --cross-feature` rolls up events;
  extend it to roll up recall traces).
- **No redaction at the MCP layer.** The MCP server logs what was
  requested and returned. Queries are operator-emitted prompts in
  natural language — no PII per se, but operators may want a redact
  hook. BACKLOG.

### 5. What this enables (consumer-side, BACKLOG)

With this contract in place, the bees harness can:

- Read `mcp-calls.jsonl` after each stage
- Cross-reference `content_sha` against the actor's output transcript
  to measure **used vs returned bytes**
- Detect **recurrence patterns** — same query in one stage means the
  first answer didn't land
- Detect **prescription failure** — when a procedural closet was
  returned, the actor tried its steps, those failed, and the actor's
  eventual successful path diverged

The retro stage queen runs these heuristics and emits retro petitions
proposing closet trims, splits, content corrections, or new content
where the existing palace fell short.

This consumer-side work is its own substantial feature; it depends
on the MCP-side log being present and stable. ADR-0004 commits to
the contract; the bees-side feature consumes it.

## Consequences

**Positive**

- **Minimal new MCP server work.** Read four env vars, write a JSONL
  record per call. ~50 lines of honeycomb-library code.
- **Unblocks the entire feedback loop.** Bees-side analysis +
  retro-petition emission has structured data to consume.
- **Identity opacity preserves decoupling.** Honeycomb doesn't know
  what a "scribe" is or what "spec" means — labels flow through
  unmodified. Future tools using honeycomb pass their own labels.
- **Content-sha enables cross-stage analysis.** The same closet text,
  served from different sources (canon then later from an overlay),
  can be detected as "actually the same thing."

**Negative**

- **Disk write per call** — synchronous flush adds latency. Measured
  cost: ~5-10ms for a JSONL line on SSD. Acceptable for typical
  recall calls (which already take 30-300ms).
- **Logs accumulate.** Per-feature logs are small but cross-feature
  rollup will need pruning. Bees-side concern.
- **No on-by-default privacy story.** Queries and returned content
  go to disk in cleartext. For local-only operation this is fine;
  for shared environments, the redact hook BACKLOG'd above becomes
  load-bearing.

## Alternatives considered

- **MCP server logs to stderr; bees captures the stream.** Avoids a
  separate log file but ties bees subprocess management more tightly
  to MCP output parsing. Rejected: harder to correlate; harder to
  query post-hoc.

- **Bees instruments by wrapping the recall call at the harness
  layer.** Avoids the MCP-side change. Rejected: bees would have to
  re-implement what the MCP server already knows about
  result-shaping; the duplicate logic drifts.

- **No actor-identity propagation; bees joins by ts + slug only.**
  Rejected: when a single feature has many concurrent actors (e.g.
  parallel scribe spawns), join-by-timestamp is fragile and actor
  attribution gets lost.

- **Defer all observability to v1.2.** Rejected: the feedback loop is
  the mechanism that drives palace tuning. Shipping v1.1 (override
  + petition + scope) without observability means the petitions will
  be operator-guess instead of data-grounded for the first window.
  Cheap to add now; expensive to retrofit.

## Sequencing

Ships in honeycomb v1.1 alongside ADR-0001 + ADR-0002. Adds:

- **Env contract** documentation in honeycomb library
- **Log writer** in the MCP server (~50 LOC)
- **Log schema** versioned via a `schema_version` field on each
  record (initial v1)
- **`tools/honeycomb-calls.sh`** — small utility to tail / pretty-print
  recent calls for honeycomb-side debugging

Consumer-side (bees) follows separately as its own BACKLOG item /
feature.

## Open questions

1. **Schema versioning policy.** Bumping schema_version is a breaking
   change for any tooling consuming the log. Major-version-only, or
   per-field additive with a manifest of changes?

2. **Honey pack source identification.** When content comes from a
   honey pack, source field is `honey-<name>@<version>`. Should
   honeycomb maintain a content-sha → source map in case packs
   rev-bump silently? Probably out of scope for v1.1; revisit when
   honey packs ship (v1.2).

3. **Multi-MCP concurrent writes.** If two bees subprocesses
   (different actors, same feature) call recall simultaneously, both
   MCP server instances write to the same `mcp-calls.jsonl`. Append
   semantics on POSIX are atomic for small writes (<PIPE_BUF), but
   JSONL records may exceed that. Use file locking, or rely on per-
   subprocess locking already in place for `.bees/<slug>/log.md`?

4. **Cost-tracking integration.** The bees `bees status` cost-tracking
   already aggregates token spend per stage. Should the MCP-call log
   carry an estimated cost field too, or stay neutral and let bees
   compute on its side from token counts?

5. **Redaction hook.** Operators in shared environments may need to
   exclude certain content from logs (sensitive queries, proprietary
   content from honey packs). Plugin point at write time? BACKLOG;
   not a v1.1 requirement.
