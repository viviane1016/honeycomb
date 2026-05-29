<!-- rework-at-pr.md: migrated from rework-at-pr.md.

Hall: hall_procedure
tools: [bees, git]
-->

When a feature has already been dispatched (builder commits on `feat/<slug>`),
closing the PR and re-dispatching will silently re-use old builder output. Old
commits leave NNN markers that match new spec numbers. Strip old builder commits
from the branch before re-dispatching, or the new spec files run but their
implementations never land. (~490 chars)
