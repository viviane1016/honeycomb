## Statuses

At emission: the artifact file is written with frontmatter `status: pending`.

At PR review: the operator marks each petition (or bundle):
- `accepted` — the suggested change is sound; queue it for the next honeycomb editorial release.
- `declined` — not the right direction; petition is noted but not queued.

Accepted petitions are queued for inclusion in a future honeycomb update. No auto-merge into honeycomb occurs at runtime (ADR-0006).
