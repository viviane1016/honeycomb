## Guidance

Mint a new drone when you have a recurring, autonomous, workflow-triggered duty whose cadence comes entirely from an external event — a release publication, a scheduled cron, a repository webhook — and which requires no interactive operator involvement between trigger and completion. A new drone is always two artefacts: a `.github/workflows/<drone>.yml` and a `role-drone-<name>.md` that inherits the shared contract from this room and documents what is specific to that drone. Both are required; the workflow defines the trigger and execution, the room makes the authority explicit for reviewers.

Extend an existing drone instead of creating a new one when the new duty fires on exactly the same trigger as an existing drone and reads the same inputs. Adding a step to an existing workflow — and a new section to the existing drone's room — is less overhead than a new workflow and keeps the authority surface legible.

**Local dry-run pattern.** Each drone ships a `tools/<drone>-dry-run.sh` that reproduces the workflow's `claude -p` invocation locally with a dry-run prompt suffix, letting operators preview intended changes without firing the GitHub Actions workflow. First instances: `tools/cartographer-dry-run.sh`, `tools/scout-dry-run.sh`, `tools/sapper-dry-run.sh`, `tools/taster-dry-run.sh`. A new drone is expected to ship its dry-run alongside the workflow.
