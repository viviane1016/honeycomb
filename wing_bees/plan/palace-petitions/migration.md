## Migration: block format → MCP tool (v1.1)

### What changed

| | v1.0 (legacy) | v1.1 (current) |
|---|---|---|
| How queens petition | `<<<PALACE PROPOSAL>>>` block in plan output | `palace_petition_submit` MCP tool call |
| Where petitions land | `.bees/<slug>/petitions/` artifact files | Override file in canon feature branch + optional consumer overlay |
| Adoption path | Operator marks artifact `accepted`; queued for editorial | Honeycomb maintainer merges PR; install manifest reports adoption |
| List / withdraw | Not available | `palace_petition_list` / `palace_petition_withdraw` MCP tools |
| Self-recall of pending petition | Not available | Overlay at `$BEES_REPO_ROOT/.bees/honeycomb-overlay/` |
| Parser | `parse_palace_proposal_blocks` in `lib/bees/plan.py` | MCP server (`bin/honeycomb-mcp`) |

### Backwards-compat window (one release)

During the bees-excise release:
- Bees accepts both `<<<PALACE PROPOSAL>>>` blocks and `palace_petition_submit` MCP tool calls.
- Block-format petitions are automatically translated to `palace_petition_submit` calls at parse time.
- A one-line deprecation warning is emitted to stderr when a block is detected.
- Behaviour after translation is identical to the direct MCP tool path.

In the release **after** bees-excise:
- Block parsing is removed entirely from `parse_palace_proposal_blocks`.
- Queens that still emit `<<<PALACE PROPOSAL>>>` blocks receive no petition — the block is treated as plain text.

### Operator action required

Update queen prompts (system prompt or queen-file injection) to instruct the queen to call `palace_petition_submit` rather than emitting `<<<PALACE PROPOSAL>>>` blocks. The MCP tool is available during plan/spec stages when `bin/honeycomb-mcp` is running. The tool call produces the same outcome as the legacy block — override file written, PR opened — with the added benefit of immediate self-recall via the consumer overlay.
