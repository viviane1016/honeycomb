## Guidance

`CONCERNS` is advisory. The operator decides the response. Three paths are available:

1. **Address concerns and re-dispatch.** Fix the underlying issue (re-dispatch the affected spec, or patch by hand), then re-run the accept gate to verify the concern is resolved.
2. **Patch by hand and re-run accept.** Implement the fix directly, commit to the feature branch, and invoke the accept gate to re-evaluate before shipping.
3. **Override and ship anyway.** The operator ships despite outstanding concerns. The concerns file (`.bees/<slug>/accept-concerns.md`) is attached to the PR body, so the human reviewer sees the queen's assessment and can make an informed decision at merge time.

The human PR-review gate remains on top. Queen-accept does not replace it. A `CONCERNS` verdict followed by an operator override simply means the operator judged the concerns acceptable — the PR reviewer still decides whether to merge.
