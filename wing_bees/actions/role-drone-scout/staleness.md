## Staleness

Scout embeds a `Scout: <ISO-8601 UTC timestamp>` tag in every header it writes (e.g. `Scout: 2026-05-12T14:23:45Z`). On subsequent runs, scout compares this tag against the file's last-commit timestamp obtained via:

```
git log --format="%aI" -1 -- <file>
```

Three-way decision:
- **No header present** → write one.
- **Header timestamp ≥ last-commit timestamp** → skip (header is current; file has not changed since the header was written).
- **Header timestamp < last-commit timestamp** → regenerate (file was modified after the header was written).

The `force` input is passed as the string `'true'` or `'false'` from `workflow_dispatch.inputs.force`. When `'true'`, it bypasses all staleness checks and unconditionally regenerates every eligible header. Useful after a header-format change or when headers have drifted and cannot be trusted.
