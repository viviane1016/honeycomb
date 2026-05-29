## File targeting

These rules live in this room — not hardcoded in the workflow — so they can evolve via a honeycomb edit without a code deployment.

- **Walk the repo**, respecting `.gitignore`.
- **Include source extensions:** `.py`, `.ts`, `.js`, `.mjs`, `.sh`, `.rb`, `.go`, `.rs`, `.java`, `.kt`, `.swift`, `.c`, `.cpp`, `.h`
- **Include repo docs:** `CLAUDE.md`, `README.md`.
- **Exclude honeycomb:** `honeycomb/**/*.md` files are intentionally excluded. Queens navigate honeycomb via hall taxonomy (`arch-halls`) and semantic recall (`arch-palace-recall`), not scout headers. Refreshing timestamps on rarely-changing honeycomb files also churns the inlined copies of role docs in drone workflow ymls (see `tools/build_drone_yml.py`). Honeycomb files keep their existing `<!-- ... Hall: ... -->` comment blocks — those are read by the recall system — but scout does not refresh them.
- **Exclude directories:** `node_modules/`, `dist/`, `build/`, `vendor/`, `__pycache__/`, `.venv/`, `.bees/` (transient artefacts, not source).
- **Exclude generated files:** files whose first five lines contain a `# generated`, `# DO NOT EDIT`, or `// Code generated` marker.
- **Exclude test files:** `test_*.py`, `*_test.py`, `*.test.ts`, `*.spec.ts` — test files are self-documenting by intent.
- **Skip tiny files:** fewer than 20 lines — not worth the token cost.
