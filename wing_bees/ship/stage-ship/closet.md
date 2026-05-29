<!-- stage-ship.md: migrated from stage-ship.md.

Hall: hall_procedure
tools: [github, git, pytest]
-->

The ship stage runs queen-accept (APPROVE / CONCERNS, advisory) then opens one PR per feature. PR title follows `<type>(<scope>): <imperative description>` format, derived from the plan; ≤72 chars. PR body is structured: Summary, Work, Test plan, Linked issues, Risks, optional Acceptance concerns, and footer. Recommend rebase-and-merge or merge commit — NOT squash — to preserve per-spec commit boundaries.
