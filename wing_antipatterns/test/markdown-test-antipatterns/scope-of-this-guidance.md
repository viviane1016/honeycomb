## Scope of this guidance

These patterns are most acute for tests on:

- Honeycomb room content (`.md` files in `honeycomb/`)
- Plan and briefing output (`.bees/<slug>/plan.md`, `briefing.md`)
- Starter scaffold files (`CLAUDE.md`, `SKILL.md`, `ONBOARDING.md`)
- Generated workflow files (`.github/workflows/*.yml`)

They are less likely to cause problems for tests on:
- Pure logic functions with stable contracts
- Binary format parsers
- Network protocol handlers

The sapper drone (see `role-drone-sapper`) is instructed to skip proposing string-literal
or line-count tests for `.md` files. If the sapper proposes such a test, treat it as a
signal that the underlying concern needs a better expression, not that the test is
acceptable with a raised threshold.
