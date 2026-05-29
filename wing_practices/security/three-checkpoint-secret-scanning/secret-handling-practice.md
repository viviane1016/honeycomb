## Secret-handling practice

The canonical workflow: credentials enter the system only at secure boundaries (environment variables from ops-managed secret stores, never echoed to logs). They stay in memory only for the duration they're needed. On rotation (either scheduled or emergency), ops updates the secret store, old values are forgotten, and any cached credential is invalidated. The alternative—plaintext configs, commits, or logs—is addressed in the antipattern rooms.
