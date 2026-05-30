## Responsibilities

Stewards own the `viviane1016/honeycomb` canon. Their primary duty is reviewing petition PRs and maintaining the commit-message convention that the install-time manifest walker uses to classify accepted/declined/pending petitions since the previous install.

**Commit-message convention:**

- Accept: merge commit message `petition: adopted <drawer-path> for <scope>`
- Decline: close the PR with a reason comment. Optionally write a cleanup commit `petition: declined <drawer-path> for <scope>` so the manifest walker classifies it correctly in the operator summary.
- PRs merged without either prefix are classified as `pending` by the manifest walker; stewards must use the prefix consistently.

**Beyond petitions.** Stewards also manage the overall structure: adding, moving, or deprecating closets; bumping `wing_bees/_manifest.yaml` version on releases; tagging release commits. Structural changes follow the normal PR process; no special commit-message prefix is required.

**Operator summary.** After each consumer runs `tools/install.sh`, the install script prints a one-line summary of accepted/declined/pending petitions since the previous install (derived by the manifest walker from the commit log between the previous HEAD and the new HEAD). Correct commit-message discipline from stewards is what makes this summary accurate.
