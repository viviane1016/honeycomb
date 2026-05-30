---
depends-on: [001]
output-files: [lib/honeycomb/petitions.py, tests/test_petitions.py]
scribe-model: claude-opus-4-7
---

# Spec 006 — Petition helpers (submit/list/withdraw)

## Builder model

claude-sonnet-4-6

## Goal

Add `lib/honeycomb/petitions.py` exposing `submit`, `list_pending`, and `withdraw` helpers that manage drawer-override files in canon (`$HONEYCOMB_ROOT`) and optionally mirror them to a consumer-side overlay, opening / closing GitHub PRs via `gh` for the canonical landing.

## Scope

**Files to create**:
- `lib/honeycomb/petitions.py`
- `tests/test_petitions.py`

**Public symbols** in `lib/honeycomb/petitions.py`:
- `class PetitionError(RuntimeError)` — raised on missing `gh` CLI, dirty canon worktree, or subprocess non-zero exit.
- `@dataclass(frozen=True) class PetitionResult` with fields `petition_id: str`, `branch: str`, `pr_url: str | None`, `overlay_path: pathlib.Path | None`.
- `@dataclass(frozen=True) class PendingPetition` with fields `petition_id: str`, `target: str`, `consumer: str | None`, `tool: str | None`, `tool_version: str | None`, `path: pathlib.Path`, `source: str` (`"canon"` or `"overlay"`), `rationale: str`.
- `submit(target: str, content: str, rationale: str, context: dict, *, hc_root: pathlib.Path, overlay_root: pathlib.Path | None = None) -> PetitionResult` — `context` keys: `tool`, `tool_version`, `consumer` (any may be `None`). Computes override scope tag from context (`<tool>-<tool_version>` or `<consumer>` or `<tool>-<tool_version>_<consumer>`; consumer-only scope when tool absent). Resolves canonical drawer path under `hc_root/wing_*/**/<target>.md`; raises `PetitionError` if no such drawer exists. `petition_id` format `YYYYMMDD-NNN-<scope>` — date in UTC derived from a `git log -1 --format=%cI HEAD` invocation in `hc_root` (deterministic, avoids `datetime.now`), sequence NNN computed by counting existing `queenfile_*.md` files under canon that day. Branch name `feat/petition-<petition_id>`. Override filename `<target>.queenfile_<scope>.md` written next to canonical drawer. Frontmatter block written into the override file matches ADR-0002 §1 (`target`, `tool`, `tool_version`, `consumer`, `rationale` keys inside an `<!-- ... -->` HTML comment). Subprocess sequence (each via `subprocess.run([...], cwd=hc_root, check=False, capture_output=True, text=True)` and raising `PetitionError` on non-zero):
  1. `git rev-parse --git-dir` — verify hc_root is a git repo
  2. `git status --porcelain` — must be empty; else `PetitionError("canon worktree dirty")`
  3. `git checkout -b feat/petition-<petition_id>`
  4. Write override file (after branch checkout)
  5. `git add <override-relative-path>`
  6. `git commit -m "petition: <target> for <scope>"`
  7. `which gh` — if non-zero, raise `PetitionError("gh CLI not found")`
  8. `gh pr create --title "petition: <target> for <scope>" --body "<rationale>"` — capture stdout; the trailing URL line is the `pr_url`.
  When `overlay_root` is not `None`, also write the override file at `overlay_root/<canonical-relative-path>/<target>.queenfile_<scope>.md` (creating parent dirs); `overlay_path` field returns that path. Overlay write is unconditional on PR success (covers the "self-recall during PR-open window" case).
