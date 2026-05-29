## Briefing classification — for the queen's internal use

When you read a briefing, internally classify it against the tag set below. Tag is multi-select: a feature may belong to several categories simultaneously.

### Tag definitions

- **`security`** — anything that strengthens or affects system security, threat model, or security controls. Usually paired with more specific tags like `auth` or `data`.
- **`auth`** — authentication, authorization, identity management, session handling, credential storage, permission models.
- **`performance`** — speed, latency, throughput, resource efficiency, caching, optimization, scalability.
- **`ui`** — user-facing frontend, UI components, user experience, accessibility, visual design.
- **`infra`** — deployment, infrastructure, environments (staging, prod), DevOps, containerization, networking, load balancing.
- **`refactor`** — internal code reorganization, pattern consolidation, technical debt reduction, no external behaviour change.
- **`docs`** — documentation, guides, comments, README updates, decision records, training materials.
- **`data`** — databases, data models, storage, migration, querying, indexing, data consistency.
- **`observability`** — logging, metrics, tracing, monitoring, dashboards, alerting, debugging aids.
- **`build`** — compilation, bundling, build tooling, CI/CD pipelines, test infrastructure, artifact management.

### How to use tags for honeycomb recall

Once you classify the briefing, use `palace_recall(tags=[...], wing="wing_practices")` to fetch guidance from honeycomb's S-SDLC wing (rooms matching your tags).

Example: A briefing for "Add OAuth login to the authentication service" classifies as `[security, auth]`. You query:

```
palace_recall(tags=["security", "auth"], wing="wing_practices")
```

Honeycomb returns rooms like `wing_practices/secret-handling`, `wing_practices/antipattern-plaintext-credentials` — matching your classification.

If your initial query feels incomplete, iterate. A mid-plan discovery ("oh, this also affects performance") justifies a follow-up recall with updated tags.

### Calibration between releases

The tag set is stable for v0.1. Between honeycomb releases, tags may be added, deprecated, or refined. When honeycomb version changes, the queen-file petitions section may reference tags that no longer match. This is handled by the queen-file review at plan time, not here.
