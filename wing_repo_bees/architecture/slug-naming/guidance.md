## Guidance

**Format.** Slugs consist of lowercase ASCII letters, decimal digits (`0-9`), and hyphens (`-`). Length is capped at 100 characters. No uppercase, no underscores, no embedded slashes (type prefixes like `feat/` are a naming convention prepended by convention, not part of the bare slug body).

**Describe the work, not the implementation.** The slug names the user-visible change or the concept being addressed — not the code path, file name, or author.

| Good | Why |
|---|---|
| `oauth-login` | names the user-facing feature |
| `dashboard-sse-leak` | names the bug by symptom |
| `queen-prompt-trimming` | describes the change in plain language |

| Bad | Why not |
|---|---|
| `john-branch` | names the author, not the work |
| `wip` | no information content |
| `temp` | no information content |

**Type prefixes.** `feat/`, `fix/`, and `refactor/` are conventional prefixes that clarify intent in branch lists and PR titles. They are optional but recommended.

**CLI validation contract.** The bees CLI validates slugs at the entry point (`bees plan <slug>`). Slugs containing path-traversal sequences (`../`), empty segments, whitespace, or characters outside the allowed set are rejected before any filesystem writes or git operations begin. This makes the slug a safe component in all path construction throughout the workflow.
