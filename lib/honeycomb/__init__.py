"""honeycomb — recall over the four-level wing/room/closet/drawer structure.

Public API:
  - palace_recall(query, ...)          keyword recall (always available)
  - palace_recall_semantic(query, ...)  ChromaDB-backed semantic recall

Both return the same shape as the legacy bees-honeycomb API to preserve
the day-1 contract; v1.1+ will add `scope`, `tools`, `models` filter
params for targeted recall.
"""

from honeycomb.recall import palace_recall  # noqa: F401
from honeycomb.semantic import palace_recall_semantic  # noqa: F401

__version__ = "1.0.0"
