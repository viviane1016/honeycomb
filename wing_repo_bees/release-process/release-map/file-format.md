## File format

`RELEASE_MAP.md` lives at the repo root. It is a Markdown file with:

- An introductory paragraph noting that items are proposals (not commitments) and identifying the cartographer as maintainer.
- `##` headings for each release group, optionally carrying a descriptive subtitle — e.g., `## v1.2 — Retro + queen feedback loop`.
- `-` bulleted items under each heading. Each bullet identifies the item (GitHub issue `#NNN` or BACKLOG text) and carries an inline one-line rationale explaining why it belongs to that release.
- An optional `## Unscoped / awaiting design` section for items in RFC or awaiting an architectural decision.
- A `## Rationale notes` section at the end, where the cartographer records its run context (trigger event, tag state, issues closed this run, triage flags).

The file is rebuilt from scratch on every cartographer run. `BACKLOG.md` is the authoritative historical record; `RELEASE_MAP.md` is the synthesis derived from `BACKLOG.md` and the open issue tracker.
