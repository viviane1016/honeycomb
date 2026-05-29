## Why

Agents work best when each file answers one question and stays scannable in a single context load. Without that constraint, planning degrades into "edit the monolith" specs that cannot parallelise, builders waste context on irrelevant code, and merge conflicts accumulate at the busiest parts of the codebase. File-structure discipline is a force multiplier: applied proactively at the planning stage, it keeps the dispatch graph fan-out high and the conflict rate low.
