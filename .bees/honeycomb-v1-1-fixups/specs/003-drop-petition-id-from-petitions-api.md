---
depends-on: [001]
scribe-model: claude-opus-4-7
---

# Spec 003 — Drop `petition_id` from petitions API and queenfile frontmatter

## Builder model

claude-opus-4-7

## Goal

Remove the `petition_id` field from `lib/honeycomb/petitions.py`, the override-file HTML-comment frontmatter, the MCP descriptors in `bin/honeycomb-mcp`, and the two affected test files; switch `palace_petition_withdraw` to take the override file's relative path (its identity per ADR-0002) and derive its branch deterministically from that path so both `submit` and `withdraw` agree.

## Scope

**Edit:**

- `lib/honeycomb/petitions.py`
  - Remove `petition_id: str` from `PetitionResult` and `PendingPetition` dataclasses.
  - Delete `_PETITION_ID_LINE_RE` and `_read_petition_id`.
  - Add a module-private helper `_branch_for_path(rel_path: str) -> str` that returns `f"feat/petition-{hashlib.sha1(rel_path.encode('utf-8')).hexdigest()[:12]}"`. Use it from both `submit` and `withdraw`.
  - In `submit`: delete the `git log -1 --format=%cI` date-derivation block, delete the `for wing_dir in hc_root.glob("wing_*"): … rglob("*.queenfile_*.md")` count block, drop the `petition_id` local variable, derive `branch = _branch_for_path(rel_path)` after computing `rel_path = str(override_path.relative_to(hc_root))`, return `PetitionResult(branch=branch, pr_url=pr_url, overlay_path=overlay_path)`.
  - In `_build_override_content`: remove the `petition_id` parameter and the `f"petition_id: {petition_id}\n"` line. Update the call site in `submit` accordingly.
  - In `list_pending`: drop the `pid = _read_petition_id(p)` lookup; construct `PendingPetition` without `petition_id`; change the sort key from `lambda p: p.petition_id` to `lambda p: str(p.path)`.
  - In `withdraw`: change signature to `withdraw(path: str, *, hc_root: pathlib.Path) -> None`; compute `branch = _branch_for_path(path)`; keep the rest of the body (`git rev-parse --verify refs/heads/{branch}`, `git checkout {branch}`, `git rm {path}`, `git commit -m f"petition: withdraw {path}"`, `gh pr close --delete-branch {branch}`).
  - Update the module docstring's `Public API` block to reflect the new `withdraw(path, *, hc_root)` signature and to drop the `sorted by petition_id` phrasing (use `sorted by path`).

- `bin/honeycomb-mcp`
  - In `PETITION_SUBMIT_DESCRIPTOR.description`: replace the literal substring `Returns {petition_id, branch, pr_url, overlay_path}.` with `Returns {branch, pr_url, overlay_path}.`.
  - In `PETITION_WITHDRAW_DESCRIPTOR`: replace `"petition_id": {"type": "string"}` with `"path": {"type": "string", "description": "Relative path to the override file within $HONEYCOMB_ROOT — its identity per ADR-0002."}` and change `"required": ["petition_id"]` to `"required": ["path"]`.
  - In the `palace_petition_withdraw` branch of `_handle_tools_call`: change the missing-argument guard from `"petition_id"` to `"path"`, change the missing-argument error string accordingly, and change the call site from `petitions.withdraw(petition_id=arguments["petition_id"], hc_root=root)` to `petitions.withdraw(path=arguments["path"], hc_root=root)`.

- `tests/test_petitions.py`
  - Drop the `petition_id: str` parameter and the `f"petition_id: {petition_id}\n"` line from `_write_override`.
  - In `test_list_pending_merges_canon_and_overlay`: remove the `petition_id=...` kwargs from the two `_write_override` calls; replace the `next(... if r.petition_id == "...")` lookups with lookups keyed on `r.target` (`"behaviour"` vs `"other"`); keep the `source` assertions intact.
  - In `TestWithdraw.test_withdraw_removes_file_and_closes_pr`: drop the `petition_id = "..."` local, define `override_rel = "wing_bees/plan/foo-room/foo-closet/behaviour.queenfile_bees-v1.18.md"`, compute the expected branch in the test via `hashlib.sha1(override_rel.encode()).hexdigest()[:12]` to match `_branch_for_path`, call `withdraw(path=override_rel, hc_root=self.hc_root)`, and assert the recorded `gh pr close --delete-branch` argv contains the computed branch.

