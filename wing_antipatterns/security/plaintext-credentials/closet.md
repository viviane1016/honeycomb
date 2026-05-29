<!-- plaintext-credentials.md: migrated from antipattern-plaintext-credentials.md.

Hall: hall_antipattern
tools: [git, aws]
-->

Never store credentials in plaintext files committed to git. The failure mode: AWS keys in `.env` checked into a public repo; key-scraper finds them hours later; cloud costs spike to $50k in a day. The alternative: ops manages secrets in a secure store (HashiCorp Vault, AWS Secrets Manager, 1Password); applications read them from environment variables at runtime, never printed to logs or config files.
