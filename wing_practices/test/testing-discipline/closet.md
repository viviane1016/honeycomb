<!-- testing-discipline.md: migrated from testing-discipline.md.

Hall: hall_pattern
-->

Write failing test first; integration tests hit real systems. Mocks rot when real systems change. Bees' subprocess paths (launching queen, scribe, builder via `claude -p`) are integration-tested, not mocked—each stage invokes the real machinery. Mocks are useful for verifying isolation and error paths, but the critical path must touch the real thing or you'll be surprised at production time.
