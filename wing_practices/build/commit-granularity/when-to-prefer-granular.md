## When to prefer granular

- Multi-file features where logically-distinct pieces could ship in different orders (taxonomy, script, parser, tests, docs).
- Anything where reverting *part* of the change is plausible (a misbehaving doc edit, a broken test, an over-ambitious refactor).
- Long-running branches where you may need to bisect later to find which step regressed something.
- Operator-reviewed branches (most bees feature branches): the operator reads `git log` to understand the work, not just the final diff.
