## JSONL log-record side-effect

Every `palace_recall` call (and every petition tool call) appends one JSONL record to the log destination before the MCP response returns.

### Record schema (schema_version: 1)

```jsonl
{
  "schema_version": 1,
  "ts": "2026-05-30T14:22:00.123Z",
  "tool": "palace_recall",
  "slug": "honeycomb-cutover",
  "actor": "queen",
  "stage": "plan",
  "model": "claude-sonnet-4-6",
  "request": {
    "query": "manual amend",
    "wings": ["wing_bees"],
    "top_k": 3,
    "drawer": false,
    "engine": "semantic"
  },
  "response": {
    "result_count": 2,
    "results": [
      {
        "wing": "wing_bees",
        "room": "build",
        "closet": "manual-amend",
        "drawer": null,
        "bytes": 1248,
        "score": 0.87,
        "source": "canon",
        "content_sha": "ab12cd34ef56gh78..."
      }
    ],
    "fallback_engine": null
  },
  "duration_ms": 42
}
```

**Field notes:**

- `bytes` — rendered bytes of the closet + drawer content returned to the caller (what the actor saw), not raw file size.
- `content_sha` — sha256 hex of the returned content. Lets the consumer correlate "this returned content" with "this content appeared in the actor's output" across stages.
- `source` — `"canon"` | `"consumer-overlay"` | `"honey-<name>@<version>"`. Identifies which collection or overlay served each result.
- `schema_version` — currently `1`. Bumping is a breaking change for log consumers; version policy is documented in `lib/honeycomb/log.py`.

### Write semantics

Records are written synchronously: `f.write(line); f.flush()` before the MCP response returns. `fcntl.flock(LOCK_EX)` wraps the append to guard against corruption when two MCP subprocesses write the same file concurrently (e.g. parallel scribe spawns on the same feature).

No rotation at the MCP layer. Per-feature logs are small (<50 recall calls per stage); cross-feature rollup is the consumer's concern.

See ADR-0004 §2 (schema), §3 (destination), §4 (write semantics).
