## Why exactly two gates

The two-gate model trades throughput for control:

- More gates = more interruptions = lower autonomy.
- Fewer gates = higher risk of unwanted output.

Plan approval is the cheapest place to catch fundamental misdirection before expensive spec and build work. PR review is the natural point to verify outcomes — the full context (plan, specs, commits) is available. This aligns with the natural decision points: intent (plan) and outcome (PR).

The reflection-stage third gate complements rather than amends this. Non-git actions have no PR-level rollback; per-action approval keeps the operator in control where it matters most.
