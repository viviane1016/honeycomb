## claude-opus-4-7

### Closet

Default scribe tier. Reserve for architecture-heavy plans, parsers/regex, security-relevant specs, or units introducing ≥5 new public symbols. The bare `[<builder-model>]` tag form resolves to Opus at the scribe tier.

### Drawer

Opus is the default scribe tier because a richer, more complete spec lets a lighter builder tier succeed. When the scribe fully specifies types, edge cases, test structure, and commit message, the builder can focus on mechanical implementation rather than design decisions.

Escalation heuristics — use `[scribe:claude-opus-4-7, <builder>]` (or bare `[<builder>]`) when:

- **parsers or regex** — work that touches grammar, tokenisation, or pattern matching.
- **security-relevant specs** — auth, secret handling, sandbox boundaries, untrusted-input parsing.
- **≥5 new public symbols** — wide API surface where naming, signature, and contract design matter.
- **architecture-heavy plans** — novel cross-module structure or significant refactors.

The queen must cite one escalation heuristic as rationale when explicitly tagging `[scribe:claude-opus-4-7, …]`. Bare `[<builder>]` tags do not require a rationale because Opus is the default.

**Retry sensitivity:** Opus rarely reaches the retry path — first attempts typically produce well-formed output. When a retry does fire, the incremental-repair framing in `build_retry_prompt` works reliably; Opus applies the fix-only directive without re-deriving the full response. See `wing_bees/retry-incremental-repair`.
