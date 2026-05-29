## Conventions

### Heading structure

- Release groupings use `##` headings, optionally with a status suffix:
  - `## Release X.Y` *(no suffix — upcoming or in-progress)*
  - `## Release X.Y (shipped YYYY-MM-DD)`
  - `## Release X.Y (target: after X retro)`
- Sub-clusters within a release use `###` headings.
- Items are `-` bulleted under their target-release heading.

### Item format

Active items are plain bullet entries:

```
- **Item title.** Description of the work.
```

### Shipped items

Struck with `~~` surrounding the bold title, followed immediately by `**Shipped YYYY-MM-DD.**` and then the rationale text. Two attested equivalent forms:

```
- ~~**item title**~~ **Shipped YYYY-MM-DD.** Rationale text here.
- ~~**item title.**~~ **Shipped YYYY-MM-DD.** Rationale text here.
```

Both forms are valid; match whichever is dominant in the live file.

### Rationale retention

Rationale text under a struck item is retained verbatim. The BACKLOG reads as a historical record, not a moving target — do not trim or summarise rationale when striking an item.

### Deferred and reordered items

Items that are deferred or reordered keep their existing rationale and gain a parenthetical note explaining the deferral:

```
- **Item title.** Original rationale. (deferred: scope creep for this release)
```
