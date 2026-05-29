## V-model practice

The V-model hierarchy ensures verification happens at the level closest to where the requirement was authored. When a queen writes a plan from the briefing, only the queen can verify whether the colony's implementation honours the briefing's intent—not just the plan's text. Similarly, when a scribe writes a spec, they alone understand the architectural choices baked into that spec. The builder who writes code understands the failing test they pinned it against. Each author-verifier compares the diff not just against literal specifications but against *why* those specifications were written.

The bees mapping follows this pattern across three levels:

- **Briefing / plan ↔ queen accept** — The queen authors the plan from the operator's briefing, distilling intent into work breakdown. At ship time, the queen reads the annotated briefing (with any operator amendments), the plan, all scribe specs, and the full feature diff to decide APPROVE (merged as-is, fulfils the briefing) or CONCERNS (deviation from intent, needs operator review before merge).

- **Spec ↔ scribe verify** — The scribe authors the spec, packaging the queen's plan into a self-contained unit. At the end of the build stage, the same scribe reads the spec and the builder's git diff. They decide APPROVE (builder did what the spec asked) or REJECT (builder misunderstood the intent, or the diff misses the point even if it matches the literal requirement).

- **Code ↔ builder tests** — The builder writes the code and (per `testing-discipline`) the failing test that pins the behaviour before the implementation. Tests run inside the cell before commit, exercising the code under the contract the test enforces.
