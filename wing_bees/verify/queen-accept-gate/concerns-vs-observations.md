## Concerns vs observations

**Concerns** are blocking-grade issues — items the operator must address if they intend the feature to behave as specified. The queen formats each concern as a numbered list item, citing the plan or spec section it references (e.g., `## Acceptance bullet 3`, `spec 003 ## Success check`). Concerns appear under the `CONCERNS` heading.

**Observations** are advisory-grade notes — items the operator may act on or ignore without breaking the feature contract (e.g., a minor naming inconsistency, an opportunity to tighten test coverage). Observations, when present, appear under a separate `## Observations` heading in the concerns file.

Both concerns and observations are non-blocking from bees' perspective; the distinction signals severity to the operator.
