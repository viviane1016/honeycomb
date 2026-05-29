## Behaviour

Honeycomb ships with bees and is read-only at runtime. No bees process writes to honeycomb; all updates happen offline by editing `~/claude/bees/honeycomb/`, opened as PRs against the bees repo, and released with the next honeycomb version. The queen and scribe call `palace_recall(query, wings, top_k, drawer=False)` within their own instances to fetch rooms. The queen self-classifies briefings (using classifier guidance that ships with honeycomb), determines what rooms she needs, and recalls them. Recalls log to `.bees/<slug>/honeycomb-trace.md` for auditing and reuse by the scribe.

Honeycomb's wing structure:
- `wing_bees` — operational knowledge about bees itself (stages, roles, architecture). Always-injected at relevant stages.
- `wing_practices` — engineering patterns and antipatterns for system design and implementation.
- `wing_tools` — tool-specific best practices (git, GitHub, CLI, etc.).
- `wing_models` — model-keyed observed-rate rubric for scribe and builder tier decisions.
- `wing_roadmap` — deferred content (features not yet implemented in bees).

Tunnels (cross-wing links via shared room names) are planned for mempalace integration; today rooms are flat markdown files cross-linked via `## See also`. See ADR-0009 for vocabulary discipline as a primary curation concern.

See ADR-0006 for why honeycomb is read-only, ADR-0008 for versioning, ADR-0013 for wing consolidation, ADR-0014 for queen-driven recall, and ADR-0018 for flat-file storage.

**Schema versioning.** `lib/honeycomb.py` declares `HONEYCOMB_SCHEMA = 2` to detect schema changes. Schema 2 covers multi-keyed rooms — rooms with one or more `## <model-id>` sub-sections, each carrying `### Closet` + `### Drawer`. Honeycomb releases are independent of bees binary releases; a bees patch bump may carry only honeycomb updates.
