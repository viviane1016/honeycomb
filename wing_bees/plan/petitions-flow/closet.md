<!-- petitions-flow: MCP tool petition flow, v1.1.

Hall: hall_protocol
-->

Queens submit honeycomb change requests via `palace_petition_submit` MCP tool — writes a scope-keyed drawer override file to a feature branch in canon, opens a GitHub PR, and mirrors to a consumer overlay for immediate self-recall during the PR window. Adoption = PR merge; rejection = PR close. `palace_petition_list` lists in-flight petitions; `palace_petition_withdraw` removes a petition and closes its PR.
