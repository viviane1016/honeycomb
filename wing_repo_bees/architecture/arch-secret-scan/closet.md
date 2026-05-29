<!-- arch-secret-scan.md: migrated from arch-secret-scan.md.

Hall: hall_architecture
languages: [python]
-->

Bees applies `scan_for_secrets` (`lib/secrets.py`) at every stage where content is persisted. Entry: briefing before the queen (non-zero exit on hit). Output: plan.md after queen (.suspect + exit); scribe drafts (.raw.NNN.txt + exit); queen REWRITE/DEPS bodies (.review.raw.txt + exit); final merged specs (exit). Extraction: queen-file-proposal and petition bodies write .suspect but continue. Queen-file injection skips silently. See `wing_practices/secret-handling` for the checkpoint model.
