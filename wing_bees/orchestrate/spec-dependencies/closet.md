<!-- spec-dependencies.md: migrated from dependency-graph.md.

Hall: hall_architecture
-->

Specs declare optional `depends-on: [NNN, ...]` frontmatter. Bees parses dependencies via `_build_dispatch_graph` and emits a wave schedule. The queen verifies dependencies and may emit `<<<DEPS>>>` blocks. FF-merge detects conflicts: when siblings touch overlapping files, merge fails and queen diagnoses. Humans resolve via re-dispatch (tightening deps or rebasing). Bees never auto-rebases in v1.
