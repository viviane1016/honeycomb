## Petition shapes

Petitions are fenced-block artifacts emitted by the queen at plan stage.

### Single-room amendment (default)

```
<<<PALACE PROPOSAL honeycomb/wing_bees/role-queen.md>>>
<terse amended room body or focused diff prose>
<<<END>>>
```

The repo-relative path must match `^honeycomb/.+\.md$` and the referenced file must exist on disk. Prefer this shape — amend an existing room when any existing room can hold the principle.

### New-room petitions

When no existing room covers the principle, the queen proposes a brand-new honeycomb room:

```
<<<PALACE PROPOSAL NEW honeycomb/wing_bees/arch-notifications.md>>>
<!-- Hall: hall_protocol Scout: 2026-01-01T00:00:00Z -->

# arch-notifications

<proposed room body>
<<<END>>>
```

Validation rules:
- Path must match `^honeycomb/.+\.md$`.
- Target file must NOT already exist on disk.
- Parent wing directory must exist.
- Body must contain a standard header comment with `Hall:` and `Scout:` substrings.

Artifact frontmatter: `kind: new-room`.

### Bundle petitions

When two or more petition constituents are coupled — partial acceptance would leave honeycomb in an inconsistent state — wrap them in a bundle:

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

Rules:
- A bundle must contain two or more constituents.
- Constituents may be amendments or new-room proposals mixed freely.
- Bundles are atomic: the operator accepts or declines the whole bundle; per-room status is not tracked.
- If any constituent fails validation, the entire bundle is rejected (stderr warning, nothing written).
- Secret-scan applies to the concatenated body; a hit writes one `.suspect` file for the whole bundle.
- Duplicate paths within a bundle are rejected by the parser.

Artifact filename: `NNN-bundle-<first-room-stem>.md`. Frontmatter uses `rooms:` (YAML list of `{path, kind}` entries) instead of `room:`.

### Optional `adr:` field

Any petition (single or bundle) may include an `adr:` field recording design-document provenance:

```
---
room: honeycomb/wing_bees/arch-notifications.md
kind: new-room
adr: docs/adr/adr-006-notifications.md
status: pending
---
```

Valid path forms: `docs/adr/<name>.md`, `decisions/<name>.md`, or `honeycomb/<wing>/adr-<name>.md`. (`decisions/` is the bees repo's own ADR home; consumer repos typically use `docs/adr/`. Both work for any repo.) The referenced file must exist on disk. The field is optional — absence is fine. Bundles carry a single `adr:` field applying to all constituents. The `adr:` field has no runtime effect; it is metadata for editorial review.
