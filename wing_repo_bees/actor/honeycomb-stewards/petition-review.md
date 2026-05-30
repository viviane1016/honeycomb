## Petition review

Each petition PR contains one file: `<drawer>.queenfile_<scope>.md`. The frontmatter block carries: `target` (canonical drawer path), `tool`, `tool_version`, `consumer`, `rationale`.

**Review checklist:**

1. Does `target` match an existing drawer or an unambiguous new slot in the four-level structure?
2. Is the proposed content terse and authoritative — not a raw AI trace or a copy of the petitioning actor's internal deliberation?
3. Does the scope (`tool`, `tool_version`, `consumer`) correctly identify the consumers this override should apply to?
4. Does the rationale cite a concrete observed failure (an ADR-0004 signal pattern, a logged miss, a documented prescription failure) — not a hypothetical?

**Accept.** Merge with commit message: `petition: adopted <target> for <scope>`. The override file is retained in canon at `<wing>/<room>/<closet>/<drawer>.queenfile_<scope>.md` and becomes visible to matching consumers on their next `tools/install.sh --tool <tool> --tool-version <ver> --consumer <consumer>` run.

**Decline.** Close the PR with a comment explaining the reason. Optionally write a cleanup commit `petition: declined <target> for <scope>` so the manifest walker classifies it correctly in the operator summary rather than leaving it as `pending`.

**Partial accept.** If the content is directionally correct but needs editing, the steward may amend the file before merging, noting the changes in the PR comment. The petitioning actor's overlay copy (if any) will diverge from canon after merge; consumers should re-run install to pick up the canon version.
