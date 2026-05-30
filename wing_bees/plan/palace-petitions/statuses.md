## Statuses

At emission: `status: pending`.

At PR review, the operator (or honeycomb maintainer for canon petitions) marks each petition:
- `accepted` — the override is sound; maintainer promotes it to canonical in the next honeycomb editorial release (renames/rewrites the base drawer, deletes the override file, merges PR).
- `declined` — not the right direction; PR closed, override file deleted from branch.

**Petition manifest.** After each `tools/install.sh` run that pulls new canon commits, the manifest generator classifies commits by message-prefix convention (`petition: adopted`, `petition: declined`, `petition: pending`) and prints a one-line operator summary: `Petitions: N accepted, M declined, K pending since v<prev>`. When no recognised petition commits are found, the summary notes this explicitly.

No auto-merge into canonical occurs at runtime — all promotion is via PR review by a honeycomb maintainer.
