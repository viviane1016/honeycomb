## File and header format

Files live at `decisions/NNNN-kebab-title.md`: four-digit zero-padded counter, kebab-case slug derived from the title.

Inside the file, the H1 is `# ADR-NNNN: <title>`. Immediately below the H1:

```
**Date:** YYYY-MM-DD
**Status:** Proposed
```

Bees' own `decisions/` directory is the canonical exemplar of this convention. Other projects may choose a different directory name (e.g., `docs/decisions/`) while keeping the same `NNNN-kebab-title.md` file shape.
