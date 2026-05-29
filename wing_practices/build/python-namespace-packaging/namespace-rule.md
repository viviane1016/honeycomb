## Namespace rule

A module installed to `~/.local/lib/plan.py` is reachable as `import plan`
by *any* process that inserts `~/.local/lib/` into `sys.path`. A module at
`~/.local/lib/bees/plan.py` is reachable only as `from bees.plan import …` —
collision-safe.

The canonical layout for a project named `bees`:

```
# In the repo
lib/
  bees/
    __init__.py
    plan.py
    dispatch.py
    …

# Installed
~/.local/
  bin/bees           ← entry point
  lib/
    bees/
      __init__.py
      plan.py
      dispatch.py
      …
```

The entry point sets:

```python
BEES_HOME = Path(__file__).resolve().parent.parent   # → ~/.local/
sys.path.insert(0, str(BEES_HOME / "lib"))            # → ~/.local/lib/
from bees.plan import cmd_plan                        # → ~/.local/lib/bees/plan.py
```

In the development tree `bin/bees` sits at `<repo>/bin/bees`, so
`BEES_HOME / "lib"` resolves to `<repo>/lib/` — the same import path
(`from bees.plan import …`) works without modification.