- `list_pending(consumer: str | None, *, hc_root: pathlib.Path, overlay_root: pathlib.Path | None = None) -> list[PendingPetition]` — walks `hc_root/wing_*/**/*.queenfile_*.md` (uses `pathlib.Path.rglob`) and, when `overlay_root` is set and exists, also walks `overlay_root/wing_*/**/*.queenfile_*.md`. Parses each file's frontmatter via `honeycomb.overrides.parse_override_file` (added in spec 001). Filters: keep entries where `consumer is None` (returns all) OR `entry.consumer == consumer` OR `entry.consumer is None` (canon-wide overrides match every consumer). Each result's `petition_id` is derived from the filename: strip the `<target>.queenfile_` prefix and the `.md` suffix to produce the scope tag, then prepend `unknown-`; the canonical `submit` path embeds the full ID by writing it into a `petition_id:` frontmatter line which the parser reads back (the override-file frontmatter parser MUST round-trip a `petition_id` key when present; if not present, fall back to the scope-tag id). Canon and overlay results are merged with overlay entries winning when they share the same override file path tail.
- `withdraw(petition_id: str, *, hc_root: pathlib.Path) -> None` — locates the branch `feat/petition-<petition_id>` (`git rev-parse --verify refs/heads/feat/petition-<petition_id>`; if missing, raise `PetitionError("petition not found")`). Switches to that branch via `git checkout`, finds the override file by reading `git diff-tree --no-commit-id --name-only -r HEAD`, removes it (`git rm <path>`), commits with message `petition: withdraw <petition_id>`, then closes the PR via `gh pr close --delete-branch <branch>`. Re-raises any subprocess failure as `PetitionError`.

**Subprocess invocations** must be wrapped in a single private helper `_run(argv: list[str], *, cwd: pathlib.Path) -> subprocess.CompletedProcess` so that tests can monkey-patch one symbol.

