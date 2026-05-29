<!-- slug-naming.md: migrated from slug-naming.md.

Hall: hall_protocol
-->

Bees slugs: lowercase letters, digits, and hyphens only; ≤100 chars. Describe the work, not the implementation. Type prefix clarifies intent: `feat/`, `fix/`, `refactor/`. Good: `oauth-login`, `dashboard-sse-leak`, `queen-prompt-trimming`. Bad: `john-branch`, `wip`, `temp`. The CLI rejects slugs containing path-traversal sequences or disallowed characters at the parser boundary, before any filesystem or git work begins.
