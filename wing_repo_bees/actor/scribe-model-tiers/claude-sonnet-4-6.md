## claude-sonnet-4-6

### Closet

Moderate implementation specs with bounded scope, where Opus-grade reasoning is overkill but Haiku would be thin. Tag with `[scribe:claude-sonnet-4-6, <builder-model>]` when the spec is clear, well-scoped, and has no novel architecture.

### Drawer

Sonnet is the middle tier: stronger than Haiku on multi-step reasoning and cross-file awareness, cheaper than Opus for work that does not require deep architectural reasoning. Choose Sonnet when:

- The spec involves a bounded set of changes across a small number of files.
- The work is implementing a known pattern, not inventing a new one.
- The spec content is clear enough that a lighter model won't misread it, but the implementation is non-trivial enough that Haiku risks thin output.

Cost framing: Sonnet typically runs at ~20% of Opus cost per scribe invocation. For a plan with 5 moderate units, tagging them Sonnet rather than Opus saves roughly 80% on the spec stage.

**Retry sensitivity:** Sonnet handles incremental repair reliably. The most common trigger is a missing required section; the fix-only directive resolves it in one correction pass without re-deriving unrelated content. See `wing_bees/retry-incremental-repair` and ADR-0022.
