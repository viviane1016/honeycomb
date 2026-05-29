## Assignment

Hall is encoded as a `Hall: hall_<x>` line inside the existing scout-header HTML comment, conventionally placed immediately before the `Scout:` line:

```
<!-- arch-thing.md: One-line description.

Body paragraph describing the room's content and intent.

Hall: hall_architecture
Scout: 2026-05-19T00:00:00Z -->
```

`tools/annotate_halls.py` walks `honeycomb/wing_*/` and inserts the line based on the assignment rules above. Edge cases (rooms whose filename prefix doesn't disambiguate) are resolved by hard-coded overrides in the script, so re-runs are deterministic and a single diff is reviewable.

`parse_room` in `lib/bees/bees_honeycomb.py` extracts the hall field and `palace_recall` accepts a `halls=[...]` filter that prunes by hall before keyword scoring. Rooms without a hall annotation are treated as "unfiltered" — they match no hall filter and pass through when `halls` is `None`. The coverage assertion in `tests/test_honeycomb_content.py` catches drift if new rooms land without an annotation.
