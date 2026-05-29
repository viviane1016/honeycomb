## claude-haiku-4-5

### Closet

Mechanical specs only: docs-update, backlog-sweep, release-ceremony, content seeding, single-file find-and-replace. Cheapest cloud tier; struggles with multi-file reasoning or novel architecture.

### Drawer

Haiku is appropriate when the spec writes itself: the scribe's job is to copy-edit a known checklist rather than reason about design. Canonical uses:

- **docs-update** — rewriting CLAUDE.md, README, SKILL.md to match shipped behaviour.
- **backlog-sweep** — moving completed items to "shipped" in BACKLOG.md.
- **release-ceremony** — tagging, install-verification checklist, branch cleanup.
- **content seeding** — adding new honeycomb rooms with a provided template.
- **single-file find-and-replace** — renaming a constant or updating a version string.

**Warning:** Haiku can produce thin specs for anything requiring cross-file reasoning. If the mechanical spec still needs to reference three or more files or coordinate with another spec's output, use Sonnet instead. The spec content produced by Haiku still needs to be precise — a cheap scribe does not excuse a vague spec; the builder will fail if the spec is underspecified.

**Retry sensitivity:** Haiku needs the most explicit fix-only framing. Smaller models sometimes re-derive the entire response on retry rather than applying the targeted correction, producing a fresh but still-invalid output. `build_retry_prompt`'s "fix only what the error flagged" directive mitigates this, but a second failure is more likely than with Sonnet or Opus on ambiguous specs. See `wing_bees/retry-incremental-repair` and ADR-0022.
