<!-- palace-petitions.md: migrated from petitions-format.md.

Hall: hall_protocol
tools: [parse_palace_proposal_blocks, secret-scan]
languages: [python]
-->

Amendment: `<<<PALACE PROPOSAL honeycomb/<wing>/<room>.md>>>…<<<END>>>` (path must exist). New-room: `<<<PALACE PROPOSAL NEW honeycomb/<wing>/<room>.md>>>…<<<END>>>` (path must NOT exist; parent wing dir must exist). Bundle: `<<<PALACE PROPOSAL BUNDLE>>>…<<<END BUNDLE>>>` (≥2 inner blocks, atomic). All shapes: optional `adr: docs/adr/<path>`. Status: `pending`→`accepted`|`declined`. Artifacts: `NNN-<room>.md` / `NNN-bundle-<stem>.md`. Parser: `parse_palace_proposal_blocks` in `lib/bees/plan.py`.
