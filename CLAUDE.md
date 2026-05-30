# Project notes

## Bees workflow

Bees is a multi-stage feature-development workflow with two human gates:
**plan approval** and **PR review**. Everything between them runs autonomously.
Full operator contract: `skills/bees/SKILL.md`.

## Briefing-prep rules

Write the briefing to `briefings/<slug>.md` before running `bees plan`.

Permitted pre-reading: `BACKLOG.md`, `RELEASE_MAP.md`.

**do NOT read** source code, GitHub issues, or honeycomb rooms — that is
the queen's job.

Briefing sections: Goal / Background / Issues table / Acceptance criteria / Constraints.

## Commands

```bash
# 1. Write briefings/<slug>.md, then kick off planning (background):
nohup bees plan <slug> -f briefings/<slug>.md > ~/.bees/<slug>-plan.log 2>&1 & disown

# 2. Mark the plan approved (foreground, near-instant):
bees approve <slug>

# 3. Launch the autonomous pipeline (background, ~600s):
nohup bees queen-orchestrate <slug> > ~/.bees/<slug>-queen.log 2>&1 & disown

# 4. Ship (orchestrator calls this; listed for reference):
bees ship <slug>
```

Two human gates only: **plan approval** and **PR review**. Do not invent extra check-ins.

## Wakeup cadences

| Stage | Cadence |
|---|---|
| Plan | ~270s (fits in the 5-min prompt-cache window) |
| Queen-orchestrate | ~600s (drives spec+dispatch+accept+ship) |
