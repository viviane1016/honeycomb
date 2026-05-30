## Override file format

Override files are placed alongside the canonical drawer in the same closet directory. The filename pattern is `<drawer-name>.queenfile_<tag>.md`. Example tree:

```
wing_bees/build/manual-amend/
  behaviour.md                                    # canonical
  behaviour.queenfile_bees-v1.18.md               # override for bees >=v1.18
  behaviour.queenfile_scarab.md                   # override for scarab consumer
  guidance.md
  guidance.queenfile_bees-v1.18.md
```

Multiple overrides on the same canonical drawer coexist when their tags differ.

### Frontmatter schema

An HTML-comment block at the top of the override file is authoritative; the filename tag is a hint only:

```markdown
<!-- behaviour.queenfile_bees-v1.18.md: bees v1.18 override.

target: behaviour
tool: bees
tool_version: ">=v1.18"
consumer: null
rationale: |
  v1.18 introduces the scoped recall context. Builders need to pass
  tool_version through queries; spec contract documents this.
-->
```

### Fields

| Field | Required | Description |
|---|---|---|
| `target` | yes | Canonical drawer name (without extension) |
| `tool` | no | Tool identifier (e.g. `bees`) or `null` for any tool |
| `tool_version` | no | Version constraint: exact `==v1.18` or range `>=v1.18`, or `null` |
| `consumer` | no | Consumer name (e.g. `scarab`) or `null` for any consumer |
| `rationale` | yes | Free-form explanation; used in PR body when submitting via MCP tool |

All four targeting fields may be `null` — that is a valid "always override" case, lowest specificity.
