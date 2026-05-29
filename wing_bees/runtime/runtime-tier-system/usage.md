## Usage

Skill content (honeycomb, design docs) never names concrete models — it references tiers. This keeps bees portable across operators with different deployments (cloud-only, local-only, hybrid). When a spec runs, bees resolves its tier to the configured model, either locally or in the cloud. MCP servers extend capabilities; plan and spec stages run with read-only tools only, while builder bees get access to edit, commit, and test. The allowlist prevents accidental `pip install`, `git push`, or other destructive commands; it's a safety constraint, not a limitation to work around.
