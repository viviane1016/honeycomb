## Multi-release race handling

When a new release fires before the operator has reviewed the prior cartographer PR, the cartographer detects open PRs carrying the `cartographer` label and posts a supersede comment on each one. The comment names the new PR number and the old commit SHA so the reviewer knows where the current analysis lives.

Prior open cartographer PRs are **not** auto-closed — operator agency is preserved, and any in-flight review comments on the older PR remain accessible. The new PR is opened with the `cartographer` label applied at creation time.

See `role-drone-cartographer` for the exact supersede-comment wording and the step-by-step order of operations.
