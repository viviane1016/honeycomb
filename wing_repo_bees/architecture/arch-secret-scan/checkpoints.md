## Checkpoints

All ten call sites are listed below, grouped by stage.

### plan stage

| Artifact | Gate type | On hit |
|---|---|---|
| Briefing content | entry | Non-zero exit; no `.suspect` file written |
| `plan.md` after queen output | output | Writes `plan.md.suspect`; non-zero exit |
| `plan.md` after operator edit | output | Writes `plan.md.suspect`; non-zero exit |
| Queen-file-proposal body | extraction | Writes `queen-file-proposal.md.suspect`; continues (no exit) |
| Each petition body | extraction | Writes `<petition>.md.suspect`; continues (no exit) |

### spec stage

| Artifact | Gate type | On hit |
|---|---|---|
| Each scribe draft | output | Writes `.raw.NNN.txt`; non-zero exit |
| Queen REWRITE body | boundary | Writes `.review.raw.txt`; non-zero exit |
| Queen DEPS body | boundary | Writes `.review.raw.txt`; non-zero exit |
| Final merged spec body | boundary | Non-zero exit (no additional `.suspect` file) |

### honeycomb injection

| Artifact | Gate type | On hit |
|---|---|---|
| Queen-file content (`.bees/queen.md`) | injection | Silent skip of injection; no file written; no exit |
