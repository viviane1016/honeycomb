## Behaviour

The retro subcommand runs synchronously, reads the local event slice for a slug (or a date window with `--since`/`--window`), and aggregates findings via a detector-plugin registry (`lib/bees/retro/detectors/`). Each detector is a small module that emits `Finding` records consumed by the aggregator's `format_markdown` step. Detectors are independent and can be added without touching the core. The drone runs the same aggregator with `--cross-feature` over a release window, packages drift findings into petition blocks, and files a single PR per run (deduped by label + slug supersede comments).

### Acceptance criteria (8)

1. Per-feature `log.md` scrape for `## For the retro` sections — verbatim under a Notes heading.
2. Tag-move detection within the covered window — surfaces force-pushed release tags as a finding.
3. Hotfix-shaped commit detection — `fix(` subject within N minutes of a tag (default 60m).
4. First-attempt success rates by stage — `Scribe X/Y first-attempt`, `Builders X/Y first-attempt`.
5. Plan-Risks → Spec-body cross-reference warning — named risks not referenced in any spec body.
6. Write/read schema asymmetry — keys emitted to events.log but not consumed by status/dash/retro.
7. Stale event promotion — `_stale_stage_warning` outcomes promoted to first-class findings.
8. Output path convention — `.bees/retros/YYYY-MM-DD-<label>.md` by default.

### Briefing-handoff contract (#36)

`bees retro <slug> --md` emits a `## Proposed next-plan scope` section with three sub-headings: "Next-feature candidates" (briefing scope), "Backlog candidates" (BACKLOG.md additions), "wing_models petition candidates" (drone input). The output is shaped to be valid input for `bees plan <next-slug> -f -`, closing the loop from "feature shipped" → "next plan scope" without leaving the bees pipeline.

### Cross-feature pattern detection

`--cross-feature` enables four detectors operating on the wider event slice: (a) same `parse_error`/`fail_reason` string across ≥2 features, (b) parallel-cell FF-merge contention signals, (c) cell-leak to primary checkout, (d) chronic findings (titles recurring across `.bees/retros/*.md` with count ≥2 promoted to "chronic"). Today's session's events.log ships as a fixture exercising each.

### Drone (#160)

`.github/workflows/retro-drone.yml` runs on weekly cron (Mondays 06:00 UTC) + `workflow_dispatch`. Reads `.bees/*/plan.md` Delivery estimates, `.bees/*/log.md` stage timing, recent merged PRs. Computes estimation gaps. PRs (labelled `retro-drone`) a `wing_models/*.md` petition when divergence exceeds threshold. Two-tier authority: read-only for analysis, PR-only for petitions (no direct commits). Failure mode: cleanup-soft / PR-soft per drone contract.
