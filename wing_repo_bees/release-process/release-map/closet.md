<!-- release-map.md: migrated from release-map.md.

Hall: hall_procedure
tools: [github-actions]
-->

`RELEASE_MAP.md` groups unshipped BACKLOG items and open GitHub issues into upcoming release milestones, each entry carrying a one-line rationale. Maintained exclusively via cartographer-labeled PRs (never direct commits) triggered on `release: published` and `workflow_dispatch`. Multi-release races resolve by supersede comments on prior open cartographer PRs; old PRs stay open. The queen reads the map at plan time (if present) to situate a feature within the release sequence.
