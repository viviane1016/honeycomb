<!-- queen-review.md: migrated from queen-review.md.

Hall: hall_procedure
tools: [read, grep, glob, palace_recall]
models: [opus]
-->

Within the spec stage, the queen runs one review pass over all drafts. For each NNN she emits one block: `<<<APPROVE NNN>>>` (keep), `<<<REWRITE NNN>>>` (replace), or `<<<DEPS NNN>>>` (correct `depends-on:`). The harness validates against expected NNN set, applies DEPS patches, validates REWRITE bodies, secret-scans, and writes all spec files atomically. No review-retry in v1.
