<!-- markdown-test-antipatterns.md: migrated from testing-discipline.md.

Hall: hall_antipattern
-->

Two anti-patterns cause agents to thrash: string-literal presence checks in `.md` files;
line-count limits on `.md` files or sections. Both drift independently of the system they
cover and become adversarial constraints. The "if you must" rule: any such test must carry a
comment explaining WHY — so future agents can judge hard-boundary vs. historical artefact.
