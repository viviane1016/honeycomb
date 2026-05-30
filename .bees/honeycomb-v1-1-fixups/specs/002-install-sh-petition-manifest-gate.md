---
output-files:
  - tools/install.sh
  - tests/test_install_no_op.py
scribe-model: claude-opus-4-7
---

# Spec 002 — Gate install.sh petition-manifest emission and renumber duplicate section

## Builder model

claude-sonnet-4-6

## Goal

Make `tools/install.sh` byte-identical across re-runs when canon hasn't moved: skip the petition-manifest write and the `Petitions:` summary line entirely on no-op installs, suppress the summary line on fresh installs, and fix the duplicate `# ── 4.` section number.

## Scope

**Edit `tools/install.sh`:**

- Parameterise the clone URL: change `REPO="https://github.com/viviane1016/honeycomb.git"` to `REPO="${HONEYCOMB_REPO:-https://github.com/viviane1016/honeycomb.git}"` so tests can point at a local-bare-repo fixture.
- Rewrite the `# ── 4. Petition manifest` block to obey three cases:
  - **Case A — no-op install** (`PREVIOUS_SHA` non-empty AND `PREVIOUS_SHA == CURRENT_SHA`): skip the entire block. No `.petition-manifest.json` write. No `Petitions:` stdout. No `warn` either.
  - **Case B — fresh install** (`PREVIOUS_SHA` empty): run the Python snippet to write `.petition-manifest.json` (with `previous_sha=null`), but do NOT call `step "$PETITION_SUMMARY"`. The summary line is suppressed on first install.
  - **Case C — update install** (both `PREVIOUS_SHA` and `CURRENT_SHA` non-empty AND they differ): run the Python snippet and print the summary via `step "$PETITION_SUMMARY"`, exactly as today.
- The existing `warn "petition manifest generation failed (continuing)"` path applies only when the manifest block actually runs (Cases B and C) and the Python snippet errors.
- Renumber the second `# ── 4. Always reindex ────────────────────────────────────────────────────────` divider comment to `# ── 5. Always reindex ────────────────────────────────────────────────────────`.
- Update the top-of-file `# Artifacts:` comment block to reflect the new behaviour: the manifest is written on first install (without summary) and on canon-update installs (with summary); a no-op install writes nothing.

**Create `tests/test_install_no_op.py`:**

- Construct a temporary local-bare-repo fixture: `git init --bare` a directory, then in a sibling working copy add a minimal canon shape (a `VERSION` file containing `0.0.0-test`, a `tools/build_index.py` shim that exits 0 quickly, a `lib/honeycomb/manifest.py` copied or imported from canon — see note below), commit, tag `v0.0.0-test`, and push to the bare repo.
- Set env `HONEYCOMB_INSTALL_DIR=<tmp1>`, `HONEYCOMB_REPO=file://<bare-repo-path>`, `HONEYCOMB_TAG=v0.0.0-test`, then invoke `bash tools/install.sh` capturing stdout. This is run 1 (fresh install).
- Invoke `bash tools/install.sh` a second time with the same env (Case A — no-op install). Capture stdout.
- Snapshot the install root after each run: a deterministic directory hash that walks files in sorted order and hashes each `(relative_path, content_bytes)` pair. Ignore mtime — git checkout updates mtimes even when content is identical.
- Assertions:
  - The directory-content hash from run 2 equals the hash from run 1 (no `.petition-manifest.json` rewrite, no other drift).
  - `"Petitions:"` does NOT appear in run-2 stdout.
  - `"Petitions:"` does NOT appear in run-1 stdout either (fresh install suppresses summary).
- The test must be skip-able when `git` or `bash` is missing from `$PATH` (use `unittest.skipUnless`).

**Note on the test fixture's `lib/honeycomb/manifest.py`:** the install.sh manifest block does `PYTHONPATH="$TARGET/lib" python3 -c "from honeycomb.manifest import …"`. For the local fixture, the simplest reliable approach is to copy the repo's current `lib/honeycomb/manifest.py` (and an empty `lib/honeycomb/__init__.py` if needed) into the fixture working tree before tagging, so the install-time Python import finds the real generator. Use `shutil.copy` from the test's repo-root reference (walk up from `__file__`).

**Non-goals:**

- Do not touch `lib/honeycomb/manifest.py` — gate logic lives in shell, not Python.
- Do not change the manifest schema or `summary_line` output format.
- Do not add CLI flags to install.sh beyond the `HONEYCOMB_REPO` env override (which is environment-driven, not a flag).

## Failing test

`tests/test_install_no_op.py::TestInstallNoOp::test_second_install_is_byte_identical_and_silent`

