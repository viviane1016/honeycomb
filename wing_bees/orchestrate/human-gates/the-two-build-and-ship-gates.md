## The two build-and-ship gates

Per ADR-0005, bees pauses at exactly two points in the main pipeline:

1. **Plan approval** — After the queen produces `plan.md`, the operator reviews and approves before any spec or build work begins. The operator is answering: "are we building the right thing?"
2. **PR review** — After all specs have been built and merged into `feat/<slug>`, bees opens a PR. The operator reviews before merge. They are answering: "is what shipped acceptable?"

Everything between (spec, dispatch, ship) runs autonomously. No gate between spec and dispatch. No gate between dispatch and ship.
