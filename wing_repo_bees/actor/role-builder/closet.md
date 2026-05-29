<!-- role-builder.md: migrated from role-builder.md.

Hall: hall_architecture
tools: [git, pytest]
-->

The builder reads a spec, implements it, commits to the cell branch, and exits. Model tier is chosen per-spec. Builders have access to Read/Grep/Glob/Edit/Write, narrowed git, and `python3 -m pytest`; no pip install, push, or config. Exit via `.bees-builder-note.md` if the spec is ambiguous. Before extending a file, check its line count — if it exceeds ~500 lines and the spec doesn't require that file, prefer a new focused module instead.
