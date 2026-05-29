<!-- agentic-file-headers.md: migrated from agentic-file-headers.md.

Hall: hall_protocol
languages: [python, shell, go, rust, ruby, java, kotlin, swift, c, cpp, typescript, javascript, markdown]
-->

Open every file with a header comment giving an agent quick orientation: path+role line, 2–5 sentence description, key exports (code files), ISO-8601 UTC timestamp. Use the language's comment syntax (`#` for Python/shell, `/** */` for TS/JS, `<!-- -->` for Markdown). Independent of how headers are *maintained*; bees ships one such drone-driven mechanism, see `wing_bees/scout-headers`.
