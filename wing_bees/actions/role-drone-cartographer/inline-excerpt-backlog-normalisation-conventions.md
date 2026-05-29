## Inline excerpt: BACKLOG normalisation conventions

The cartographer normalises `BACKLOG.md` to the conventions already in use in the file. The current style:

- Release groupings use `##` headings, optionally with a status suffix such as `(shipped YYYY-MM-DD)` or `(target: after X retro)`.
- Sub-clusters within a release use `###` headings.
- Items are `-` bulleted under their target release heading.
- Shipped items are struck with surrounding `~~` and annotated with `**Shipped YYYY-MM-DD.**` immediately after the strike, in one of the equivalent forms already attested in the file:
  - `- ~~**item title**~~ **Shipped YYYY-MM-DD.**` followed by rationale text.
  - `- ~~**item title.**~~ **Shipped YYYY-MM-DD.**` followed by rationale text.
- Rationale text under a struck item is retained verbatim, so the BACKLOG reads as a historical record rather than a moving target.
- Items deferred or reordered keep their rationale and gain a parenthetical note explaining the deferral.

The cartographer reads the current `BACKLOG.md` before mutating to confirm the live style, and matches whichever form is dominant in the file at run time.