- `tests/test_mcp_petitions.py`
  - In `_STUB_PETITIONS_CODE`:
    - Drop the `"petition_id": "p123"` key from the `submit` stub's return dict.
    - Change the `withdraw` stub signature from `def withdraw(petition_id, *, hc_root):` to `def withdraw(path, *, hc_root):`; change the `_record("withdraw", {"petition_id": petition_id})` call to `_record("withdraw", {"path": path})`.
  - In `test_petition_submit_dispatches_to_helper`: remove `self.assertEqual(result["petition_id"], "p123")`; keep the `branch`, `pr_url`, `overlay_path` assertions.

**Add (new test, drives the implementation):**

- `tests/test_petitions.py::TestPetitionSubmit::test_submit_omits_petition_id_and_branch_is_deterministic_from_path`.

**Non-goals (explicitly out of scope, do NOT touch):**

- Any markdown file under `wing_bees/plan/palace-petitions/` or `wing_bees/plan/petitions-flow/`. Documentation sync is unit 004.
- `decisions/0002-drawer-overrides-scoped-indexes.md`. Supersession note is unit 004.
- `decisions/0001-mcp-mediated-queenfile-and-petitions.md`. ADR-0001 already carries a "superseded" annotation on the petition_id sections from prior work; do not edit.
- `README.md`, `CHANGELOG.md`, `BACKLOG.md`, `VERSION`. Unit 004.
- `tools/install.sh`. Unit 002.
- `lib/honeycomb/recall.py`, `lib/honeycomb/semantic.py`, `lib/honeycomb/log.py`, `lib/honeycomb/overrides.py`, `lib/honeycomb/manifest.py`. Out of scope.
- Migration / deprecation logic for pre-existing `.queenfile_*.md` files that still carry `petition_id:`. The `overrides.parse_override_file` parser already ignores unknown frontmatter fields, so legacy content remains readable without action.

## Failing test

`tests/test_petitions.py::TestPetitionSubmit::test_submit_omits_petition_id_and_branch_is_deterministic_from_path`

Add this test to the existing `TestPetitionSubmit` class. Before the builder's implementation lands, the test fails because (a) `PetitionResult` still carries `petition_id`, (b) the written override file's HTML comment still contains a `petition_id:` line, and (c) the branch name still encodes the YYYYMMDD-NNN-scope scheme rather than a SHA-derived suffix.

```python
def test_submit_omits_petition_id_and_branch_is_deterministic_from_path(self):
    import hashlib
    mock_run, calls = self._build_mock()

    with patch.object(pet_mod, "_run", mock_run):
        result = submit(
            target="behaviour",
            content="override body",
            rationale="testing",
            context={"tool": "bees", "tool_version": "v1.18", "consumer": None},
            hc_root=self.hc_root,
            overlay_root=None,
        )

    self.assertFalse(
        hasattr(result, "petition_id"),
        "PetitionResult must not carry a petition_id field",
    )

    override_path = (
        self.hc_root
        / "wing_bees" / "plan" / "foo-room" / "foo-closet"
        / "behaviour.queenfile_bees-v1.18.md"
    )
    text = override_path.read_text(encoding="utf-8")
    self.assertNotIn(
        "petition_id:", text,
        "override frontmatter must not contain a petition_id line",
    )

    rel = str(override_path.relative_to(self.hc_root))
    expected_branch = f"feat/petition-{hashlib.sha1(rel.encode('utf-8')).hexdigest()[:12]}"
    self.assertEqual(result.branch, expected_branch)
```

The test must pass after the builder finishes. The full `tests/` suite must pass too — the builder is responsible for updating the other tests listed in **Scope** so they remain green under the new API.

## Builder prompt

You are removing the `petition_id` field from the honeycomb petitions API and the queenfile HTML-comment frontmatter. The field is an over-engineered date-and-count identifier; ADR-0002 says the override file's path *is* its identity, so the field is redundant and its derivation logic (querying git log + counting existing queenfiles) is fragile.

**Read first** to ground yourself:

- `lib/honeycomb/petitions.py` — the whole file. Note `PetitionResult`, `PendingPetition`, `_PETITION_ID_LINE_RE`, `_read_petition_id`, `_build_override_content`, `submit`, `list_pending`, `withdraw`. The date-derivation step is `_run(["git", "log", "-1", "--format=%cI", "HEAD"], cwd=hc_root)`; the count step uses `for wing_dir in hc_root.glob("wing_*"): existing_count += sum(1 for _ in wing_dir.rglob("*.queenfile_*.md"))`. Both go away.
- `lib/honeycomb/overrides.py` — confirm `parse_override_file` reads only `target`, `tool`, `tool_version`, `consumer`, `rationale`. It already ignores `petition_id:` lines, so removing them is safe (and removing them aligns the implementation with the documented schema in `wing_bees/plan/queenfile-contract/file-format.md`).
- `bin/honeycomb-mcp` — locate `PETITION_SUBMIT_DESCRIPTOR`, `PETITION_LIST_DESCRIPTOR`, `PETITION_WITHDRAW_DESCRIPTOR`, and the `palace_petition_withdraw` branch inside `_handle_tools_call`.
- `tests/test_petitions.py` and `tests/test_mcp_petitions.py` — these are the tests you must update so the full suite stays green.

