## Notable event shapes

**Wave events** (dispatch only): `stage="dispatch_wave_started"` and `stage="dispatch_wave_completed"` carry `wave=N`, `specs=[NNN, …]`, and a per-wave `outcome ∈ {success, partial, fail}`. `partial` means some specs in the wave merged but at least one didn't; subsequent waves still run. The completed event carries `skipped=[…]` listing specs not launched because their declared deps include a failed NNN.

**Per-spec dispatch outcomes**: `outcome="interrupted"` (SIGINT), `outcome="skipped"` with `reason="already_merged"` or `reason="failed_dep"`, `outcome="failure"` with `fail_reason="unexpected exit"` (terminal-event fallback when a builder dies without emitting its own outcome). Skip propagation is transitive — a spec depending on a skipped spec is also skipped.

**`plan/superseded` tombstone**: a re-run of `bees plan <slug>` over a slug whose latest plan event is `outcome="started"` (an aborted prior attempt with no terminal event) first emits a tombstone `plan` record with `outcome="superseded"` before the new `plan/started`. Downstream readers see a clean log. `plan/superseded` is terminal — every consumer that closes a plan attempt by `outcome != "started"` treats it correctly without further changes.

**Coverage gap**: `stage="spec", outcome="coverage_gap"` is emitted when scribe fan-out drops one or more plan NNNs (see `stage-spec`).

**Verify stage events**: `stage="verify"`, `outcome ∈ {approve, reject, rejected-final, disabled, error}`, fields: `spec=NNN`, `attempt=1|2`, `model`, `duration_ms`, `tokens_in/out`, `cache_read/write`, `cost_usd`. First REJECT triggers a spec-revision pass and second builder attempt; second REJECT produces `rejected-final`. `disabled` when `BEES_VERIFY_DISABLE=1`.

**Spec-revision events**: `stage="spec-revision"`, `outcome ∈ {success, failure, error}`, fields: `spec=NNN`, `model`, `duration_ms`. Emitted during the one-retry remediation loop when first verify REJECT triggers a scribe revision pass.

**Accept stage events**: `stage="accept"`, `outcome ∈ {approve, concerns, disabled, error}`, fields: `concerns_count`, `observations_count`, `model`, `duration_ms`, `tokens_in/out`, `cache_read/write`, `cost_usd`. `disabled` when `BEES_ACCEPT_DISABLE=1` or `--skip-accept` passed to ship.

**Operator-repair events** (`bees ship` reconciliation): when `bees ship` detects that a spec's commits landed on the feature branch but no `dispatch/success` event was ever emitted (e.g., dispatch crashed after the builder committed), it appends one `stage="dispatch", outcome="success", source="operator-repair", repair_reason="commits_on_branch_no_success_event"` record per repaired spec. This reconciliation runs post-push, pre-PR, and is idempotent — a spec already showing `outcome=success` is skipped.
