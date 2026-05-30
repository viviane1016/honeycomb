<!-- palace-petitions.md: v1.1 — block format deprecated; MCP tool is primary.

Hall: hall_protocol
-->

v1.1: Queens submit petitions via `palace_petition_submit` MCP tool. Legacy `<<<PALACE PROPOSAL>>>` fenced blocks are translated to MCP tool calls for one bees release post-excise-cutover; a deprecation warning is emitted on parse. Block parsing is removed in the following release. Petition = override file: `<drawer>.queenfile_<consumer>.md`. Statuses: pending → accepted | declined.
