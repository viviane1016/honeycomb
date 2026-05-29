## Scan architecture

`scan_for_secrets` is defined in `lib/secrets.py` alongside the `SECRET_PATTERNS` list. It returns a list of matched label strings; an empty list means clean. It is imported and called by `lib/plan.py`, `lib/spec.py`, and `lib/honeycomb.py`.

The three-checkpoint model (`wing_practices/secret-handling`) maps onto the bees pipeline as follows:

- **Entry gate** — applied to untrusted external input before it reaches any LLM (briefing content at plan entry).
- **Output gate** — applied to LLM-generated output before it is written to disk (`plan.md`, scribe drafts, queen REWRITE/DEPS bodies, final merged specs).
- **Extraction gate** — applied to structured blocks extracted from LLM output that become secondary artefacts (queen-file-proposal, petition bodies). A hit here writes a `.suspect` file but does not abort the surrounding stage.
- **Injection gate** — applied to content about to be injected into a subsequent LLM context (queen-file content). A hit here silently skips the injection with no file written and no exit.
