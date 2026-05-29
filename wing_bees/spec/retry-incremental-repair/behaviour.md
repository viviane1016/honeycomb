## Behaviour

### Retry trigger

A retry fires when `parse_spec_blocks`, `validate_spec_body`, or the block-count check raises `ValueError` (`lib/spec.py:1144`). Common triggers include: missing required sections, wrong fence count, wrong NNN prefix, and invalid spec filename. Secret-detected failures (`scan_for_secrets`) are terminal — they do not retry.

### Retry prompt structure

`build_retry_prompt` (`lib/spec.py:362`) constructs a three-part follow-up prompt:

1. **Error block** — the specific `ValueError` message, code-indented in the preamble. The preamble states: "Your previous output failed validation with this error."

2. **Previous-raw-output block** — the model's prior output verbatim, enclosed in markers:
   ```
   ---PREVIOUS OUTPUT (BEGIN)---
   <prior output>
   ---PREVIOUS OUTPUT (END)---
   ```

3. **Original request** — the base prompt appended after the previous-output block, introduced by "Original request (for reference):".

The directive embedded in the preamble reads: "Emit the same specs again, fixing only what the error flagged. Do not explain, do not apologize, do not add commentary — output only the corrected fenced specs."

### Retry loop flow

The retry loop at `lib/spec.py:1082-1158` iterates `attempt` from 1 to `max_attempts` (2). On `ValueError`:

- `is_last = attempt >= max_attempts` (`lib/spec.py:1146`) guards the two paths.
- If not last: `attempt_prompt = build_retry_prompt(base_prompt, raw, error)` and the loop continues.
- If last: `specs_dir / f".raw.{nnn}.txt"` is written with the raw output, and the process exits non-zero with a message citing the saved file.

The event log records `outcome="parse_failure_retrying"` on the first failure and `outcome="parse_failure_final"` on the second, both carrying the `parse_error` field.

### What "fix only what the error flagged" means operationally

The directive is narrow by design: the model must not re-derive the full spec, restructure sections that passed validation, or add explanatory commentary. Only the single element that caused the `ValueError` is corrected — for example, adding a missing `## Failing test` section or adjusting a fence label to match the expected `NNN-` prefix. This prevents regressions in sections that were already correct.

### Postmortem artefact

On second failure, `.raw.NNN.txt` is written to the specs directory (not the cell root). This file contains the model's last raw output before exit, enabling the operator to inspect what the scribe produced and diagnose whether the failure was a model-reasoning issue, a spec-ambiguity issue, or a transient formatting glitch.
