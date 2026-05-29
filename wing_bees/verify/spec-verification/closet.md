<!-- spec-verification.md: migrated from stage-verify.md.

Hall: hall_procedure
-->

The scribe re-enters per spec in verify mode. Inputs: spec body + builder diff. Four criteria: scope-file containment, required-symbol presence, failing-test scenario addressed, commit-message references spec path. Output: APPROVE NNN or REJECT NNN + reason. Evaluates the diff against the spec; doesn't re-implement. Slots between builder commit and FF-merge in stage-dispatch.