Before the builder runs: file does not exist, so the test does not exist — `python3 -m pytest tests/test_install_no_op.py` reports "no tests ran" (effectively failing the spec's success check). After the builder runs: the test file exists and the test passes against the modified `tools/install.sh`.

A secondary test in the same file, `test_first_install_writes_manifest_without_summary`, asserts that run 1's stdout omits `"Petitions:"` while `.petition-manifest.json` exists in the install root with `previous_sha == null`.

## Builder prompt

You are implementing spec 002 of the honeycomb v1.1 fixups. The current `tools/install.sh` has two problems flagged by `bees accept` on PR #4:

1. The `# ── 4. Petition manifest` block writes `.petition-manifest.json` and prints a `Petitions:` line on every install — including no-op installs (re-running install.sh on an unchanged canon), which breaks the "byte-identical-to-v1.0 for a no-change canon" install acceptance bullet.
2. Two adjacent section dividers are both labelled `# ── 4.` — cosmetic but visible.

**Edit `tools/install.sh`:**

1. Change `REPO="https://github.com/viviane1016/honeycomb.git"` to `REPO="${HONEYCOMB_REPO:-https://github.com/viviane1016/honeycomb.git}"` so the test can point at a local-bare-repo fixture.

2. Rewrite the `# ── 4. Petition manifest` block to gate on three cases. Pseudocode:

   ```
   CURRENT_SHA="$(git -C "$TARGET" rev-parse HEAD 2>/dev/null || echo "")"
   if [ -z "$CURRENT_SHA" ]; then
       :  # nothing to do — not a git checkout
   elif [ -n "$PREVIOUS_SHA" ] && [ "$PREVIOUS_SHA" = "$CURRENT_SHA" ]; then
       :  # Case A — no-op install. Skip everything.
   else
       # Cases B (fresh) and C (update) — write the manifest.
       PREV_ARG="${PREVIOUS_SHA:-}"
       if PETITION_SUMMARY="$(PYTHONPATH="$TARGET/lib" python3 -c "…same python as today…" "$PREV_ARG" "$CURRENT_SHA" "$TARGET")"; then
           # Only print the summary on Case C — when PREVIOUS_SHA is non-empty.
           if [ -n "$PREVIOUS_SHA" ]; then
               step "$PETITION_SUMMARY"
           fi
       else
           warn "petition manifest generation failed (continuing)"
       fi
   fi
   ```

   Keep the embedded Python snippet exactly as it is today — it calls `generate_manifest`, `write_manifest`, and `summary_line`, and prints the summary line. The shell wrapper decides whether to display that line.

3. Renumber the second divider from `# ── 4. Always reindex ───…` to `# ── 5. Always reindex ───…`. Section numbers must be monotonically increasing and unique: 1, 2, 3, 4, 5.

4. Update the `# Artifacts:` comment block near the top of the file (the lines describing `.petition-manifest.json`) to say the manifest is written on first install (without a summary line) and on canon-update installs (with a summary line); skipped entirely on no-op re-runs.

**Create `tests/test_install_no_op.py`:**

```python
"""Tests that re-running install.sh against an unchanged canon is byte-identical
and silent — no .petition-manifest.json rewrite, no `Petitions:` stdout line."""

import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _have(cmd):
    return shutil.which(cmd) is not None


def _run(args, cwd=None, env=None, check=True):
    return subprocess.run(
        args, cwd=cwd, env=env, check=check, capture_output=True, text=True
    )


def _dir_content_hash(root: pathlib.Path) -> str:
    """Hash of (relative path, content) pairs — ignores mtime."""
    h = hashlib.sha256()
    files = sorted(p for p in root.rglob("*") if p.is_file())
    for p in files:
        rel = p.relative_to(root).as_posix()
        h.update(rel.encode())
        h.update(b"\x00")
        h.update(p.read_bytes())
        h.update(b"\x01")
    return h.hexdigest()


def _make_fixture(workdir: pathlib.Path) -> pathlib.Path:
    """Build a bare repo with a minimal canon-shape tagged v0.0.0-test.
    Returns the path to the bare repo (suitable for cloning via file://)."""
    src = workdir / "src"
    src.mkdir()
    # Copy the real manifest module so install.sh's embedded python import works.
    (src / "lib" / "honeycomb").mkdir(parents=True)
    (src / "lib" / "honeycomb" / "__init__.py").write_text("")
    shutil.copy(
        REPO_ROOT / "lib" / "honeycomb" / "manifest.py",
        src / "lib" / "honeycomb" / "manifest.py",
    )
    # Minimal build_index that exits 0 so install.sh's reindex step succeeds.
    (src / "tools").mkdir()
    (src / "tools" / "build_index.py").write_text(
        "import sys\nsys.exit(0)\n"
    )
    (src / "VERSION").write_text("0.0.0-test\n")
    _run(["git", "init", "-q", "-b", "main"], cwd=src)
    _run(["git", "config", "user.email", "t@t.t"], cwd=src)
    _run(["git", "config", "user.name", "t"], cwd=src)
    _run(["git", "add", "."], cwd=src)
    _run(["git", "commit", "-q", "-m", "init"], cwd=src)
    _run(["git", "tag", "v0.0.0-test"], cwd=src)
    bare = workdir / "canon.git"
    _run(["git", "clone", "-q", "--bare", str(src), str(bare)])
    return bare


@unittest.skipUnless(_have("bash") and _have("git") and _have("python3"),
                     "requires bash, git, python3")
class TestInstallNoOp(unittest.TestCase):

    def test_second_install_is_byte_identical_and_silent(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = pathlib.Path(td)
            bare = _make_fixture(tdp)
            install_dir = tdp / "install"

            env = dict(os.environ)
            env["HONEYCOMB_INSTALL_DIR"] = str(install_dir)
            env["HONEYCOMB_REPO"] = f"file://{bare}"
            env["HONEYCOMB_TAG"] = "v0.0.0-test"

            r1 = _run(
                ["bash", str(REPO_ROOT / "tools" / "install.sh")],
                env=env,
            )
            hash1 = _dir_content_hash(install_dir)

            r2 = _run(
                ["bash", str(REPO_ROOT / "tools" / "install.sh")],
                env=env,
            )
            hash2 = _dir_content_hash(install_dir)

            self.assertEqual(
                hash1, hash2,
                "second install changed the install root",
            )
            self.assertNotIn(
                "Petitions:", r2.stdout,
                f"no-op install printed Petitions: line\nstdout:\n{r2.stdout}",
            )

    def test_first_install_writes_manifest_without_summary(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = pathlib.Path(td)
            bare = _make_fixture(tdp)
            install_dir = tdp / "install"

            env = dict(os.environ)
            env["HONEYCOMB_INSTALL_DIR"] = str(install_dir)
            env["HONEYCOMB_REPO"] = f"file://{bare}"
            env["HONEYCOMB_TAG"] = "v0.0.0-test"

            r = _run(
                ["bash", str(REPO_ROOT / "tools" / "install.sh")],
                env=env,
            )
            manifest_path = install_dir / ".petition-manifest.json"
            self.assertTrue(
                manifest_path.exists(),
                "fresh install should write .petition-manifest.json",
            )
            import json
            data = json.loads(manifest_path.read_text())
            self.assertIsNone(
                data["previous_sha"],
                "fresh install manifest should have previous_sha=null",
            )
            self.assertNotIn(
                "Petitions:", r.stdout,
                f"fresh install printed Petitions: line\nstdout:\n{r.stdout}",
            )


if __name__ == "__main__":
    unittest.main()
```

**Verification steps:**

1. `python3 -m pytest tests/test_install_no_op.py -v` — both tests pass.
2. `python3 -m pytest tests/` — no other tests regressed.
3. `grep -nE '^# ── [0-9]\.' tools/install.sh` — five distinct lines, numbered 1 through 5 with no duplicates.
4. `grep -nE '^REPO=' tools/install.sh` — exactly one line, using `"${HONEYCOMB_REPO:-…}"`.

**Constraints:**

- Do not modify `lib/honeycomb/manifest.py`. The Python summary line still includes `(no canon update — 0 commits in range)` for Case A inputs — that branch is unreachable from install.sh after this change but stays available for other callers and the existing `tests/test_manifest.py::test_summary_line_no_change` test.
- The embedded Python snippet inside install.sh must keep its current shape (calls `generate_manifest`, `write_manifest`, `summary_line`, prints summary). Only the surrounding bash conditionals change.
- Keep `set -eu` discipline — every variable reference inside the new conditionals must be either initialised or use `${VAR:-}` defaulting.
- Test must work without network access — the `file://` clone is purely local.

## Success check

- `python3 -m pytest tests/test_install_no_op.py` — both tests pass.
- `python3 -m pytest tests/` — all tests pass; no regressions in `test_manifest.py`.
- `grep -c '^# ── 4\.' tools/install.sh` returns `1` (was `2` before this spec).
- `grep -c '^# ── 5\.' tools/install.sh` returns `1`.
- Diff review: install.sh has three clearly-distinguished branches (skip / write-without-summary / write-with-summary) and a single `REPO="${HONEYCOMB_REPO:-…}"` line at the top.

## Commit message

```
fix(install): gate petition-manifest emission and renumber sections (#002)

Re-running install.sh against an unchanged canon now skips the
.petition-manifest.json write and the `Petitions:` stdout line entirely,
making no-op installs byte-identical to v1.0. Fresh installs still write
the manifest (with previous_sha=null) but suppress the summary line —
there's no prior range to summarise. Only canon-update installs print
the operator summary.

Also fixes the duplicate `# ── 4.` section divider — `Always reindex`
is now correctly numbered `# ── 5.`.

Adds HONEYCOMB_REPO env override so the new tests/test_install_no_op.py
can drive install.sh against a local-bare-repo fixture without network.

Refs: .bees/honeycomb-v1-1-fixups/specs/002-install-sh-petition-manifest-gate.md
```
