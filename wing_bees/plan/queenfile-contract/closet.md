<!-- queenfile-contract: drawer override file format, v1.1.

Hall: hall_protocol
-->

Petitions are drawer override files: `<drawer>.queenfile_<scope>.md` alongside canonical drawers. Frontmatter (HTML-comment block) declares `target`, `tool`, `tool_version`, `consumer`, and `rationale`. Filename suffix is a hint; frontmatter is authoritative. When multiple overrides match a recall context, specificity ranking selects the winner: most axes matched > version-pinned > consumer-pinned > mtime.
