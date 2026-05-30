## Parser and emitter (v1.1)

### v1.1 path (primary)

`palace_petition_submit` MCP tool is the direct submission path from honeycomb v1.1. The MCP server (`bin/honeycomb-mcp`) writes the override file, opens the PR via `gh`, and returns `{petition_id, branch, pr_url}`. No client-side parsing required. See `wing_bees/plan/petitions-flow/mcp-tool-emission` for full tool contracts.

### Legacy translation path (one-release backwards-compat window)

`parse_palace_proposal_blocks` in `lib/bees/plan.py` still scans queen output for `<<<PALACE PROPOSAL>>>` blocks during the bees-excise cutover release. On detection:

1. Emits a one-line deprecation warning to stderr: `[petition] <<<PALACE PROPOSAL>>> blocks deprecated — update queen prompts to call palace_petition_submit`.
2. Translates each block to a `palace_petition_submit` call. Behaviour is identical post-translation.
3. Writes artifact to `.bees/<slug>/petitions/` (same layout as v1.0 for operator familiarity).

Block parsing is removed in the release **following** bees-excise. Queens must use the MCP tool.

### Artifacts (legacy format)

`.bees/<slug>/petitions/NNN-<room-basename>.md` (single petition), `NNN-bundle-<first-room-stem>.md` (bundle). Secret-pattern scan applies to the full body before writing; a hit writes `<filename>.suspect` and flags on stderr.
