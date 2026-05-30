## Petition lifecycle

1. **Submit** — Queen calls `palace_petition_submit(target, content, rationale)`. The MCP server writes `<drawer>.queenfile_<consumer>.md` to `feat/petition-<slug>` in `$HONEYCOMB_ROOT`, opens a PR, and writes a copy to `$BEES_REPO_ROOT/.bees/honeycomb-overlay/` when that root is set.

2. **In-flight** — Status `pending`. The override is visible to `palace_recall` via the consumer overlay (immediately on submit) and as a canon PR (visible to all consumers after honeycomb maintainer merges).

3. **Adopted (PR merged)** — Honeycomb maintainer promotes the override to canonical (rewrites the base drawer, deletes the override file). The install script reads the petition manifest after `git pull` and prints a one-line summary: `Petitions: N accepted, M declined, K pending since v<prev>`.

4. **Declined (PR closed without merge)** — Override file deleted from branch. Status moves to `declined`. Consumer overlay copy remains until the next install or explicit withdrawal.

5. **Withdrawn** — `palace_petition_withdraw(path=<override-file-path>)` removes the override from the canon branch, closes the PR, and removes the local overlay copy. Status moves to `withdrawn`.

### Overlay precedence

Overlay drawer files win over canon for matching drawer paths during `palace_recall`. When no overlay is present (default bees v1.17 install, no `$BEES_REPO_ROOT` set), recall reads canon only — v1.0 behaviour is preserved.
