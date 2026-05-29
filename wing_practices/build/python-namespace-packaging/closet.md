<!-- python-namespace-packaging.md: migrated from python-packaging.md.

Hall: hall_rubric
tools: [pip, setuptools]
languages: [python]
-->

Always namespace library modules under the project name: `from bees.plan import …`, not `from lib.plan import …`. Install to `~/.local/lib/<project>/`. Insert the *parent* of the namespace package into `sys.path` — not the grandparent. Generic names (`lib`, `utils`, `helpers`) pollute shared `sys.path` directories and risk silent collisions with other tools.
