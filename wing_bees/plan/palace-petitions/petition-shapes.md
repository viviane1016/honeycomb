## Petition shapes (legacy — deprecated in v1.1)

> **Deprecated.** As of honeycomb v1.1, queens submit petitions via the
> `palace_petition_submit` MCP tool, which writes a scope-keyed drawer
> override file (`<drawer>.queenfile_<consumer>.md`) to canon via PR.
> The `<<<PALACE PROPOSAL>>>` block format below is accepted for one bees
> release post-excise-cutover (emits a deprecation warning on parse).
> Block parsing is removed in the following release.
>
> See `wing_bees/plan/petitions-flow` for the current v1.1 flow.

### Single-room amendment (legacy)

```
<<<PALACE PROPOSAL honeycomb/wing_bees/role-queen.md>>>
<terse amended room body or focused diff prose>
<<<END>>>
```

Path must match `^honeycomb/.+\.md$`; file must exist on disk. Parser translates to a `palace_petition_submit` call; behaviour is identical post-translation.

### New-room petition (legacy)

```
<<<PALACE PROPOSAL NEW honeycomb/wing_bees/arch-notifications.md>>>
<!-- Hall: hall_protocol Scout: 2026-01-01T00:00:00Z -->
# arch-notifications
<proposed room body>
<<<END>>>
```

Target file must NOT already exist; parent wing directory must exist.

### Bundle petition (legacy)

```
<<<PALACE PROPOSAL BUNDLE>>>
<<<PALACE PROPOSAL honeycomb/wing_bees/arch-foo.md>>>
<amendment body>
<<<END>>>
<<<PALACE PROPOSAL NEW honeycomb/wing_bees/arch-bar.md>>>
<!-- Hall: hall_protocol Scout: 2026-01-01T00:00:00Z -->
<new-room body>
<<<END>>>
<<<END BUNDLE>>>
```

Bundles are atomic (accepted or declined as a whole). Duplicate paths within a bundle are rejected by the parser.

### Optional `adr:` field

Any petition may include an `adr:` field in frontmatter recording design-document provenance. Valid path forms: `docs/adr/<name>.md`, `decisions/<name>.md`, `honeycomb/<wing>/adr-<name>.md`. The referenced file must exist. Metadata only; no runtime effect.
