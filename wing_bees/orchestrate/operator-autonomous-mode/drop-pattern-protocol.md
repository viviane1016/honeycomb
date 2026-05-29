## Drop-pattern protocol

When an underlying bug is fixed and a previously-approved workaround becomes obsolete, retire it using this procedure:

1. **File a PR against this room** removing the obsolete entry from `## Approved baked-in logic` and adding a "dropped" entry to `## Recipe-version history` that names the workaround, the date it was dropped, and the fix that made it obsolete.
2. **Audit in-flight wakeup prompts.** Any `ScheduleWakeup` prompts that were generated from the old recipe — whether still pending or already fired but with descendants scheduled — should have the obsolete logic stripped. If you cannot identify all in-flight prompts, add a note to the PR body so the operator knows to watch for stale behaviour on any active feature runs.
3. **Update the recipe-version history** with a `vN (dropped <workaround>)` sub-entry so the timeline is legible.

**Canonical example — v1.7.2 Haiku-to-Sonnet sed-fix (2026-05-25).** During a bees dogfood session, operator-Claude had a Haiku-to-Sonnet model-substitution workaround baked into its wakeup prompts. The workaround predated v1.7.2's proper fix and had been obsolete since that release. On 2026-05-25, operator-Claude's stale wakeup prompts applied the sed-substitution to a feature that didn't need it, corrupting a spec stage that would otherwise have succeeded and killing the feature run. The incident (#217) prompted this room. The drop-pattern protocol above is the intended safeguard against recurrence: workarounds are documented here, removed here when the fix lands, and the audit step above closes the gap between "fix merged" and "all prompts updated."
