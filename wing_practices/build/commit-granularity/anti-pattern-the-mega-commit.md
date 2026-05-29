## Anti-pattern: the mega-commit

A single commit that adds a new module, annotates 67 existing files, changes a parser, extends an MCP descriptor, adds tests, updates 3 docs, bumps a version, and regenerates a workflow yaml. Even if every change is correct, the diff is unreviewable and a partial revert is impossible. Split it.
