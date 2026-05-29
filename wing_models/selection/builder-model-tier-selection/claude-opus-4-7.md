## claude-opus-4-7

### Closet

Best for high-stakes specs touching parsers, regex, or cross-cutting refactors; highest unit cost; reserve for ≥1 of: novel architecture, public API change, security-relevant code.

### Drawer

Scribes already run Opus universally, so the cost is justified when the spec touches parsers, regex, or cross-cutting refactors. Most plans don't need Opus builders, but when they do, the cost is worth it for the reliability and depth of reasoning Opus brings to complex architectural work.

Use the following escalation heuristics to decide when `[claude-opus-4-7]` is warranted:

- **parsers or regex** — work that touches grammar, tokenisation, or pattern matching where edge cases bite hard.
- **cross-file refactor** — coordinated edits across more than one module that must stay consistent.
- **≥5 new public symbols** — a wide API surface where naming, signature, and contract design matter.
- **≥3 new tables** — schema design with foreign-key and migration considerations.
- **security-relevant code** — auth, secret handling, sandbox boundaries, untrusted-input parsing.
- **cross-language integration** — edits that span Python, shell, JS, SQL, or template DSLs.

The queen must cite one of these escalation heuristics as a one-sentence rationale in any plan that tags a unit `[claude-opus-4-7]`.
