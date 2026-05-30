## Behaviour

Surveyor is invoked by the queen during the retro stage, after the main retro narrative is written, when `.bees/<slug>/mcp-calls.jsonl` is non-empty.

It reads the JSONL records and analyses for the three ADR-0004 signal patterns:

- **Pattern 1 — Bloat:** high `bytes` returned, low conceptual match to the actor's downstream work. Repeated across features, this signals an oversized closet that could be trimmed or split.
- **Pattern 2 — Miss:** repeated `palace_recall` calls on the same or closely related query within a single stage. Two or more retries suggest the first result lacked the content the actor needed.
- **Pattern 3 — Prescription failure:** a recalled procedure was not followed; the actor improvised a different sequence that succeeded. Detectable from stage/actor trace when actor deviates from documented steps.

In v1.1, invocation is **manual**: the queen decides whether to invoke the surveyor based on what the retro narrative reveals. Automated correlation (signal heuristics, auto-petition emission, cross-feature aggregation) is deferred to bees BACKLOG.

**Petition emission.** Surveyor emits at most 3 petitions per retro via `palace_petition_submit`. Each petition targets a specific drawer path, carries the observed signal as rationale, and proposes concrete amendment text. Petitions that would merely speculate without a concrete logged signal are suppressed.

**Findings report.** All observations are written to `proposed-actions.md` alongside the retro output. Findings that did not cross the petition threshold appear there for operator review without opening a PR.

**Model.** Opus — same tier as the queen's retro stage. Lighter tiers risk underspecifying petition rationale or missing pattern 3 inferences that require cross-record reasoning.
