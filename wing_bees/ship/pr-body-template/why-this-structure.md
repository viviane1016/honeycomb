## Why this structure

**Summary + context** — reviewers understand what and why before reading code.

**Specs list** — each builder commit references its spec; the PR body makes the spec files directly accessible so reviewers can audit the work breakdown.

**Test plan** — verification approach is explicit, not hidden in the test diff.

**Linked issues** — GitHub auto-closes issues when the PR merges, and the PR body documents which issues are affected.

**Risks** — tradeoffs and dependencies bubble up from the plan into the review conversation.

**Links to plan and trace** — context-depth without bloating the PR body. A reviewer curious about the original briefing or what rooms were consulted can follow the links.