**Non-goals**:
- No `gh` retry / auth flow — assume `gh` is installed and authenticated; surface its stderr in `PetitionError` messages.
- No conflict-with-existing-petition detection beyond filename collision (overwrite-protect: if override file already exists on the target branch, raise `PetitionError("override file already exists")`).
- No PR-status polling, no PR merge logic, no manifest classification (that's spec 009).
- No use of `palace_recall` from inside `petitions.py` — keep the module subprocess + filesystem only.

## Failing test

`tests/test_petitions.py::TestPetitionSubmit::test_submit_writes_override_and_invokes_gh`

Sets up a temp directory acting as `hc_root` initialised as a git repo with one canonical drawer (`wing_bees/plan/foo-room/foo-closet/behaviour.md`) and one seed commit. Monkey-patches `honeycomb.petitions._run` to record argv and return synthetic `CompletedProcess` objects (returncode 0 for all calls; `gh pr create` returns a fake URL on stdout). Calls `submit(target="behaviour", content="override body", rationale="testing", context={"tool": "bees", "tool_version": "v1.18", "consumer": None}, hc_root=tmp_path, overlay_root=tmp_overlay)`. Asserts:
- Returns `PetitionResult` with `pr_url` matching the mock URL and `overlay_path` pointing at the overlay-written file.
- The override file exists at `wing_bees/plan/foo-room/foo-closet/behaviour.queenfile_bees-v1.18.md` and contains the rationale + content.
- The overlay copy exists at the same relative path under `tmp_overlay`.
- `_run` argv list includes a `git checkout -b feat/petition-...` call before the file write call, and a `gh pr create` call after the commit call.

A second test `test_submit_raises_when_gh_missing` patches `_run` so the `which gh` call returns returncode 1 and asserts `PetitionError` is raised with message containing `"gh CLI not found"`.

A third test `test_list_pending_merges_canon_and_overlay` seeds two override files (one in canon, one in overlay) with different `petition_id` frontmatter keys and asserts `list_pending(consumer=None, hc_root=..., overlay_root=...)` returns both entries with the correct `source` field.

A fourth test `test_withdraw_removes_file_and_closes_pr` seeds canon with a feature branch containing one override file, monkey-patches `_run`, calls `withdraw`, and asserts the recorded argv includes `git rm`, `git commit`, and `gh pr close --delete-branch`.

The tests must run via `python3 -m unittest discover -s tests` and fail before the builder starts (file does not exist).

## Builder prompt

You are the builder for spec 006 of honeycomb v1.1. Create two files:

1. `lib/honeycomb/petitions.py` — petition helpers that manage drawer-override files in canon and (optionally) a consumer overlay, opening and closing GitHub PRs via `gh`.
2. `tests/test_petitions.py` — unit tests using stdlib `unittest`.

**Background**: Honeycomb v1.1 collapses ADR-0001's petition mechanism into ADR-0002's drawer-override file format. A petition IS an override file (`<target>.queenfile_<scope>.md`) committed to a feature branch in canon and surfaced via a PR. Optionally the override is also written to a consumer overlay (e.g. `$BEES_REPO_ROOT/.bees/honeycomb-overlay/`) for immediate self-recall before PR merge.

**Public API** (exact signatures):

```python
class PetitionError(RuntimeError):
    pass

@dataclass(frozen=True)
class PetitionResult:
    petition_id: str
    branch: str
    pr_url: str | None
    overlay_path: pathlib.Path | None

@dataclass(frozen=True)
class PendingPetition:
    petition_id: str
    target: str
    consumer: str | None
    tool: str | None
    tool_version: str | None
    path: pathlib.Path
    source: str  # "canon" or "overlay"
    rationale: str

def submit(target: str, content: str, rationale: str, context: dict,
           *, hc_root: pathlib.Path,
           overlay_root: pathlib.Path | None = None) -> PetitionResult: ...

def list_pending(consumer: str | None, *,
                 hc_root: pathlib.Path,
                 overlay_root: pathlib.Path | None = None) -> list[PendingPetition]: ...

def withdraw(petition_id: str, *, hc_root: pathlib.Path) -> None: ...
```

**Subprocess discipline**:
- All shell invocations route through a single private helper `_run(argv, *, cwd) -> subprocess.CompletedProcess`. Tests will monkey-patch this symbol.
- Use `subprocess.run(..., capture_output=True, text=True, check=False)`. On non-zero exit, raise `PetitionError(f"{argv[0]} failed: {stderr}")`.

**`submit` algorithm**:
1. `_run(["git", "rev-parse", "--git-dir"], cwd=hc_root)` — verify git repo.
2. `_run(["git", "status", "--porcelain"], cwd=hc_root)` — must produce empty stdout; otherwise `PetitionError("canon worktree dirty")`.
3. Compute `scope` from `context`:
   - if `tool` and `tool_version` and `consumer`: `f"{tool}-{tool_version}_{consumer}"`
   - elif `tool` and `tool_version`: `f"{tool}-{tool_version}"`
   - elif `consumer`: `consumer`
   - else: raise `PetitionError("petition context must include at least tool+tool_version or consumer")`
4. Derive date string from `_run(["git", "log", "-1", "--format=%cI", "HEAD"], cwd=hc_root)` — parse the YYYY-MM-DD portion. (Deterministic; do NOT call `datetime.now`.)
5. Count existing `<...>.queenfile_*.md` files under `hc_root/wing_*` to derive a zero-padded `NNN` sequence number for the day.
6. `petition_id = f"{YYYYMMDD}-{NNN:03d}-{scope}"`. `branch = f"feat/petition-{petition_id}"`.
7. Locate canonical drawer file `hc_root/wing_*/**/<target>.md` via `pathlib.Path.rglob`. If 0 or >1 matches, raise `PetitionError`.
8. Override path: `<canonical-drawer-dir>/<target>.queenfile_<scope>.md`. If it already exists in the working tree, raise `PetitionError("override file already exists")`.
9. `_run(["git", "checkout", "-b", branch], cwd=hc_root)`.
10. Write override file with frontmatter:
    ```
    <!-- <target>.queenfile_<scope>.md
    target: <target>
    tool: <tool or "null">
    tool_version: <tool_version or "null">
    consumer: <consumer or "null">
    petition_id: <petition_id>
    rationale: |
      <rationale>
    -->

    <content>
    ```
11. `_run(["git", "add", str(override_path.relative_to(hc_root))], cwd=hc_root)`.
12. `_run(["git", "commit", "-m", f"petition: {target} for {scope}"], cwd=hc_root)`.
13. `_run(["which", "gh"], cwd=hc_root)` — if returncode != 0, raise `PetitionError("gh CLI not found")`.
14. `_run(["gh", "pr", "create", "--title", f"petition: {target} for {scope}", "--body", rationale], cwd=hc_root)` — last non-empty line of stdout is the `pr_url`.
15. If `overlay_root` is not `None`: compute overlay path `overlay_root / override_path.relative_to(hc_root)`, mkdir parents, write the same file content. Set `overlay_path` on the result.
16. Return `PetitionResult(petition_id, branch, pr_url, overlay_path)`.

**`list_pending` algorithm**:
- Use `honeycomb.overrides.parse_override_file(path)` (from spec 001) to read frontmatter from each `*.queenfile_*.md` under `hc_root/wing_*` and (when overlay_root is set and exists) `overlay_root/wing_*`. The parser returns an `OverrideSpec` with `target`, `tool`, `tool_version`, `consumer`, `rationale` plus an optional `petition_id` field — fall back to the scope-tag portion of the filename when the frontmatter doesn't carry one (prefix with `"unknown-"`).
- Filter: include the entry when `consumer is None` (caller wants everything), or `spec.consumer == consumer`, or `spec.consumer is None` (canon-wide override matches every consumer).
- Tag canon entries with `source="canon"` and overlay entries with `source="overlay"`. When the same relative path appears in both, prefer the overlay copy.
- Return the merged list ordered by `petition_id`.

**`withdraw` algorithm**:
1. `branch = f"feat/petition-{petition_id}"`.
2. `_run(["git", "rev-parse", "--verify", f"refs/heads/{branch}"], cwd=hc_root)` — if non-zero, raise `PetitionError("petition not found")`.
3. `_run(["git", "checkout", branch], cwd=hc_root)`.
4. `_run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], cwd=hc_root)` — stdout is the override path (one line expected).
5. `_run(["git", "rm", override_path], cwd=hc_root)`.
6. `_run(["git", "commit", "-m", f"petition: withdraw {petition_id}"], cwd=hc_root)`.
7. `_run(["gh", "pr", "close", "--delete-branch", branch], cwd=hc_root)`.

**Tests** (`tests/test_petitions.py`):
- Use `unittest.TestCase` + `tempfile.TemporaryDirectory`.
- Initialise the tmp canon as a git repo via real `subprocess.run` calls (`git init`, `git -c user.email=test@example.com -c user.name=Test commit ...`) once per setUp so `git log` / `git rev-parse` succeed.
- Monkey-patch `honeycomb.petitions._run` for the subprocess sequence under test; record argv into a list so the test can assert ordering.
- Four tests as enumerated in the **Failing test** section above.
- Tests run under `python3 -m unittest discover -s tests`.

**Constraints**:
- Stdlib only — no third-party imports.
- Python ≥ 3.10 (use `pathlib.Path`, `dataclass(frozen=True)`, `|` union syntax).
- Module docstring documents the public API and the `gh` CLI dependency.
- Do not call `datetime.now`, `time.time`, or `os.environ` in `submit` — keep the function deterministic given (target, content, rationale, context, hc_root, overlay_root) and the canon repo state.
- Do not log or print at import time; keep the module side-effect-free until called.

**Acceptance** (success check below):
- All four tests pass via `python3 -m unittest discover -s tests`.
- The diff touches only `lib/honeycomb/petitions.py` and `tests/test_petitions.py`.

## Success check

`python3 -m unittest discover -s tests -v` passes (including the four new tests), and the diff is limited to `lib/honeycomb/petitions.py` plus `tests/test_petitions.py`. Manual review confirms: (a) all subprocess calls flow through `_run`, (b) `submit` does not call `datetime.now`, (c) `PetitionError` is raised with a clear message when `gh` is missing or canon is dirty, (d) overlay write happens only when `overlay_root` is provided.

## Commit message

```
feat(honeycomb): petition helpers (submit/list/withdraw) (#006)

Adds lib/honeycomb/petitions.py with submit/list_pending/withdraw
helpers that manage <drawer>.queenfile_<scope>.md override files in
canon and optionally mirror them to a consumer overlay. submit opens a
GitHub PR via gh; withdraw closes it. All subprocess invocations route
through a single _run helper so tests can monkey-patch one symbol.

Refs: .bees/honeycomb-v1-1/specs/006-petition-helpers.md
```
