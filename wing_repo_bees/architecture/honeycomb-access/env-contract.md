## Env contract and log destination

The honeycomb MCP server reads five env vars at invocation:

| Var | Since | Purpose |
|-----|-------|---------|
| `BEES_FEATURE_SLUG` | v1.0 | In-flight feature slug; used in log path |
| `BEES_REPO_ROOT` | v1.0 | Consumer repo root; used for overlay and log path |
| `BEES_ACTOR` | v1.1 | Actor identity: `"queen"` \| `"scribe"` \| `"builder"` \| `"drone-<name>"` |
| `BEES_STAGE` | v1.1 | Stage: `"plan"` \| `"spec"` \| `"dispatch"` \| `"verify"` \| `"accept"` \| `"ship"` \| `"retro"` \| `"debug"` |
| `BEES_MODEL` | v1.1 | Model identifier, e.g. `"claude-sonnet-4-6"` |

**Missing values are non-fatal.** When `BEES_ACTOR`, `BEES_STAGE`, or `BEES_MODEL` is absent, the log record writes `"unknown"` for that field. The MCP server does not validate values against an allowlist — labels are opaque strings, preserving decoupling from bees actor taxonomy.

**The bees harness is expected to set all five for every MCP spawn.** Missing values in production indicate a harness integration gap.

### Log destination

Production (both vars set):
```
$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl
```

Dev fallback (either var unset):
```
$HONEYCOMB_ROOT/.calls.jsonl
```

The dev fallback is not consumed by anything in production; it exists for honeycomb-side debugging only.

See ADR-0004 §1 (env contract) and §3 (log destination).
