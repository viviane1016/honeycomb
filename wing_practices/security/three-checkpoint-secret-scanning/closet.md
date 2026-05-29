<!-- three-checkpoint-secret-scanning.md: migrated from secret-handling.md.

Hall: hall_pattern
-->

Secret handling: never log, commit, or print credentials. Apply three-checkpoint scanning: entry gate (scan untrusted input before processing), output gate (scan generated output before persisting), boundary gate (scan any artifact crossing a trust boundary). Same response at every gate: quarantine the artifact and exit non-zero. Scanned patterns: API keys (Anthropic, OpenAI, AWS, GitHub, Slack), PEM private keys.