**Implement:**

1. **`lib/honeycomb/petitions.py`.** Add `import hashlib` if not already present. Add a module-private helper:

   ```python
   def _branch_for_path(rel_path: str) -> str:
       return f"feat/petition-{hashlib.sha1(rel_path.encode('utf-8')).hexdigest()[:12]}"
   ```

   Remove `petition_id: str` from both `PetitionResult` and `PendingPetition` (the dataclasses are `@dataclass(frozen=True)` — leave the decorator and the other fields untouched). Delete `_PETITION_ID_LINE_RE` and `_read_petition_id`. Remove the `petition_id` parameter from `_build_override_content` and remove the `f"petition_id: {petition_id}\n"` line from its returned string — the resulting comment block must contain only `target`, `tool`, `tool_version`, `consumer`, and `rationale` (matching the schema in `wing_bees/plan/queenfile-contract/file-format.md`).

   In `submit`: delete the `# 4. Derive date from git log` block (the `git log -1 --format=%cI` call) and the `# 5. Count existing queenfile files` block. Drop the `petition_id` local. After computing `rel_path = str(override_path.relative_to(hc_root))` (which currently happens after the override is written but before the `git add` call), compute `branch = _branch_for_path(rel_path)` and use it for the `git checkout -b {branch}` call. Move the `git checkout -b` call so it happens AFTER `rel_path` is known — the existing code checks out the branch before writing the file, but you now need `rel_path` to compute the branch name. Reorder to: locate canonical drawer → compute override_path → guard against clobber → compute `rel_path` → compute `branch = _branch_for_path(rel_path)` → `git checkout -b {branch}` → write file → `git add` → `git commit` → `which gh` → `gh pr create` → overlay mirror. Return `PetitionResult(branch=branch, pr_url=pr_url, overlay_path=overlay_path)`. Keep all existing PetitionError raises unchanged.

   In `list_pending`: in `_collect`, drop the `pid = _read_petition_id(p)` line and the `if pid is None: pid = f"unknown-..."` fallback; construct `PendingPetition(target=..., consumer=..., tool=..., tool_version=..., path=p, source=source, rationale=spec.rationale)` without a `petition_id` arg. Change the final return to `return sorted(entries.values(), key=lambda p: str(p.path))`.

   In `withdraw`: change the signature to `def withdraw(path: str, *, hc_root: pathlib.Path) -> None:`. First line of body: `branch = _branch_for_path(path)`. Keep the `git rev-parse --verify refs/heads/{branch}` check (re-raise as `PetitionError("petition not found")` on failure). Keep `git checkout {branch}`. Replace the `git diff-tree` call that recovered the override path — you already have the path. Use it directly: `_run(["git", "rm", path], cwd=hc_root)`, `_run(["git", "commit", "-m", f"petition: withdraw {path}"], cwd=hc_root)`. Keep `_run(["gh", "pr", "close", "--delete-branch", branch], cwd=hc_root)`.

   Update the module-level docstring's `Public API` section to read `withdraw(path, *, hc_root)` and replace the `sorted by petition_id` phrase with `sorted by path`.

2. **`bin/honeycomb-mcp`.** In `PETITION_SUBMIT_DESCRIPTOR.description`, change `Returns {petition_id, branch, pr_url, overlay_path}.` to `Returns {branch, pr_url, overlay_path}.`. In `PETITION_WITHDRAW_DESCRIPTOR`, replace the property entry so `properties` becomes `{"path": {"type": "string", "description": "Relative path to the override file within $HONEYCOMB_ROOT — its identity per ADR-0002."}}` and `required` becomes `["path"]`. In `_handle_tools_call` under the `name == "palace_petition_withdraw"` branch: change the guard from `if "petition_id" not in arguments` to `if "path" not in arguments`, change the error message from `missing required argument: petition_id` to `missing required argument: path`, and change the dispatch call from `petitions.withdraw(petition_id=arguments["petition_id"], hc_root=root)` to `petitions.withdraw(path=arguments["path"], hc_root=root)`. Leave `PETITION_LIST_DESCRIPTOR` untouched (its description does not mention `petition_id`).

