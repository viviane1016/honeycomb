## Guidance

The review pass is the cross-spec consistency gate. Per-spec issues should usually be caught here rather than discovered at builder-bee time, because a builder failure costs more in tokens, time, and operator attention than a queen rewrite. Keep REWRITEs minimal — replace only what's actually wrong; APPROVE everything else.

The review has no retry: a malformed response aborts the spec stage with no files written. This favours fast failure over silent corruption.
