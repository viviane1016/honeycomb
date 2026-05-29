## Recipe-version history

Append-only. Each entry records the recipe version, date, and what changed. Use sub-entries for dropped items.

**v1 (2026-05-25)**
Approved baked-in logic (see `## Approved baked-in logic` for full text):
- Status-table on every wakeup (#200)
- Plan → approve auto-cascade on operator approval
- FF-merge NNN surfacing in operator updates
- Wave-progress table verbatim passthrough
- Dogfood via `bees approve` + `bees queen-orchestrate` for bees-self features

**v2 (2026-05-27)**
Added `## Approved recovery sequences for known bugs` section. Three recovery recipes:
- bees#260 — spec post-check undercount on scribe-only units (7-step commit-then-restore-working-tree)
- bees#269 — verify rejects on missing Refs footer (prevention + cherry-pick recovery)
- bees#223 — orchestrator silent no-op on existing PR with concerns (manual progression, do not re-fire approve)

Discovered during scarab dogfooding 2026-05-26 → 2026-05-27 (7 colonies across parallel waves). The #260 recovery's step 6 (restore `.bees/<slug>/` from feat branch to working tree) was load-bearing and discovered only after one silent-fail re-attempt. Captured here to spare future operators that diagnostic round-trip.

This room supersedes ad-hoc workaround additions to `ScheduleWakeup` prompts. Future workarounds must be PRs against this room before they are embedded in prompts.

**v2 (2026-05-28)**
- v2 (2026-05-28): two-step approve / queen-orchestrate split — `bees approve` became a pure gate; `bees queen-orchestrate` absorbed the orchestrator launch and PID gate.
