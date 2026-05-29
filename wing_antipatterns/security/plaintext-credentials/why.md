## Why

Credentials in git are a mass-exploit vector. Scrapers are automated; they don't care about private vs public repos (mirrors and forks leak "private" repos immediately). The cost of storing credentials in plaintext is huge, and the benefit is tiny (convenience during development is not a benefit if it turns into a 3am incident). The alternative (environment variables, secret stores, ops-managed rotation) is not much harder: `os.environ.get("DB_PASSWORD")` is as easy as reading a file, and it's secure. Once you've seen one incident, you never commit credentials again.
