<!-- halls-system.md: migrated from arch-halls.md.

Hall: hall_architecture
-->

Six halls partition every room by query intent: `hall_architecture` (what something IS), `hall_protocol` (contracts and templates), `hall_procedure` (steps and checklists), `hall_pattern` (engineering practices), `hall_antipattern` (known landmines), `hall_rubric` (decision tables and lookups). Encoded as `Hall: hall_<x>` in the scout-header HTML comment. Mostly assigned by filename prefix; edge cases resolved by overrides in `tools/annotate_halls.py`.
