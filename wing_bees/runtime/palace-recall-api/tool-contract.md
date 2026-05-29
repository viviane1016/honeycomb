## Tool contract

**Signature:** `palace_recall(query, wings=None, halls=None, top_k=3, drawer=False)`

Parameters:

- `query` (str, required) — free-text search string; the scorer matches terms against room names, closets, and body content.
- `wings` (list of str, optional, default `None`) — restrict search to specific wings, e.g. `["bees"]`, `["practices"]`, `["tools"]`. Omit (or pass `None`) for a cross-wing search.
- `halls` (list of str, optional, default `None`) — restrict search to specific halls, e.g. `["hall_procedure"]`, `["hall_architecture", "hall_protocol"]`. Short names without the `hall_` prefix are accepted. Omit for an unfiltered search. Rooms without a hall annotation match no hall filter. See `arch-halls` for the taxonomy.
- `top_k` (int, default `3`) — maximum number of rooms to return.
- `drawer` (bool, default `False`) — when `False`, each result dict contains `{wing, room, hall, path, closet}`; when `True`, a `"drawer"` key is added containing the full room body.

**Return value:** a list of result dicts ordered highest-score first. An empty list means no room scored above zero. Callers should handle the empty case gracefully.