3. **`tests/test_petitions.py`.** Drop the `petition_id: str` keyword-only parameter and the `f"petition_id: {petition_id}\n"` line from `_write_override`. In `test_list_pending_merges_canon_and_overlay`: remove the `petition_id="..."` kwargs from the two `_write_override` calls; rewrite the two `next(... if r.petition_id == "...")` lookups to key on `r.target` (`"behaviour"` for canon, `"other"` for overlay); keep the `source` assertions. In `TestWithdraw.test_withdraw_removes_file_and_closes_pr`: drop the `petition_id` and `branch` locals; add `override_rel = "wing_bees/plan/foo-room/foo-closet/behaviour.queenfile_bees-v1.18.md"`; compute `expected_branch` in the test body using `hashlib.sha1(override_rel.encode("utf-8")).hexdigest()[:12]` so it matches `_branch_for_path`; the mock's `git diff-tree` stub stdout is no longer used (the new `withdraw` doesn't call diff-tree) but leaving the branch in the stub is harmless; replace `withdraw(petition_id=petition_id, hc_root=self.hc_root)` with `withdraw(path=override_rel, hc_root=self.hc_root)`; update the gh-close assertion to verify the computed branch appears in the recorded argv. Add `import hashlib` to the test module if not present.

4. **`tests/test_mcp_petitions.py`.** In `_STUB_PETITIONS_CODE`: remove `"petition_id": "p123",` from the `submit` return dict; change `def withdraw(petition_id, *, hc_root):` to `def withdraw(path, *, hc_root):` and the recorder call to `_record("withdraw", {"path": path})`. In `test_petition_submit_dispatches_to_helper`: delete the `self.assertEqual(result["petition_id"], "p123")` assertion; leave the other three result-key assertions.

5. **Add the failing test** from the "Failing test" section above into `tests/test_petitions.py` as a new method on `TestPetitionSubmit`. The `_build_mock` mock currently special-cases `git log -1 --format=%cI` — that branch becomes unreachable after your changes; leave it in (dead-code in a test mock is harmless) so other tests calling `_build_mock` continue to work.

**Verify locally:**

```
python3 -m pytest tests/
grep -nE "petition_id" lib/honeycomb/ bin/honeycomb-mcp
```

The grep must return zero matches in `lib/honeycomb/` and `bin/honeycomb-mcp`. (Matches in `tests/` are acceptable if they are intentional — e.g., assertions that the field is absent — but with the edits described above none should remain.)

**Do NOT:**

- Touch any file outside the four listed in Scope's `Edit:` list.
- Add backwards-compat shims, deprecation warnings, or accept `petition_id=` kwargs alongside the new `path=` parameter on `withdraw`. ADR-0002 framing supersedes the old identifier — the API moves cleanly.
- Update markdown docs under `wing_bees/` or `decisions/` — that is unit 004's job.
- Add `--no-verify` or skip hooks on commits.

## Success check

- `python3 -m pytest tests/` passes the full suite (with the new test added and the four edited tests adjusted).
- `grep -nE "petition_id" lib/honeycomb/ bin/honeycomb-mcp` returns zero matches.
- `grep -nE "petition_id" tests/` returns at most the intentional `assertNotIn("petition_id:", text)` assertion from the new test.
- `bin/honeycomb-mcp` `tools/list` returns 5 tools including `palace_petition_withdraw` with `inputSchema.required == ["path"]`.
- Diff review: `PetitionResult` and `PendingPetition` dataclasses no longer declare `petition_id`; `_build_override_content`'s returned string no longer contains `petition_id:`; `submit` no longer calls `git log -1 --format=%cI` or counts existing queenfiles; `withdraw`'s first body line is `branch = _branch_for_path(path)`; both `submit` and `withdraw` route through `_branch_for_path` (one shared helper, no inline duplication).

## Commit message

```
refactor(petitions): drop petition_id; identity is the override file path

PetitionResult and PendingPetition no longer carry petition_id;
.queenfile_*.md frontmatter no longer writes a petition_id line.
submit derives the branch deterministically from the override file's
relative path via SHA1; withdraw takes that path directly and recomputes
the same branch. Aligns the API with ADR-0002 ("path is identity") and
removes a fragile date-and-count derivation that depended on git log
state and queenfile file enumeration.

Refs: .bees/honeycomb-v1-1-fixups/specs/003-drop-petition-id-from-petitions-api.md
```
