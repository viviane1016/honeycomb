## Anti-patterns

- **Flat install under a generic name** — `~/.local/lib/plan.py` silently
  shadows or is shadowed by same-named modules from unrelated tools.
- **Inserting the package directory itself** — `sys.path.insert(0, ".../lib/bees")` means `import plan` works but `from bees.plan import …` does not; breaks the namespace guarantee.
- **Different import paths in dev vs installed** — if `bin/bees` uses
  `from lib.plan import …` in the repo but the installed copy needs
  `from bees.plan import …`, the two code paths diverge and bugs hide
  in one but not the other.
