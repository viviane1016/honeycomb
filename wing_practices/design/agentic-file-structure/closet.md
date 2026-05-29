<!-- agentic-file-structure.md: migrated from agentic-file-structure.md.

Hall: hall_pattern
-->

Size sweet spot: 300–500 lines. Yellow zone: >800 (consider splitting before extending). Red zone: >1500 (split now). One concern per file — a file should answer one "what is this?" question. Test files mirror source structure. Parallel-builder corollary: files are the unit of concurrency in wave-parallel dispatch; disjoint files = wave-parallel safe. Prefer new focused files over extending large ones.
