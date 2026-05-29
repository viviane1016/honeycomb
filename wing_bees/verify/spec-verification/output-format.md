## Output format

The verifier emits exactly one block per spec it evaluates:

- `<<<APPROVE NNN>>>...<<<END APPROVE>>>` — the diff satisfies all four criteria; ff-merge proceeds.
- `<<<REJECT NNN>>>...<<<END REJECT>>>` — at least one criterion fails. The body cites the specific criterion (e.g., "Scope-file containment: diff touches `lib/foo.py` which is not listed in the spec's Scope") and gives concrete feedback for the operator or builder to act on.
