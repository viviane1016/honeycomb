## Behaviour

The design actor (Opus, high effort) receives a topic — a question, a tension, a pointer to an existing design doc — and browses freely: existing ADRs, HONEYCOMB_DESIGN.md, BEES_DESIGN.md, BACKLOG, and relevant honeycomb rooms. It proposes one or more ADRs using the next available number(s) detected by globbing `decisions/`. ADRs are fenced blocks, parsed atomically, written to `decisions/XXXX-*.md` with `Status: Proposed`. The actor also proposes BACKLOG amendments and design doc updates. If the session concludes that implementation should follow, it outputs a recommended briefing for `bees plan`.

The design stage does not produce a work breakdown. That is plan's job. The boundary is: design resolves *how/whether*; plan resolves *what to build and in what order*.
