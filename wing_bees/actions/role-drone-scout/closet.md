<!-- role-drone-scout.md: migrated from role-drone-scout.md.

Hall: hall_architecture
tools: [git, gh, github-actions]
models: [haiku]
languages: [python, typescript, javascript, shell, ruby, go, rust, java, kotlin, swift, c, cpp]
-->

Scout writes AI-readable file headers (path, description, key exports, Scout: <ISO-8601 UTC> staleness tag) so queens can navigate a codebase on first contact. Two triggers: push to main (incremental direct-commit) and workflow_dispatch (full-scan PR labeled `scout`). Haiku-batched ~10 files per invocation. Bot-loop guard skips github-actions[bot] actor. `force` input regenerates all headers. Format spec in `scout-headers`.
