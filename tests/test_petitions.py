"""Tests for honeycomb.petitions (spec 006)."""

import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))

import honeycomb.petitions as pet_mod
from honeycomb.petitions import (
    PetitionError,
    submit,
    list_pending,
    withdraw,
)


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _make_cp(argv, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=argv, returncode=returncode, stdout=stdout, stderr=stderr)


class TestPetitionSubmit(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.hc_root = pathlib.Path(self._tmpdir.name) / "canon"
        self.hc_root.mkdir()
        self.overlay_root = pathlib.Path(self._tmpdir.name) / "overlay"
        self.overlay_root.mkdir()

        drawer_dir = self.hc_root / "wing_bees" / "plan" / "foo-room" / "foo-closet"
        drawer_dir.mkdir(parents=True)
        (drawer_dir / "behaviour.md").write_text("# behaviour\n", encoding="utf-8")

        _git("init", cwd=self.hc_root)
        _git("config", "user.email", "test@example.com", cwd=self.hc_root)
        _git("config", "user.name", "Test", cwd=self.hc_root)
        _git("add", ".", cwd=self.hc_root)
        _git("commit", "-m", "init: seed drawer", cwd=self.hc_root)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _build_mock(self):
        """Return (mock_run, calls_list). mock_run intercepts all _run calls."""
        calls = []

        def mock_run(argv, *, cwd):
            calls.append(list(argv))
            stdout = ""
            if argv[:4] == ["git", "log", "-1", "--format=%cI"]:
                stdout = "2026-05-30T12:00:00+00:00\n"
            elif argv[:3] == ["gh", "pr", "create"]:
                stdout = "https://github.com/org/repo/pull/42\n"
            return _make_cp(argv, stdout=stdout)

        return mock_run, calls

    def test_submit_writes_override_and_invokes_gh(self):
        mock_run, calls = self._build_mock()

        with patch.object(pet_mod, "_run", mock_run):
            result = submit(
                target="behaviour",
                content="override body",
                rationale="testing",
                context={"tool": "bees", "tool_version": "v1.18", "consumer": None},
                hc_root=self.hc_root,
                overlay_root=self.overlay_root,
            )

        override_path = (
            self.hc_root
            / "wing_bees" / "plan" / "foo-room" / "foo-closet"
            / "behaviour.queenfile_bees-v1.18.md"
        )
        self.assertTrue(override_path.exists(), "override file must exist in canon")
        text = override_path.read_text()
        self.assertIn("testing", text)
        self.assertIn("override body", text)

        self.assertEqual(result.pr_url, "https://github.com/org/repo/pull/42")

        self.assertIsNotNone(result.overlay_path)
        self.assertTrue(result.overlay_path.exists(), "overlay file must exist")
        rel = override_path.relative_to(self.hc_root)
        self.assertEqual(result.overlay_path, self.overlay_root / rel)

        checkout_idx = next(
            (i for i, a in enumerate(calls) if a[:3] == ["git", "checkout", "-b"]), None
        )
        commit_idx = next(
            (i for i, a in enumerate(calls) if a[:2] == ["git", "commit"]), None
        )
        gh_pr_idx = next(
            (i for i, a in enumerate(calls) if a[:3] == ["gh", "pr", "create"]), None
        )
        self.assertIsNotNone(checkout_idx, "must call git checkout -b")
        self.assertIsNotNone(commit_idx, "must call git commit")
        self.assertIsNotNone(gh_pr_idx, "must call gh pr create")
        self.assertLess(checkout_idx, gh_pr_idx, "checkout must precede gh pr create")
        self.assertLess(commit_idx, gh_pr_idx, "commit must precede gh pr create")

    def test_submit_raises_when_gh_missing(self):
        mock_run, _ = self._build_mock()

        def patched_run(argv, *, cwd):
            if argv[:2] == ["which", "gh"]:
                raise PetitionError("which failed: gh not found")
            return mock_run(argv, cwd=cwd)

        with patch.object(pet_mod, "_run", patched_run):
            with self.assertRaises(PetitionError) as ctx:
                submit(
                    target="behaviour",
                    content="override body",
                    rationale="testing",
                    context={"tool": "bees", "tool_version": "v1.18", "consumer": None},
                    hc_root=self.hc_root,
                    overlay_root=None,
                )
        self.assertIn("gh CLI not found", str(ctx.exception))


class TestListPending(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.hc_root = pathlib.Path(self._tmpdir.name) / "canon"
        self.hc_root.mkdir()
        self.overlay_root = pathlib.Path(self._tmpdir.name) / "overlay"
        self.overlay_root.mkdir()

    def tearDown(self):
        self._tmpdir.cleanup()

    def _write_override(
        self,
        root: pathlib.Path,
        rel_path: str,
        *,
        petition_id: str,
        target: str,
        tool: str = "null",
        tool_version: str = "null",
        consumer: str = "null",
        rationale: str = "test rationale",
    ) -> pathlib.Path:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"<!-- {path.name}\n"
            f"target: {target}\n"
            f"tool: {tool}\n"
            f"tool_version: {tool_version}\n"
            f"consumer: {consumer}\n"
            f"petition_id: {petition_id}\n"
            f"rationale: |\n"
            f"  {rationale}\n"
            f"-->\n\n"
            f"body\n",
            encoding="utf-8",
        )
        return path

    def test_list_pending_merges_canon_and_overlay(self):
        self._write_override(
            self.hc_root,
            "wing_bees/plan/foo-room/foo-closet/behaviour.queenfile_bees-v1.18.md",
            petition_id="20260530-000-bees-v1.18",
            target="behaviour",
            tool="bees",
            tool_version="v1.18",
            rationale="canon rationale",
        )
        self._write_override(
            self.overlay_root,
            "wing_bees/plan/foo-room/foo-closet/other.queenfile_tool-v1.0.md",
            petition_id="20260530-001-tool-v1.0",
            target="other",
            tool="tool",
            tool_version="v1.0",
            rationale="overlay rationale",
        )

        results = list_pending(
            consumer=None, hc_root=self.hc_root, overlay_root=self.overlay_root
        )

        self.assertEqual(len(results), 2, f"expected 2 results, got {results}")

        canon_entry = next(
            (r for r in results if r.petition_id == "20260530-000-bees-v1.18"), None
        )
        overlay_entry = next(
            (r for r in results if r.petition_id == "20260530-001-tool-v1.0"), None
        )

        self.assertIsNotNone(canon_entry, "canon entry missing")
        self.assertIsNotNone(overlay_entry, "overlay entry missing")
        self.assertEqual(canon_entry.source, "canon")
        self.assertEqual(overlay_entry.source, "overlay")


class TestWithdraw(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.hc_root = pathlib.Path(self._tmpdir.name) / "canon"
        self.hc_root.mkdir()

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_withdraw_removes_file_and_closes_pr(self):
        petition_id = "20260530-000-bees-v1.18"
        branch = f"feat/petition-{petition_id}"
        override_rel = "wing_bees/plan/foo-room/foo-closet/behaviour.queenfile_bees-v1.18.md"

        calls = []

        def mock_run(argv, *, cwd):
            calls.append(list(argv))
            stdout = ""
            if argv[:4] == ["git", "diff-tree", "--no-commit-id", "--name-only"]:
                stdout = f"{override_rel}\n"
            return _make_cp(argv, stdout=stdout)

        with patch.object(pet_mod, "_run", mock_run):
            withdraw(petition_id=petition_id, hc_root=self.hc_root)

        rm_calls = [a for a in calls if a[:2] == ["git", "rm"]]
        self.assertTrue(rm_calls, f"expected git rm call; got {calls}")

        commit_calls = [a for a in calls if a[:2] == ["git", "commit"]]
        self.assertTrue(commit_calls, "expected git commit call")

        gh_close_calls = [
            a for a in calls
            if a[:3] == ["gh", "pr", "close"] and "--delete-branch" in a
        ]
        self.assertTrue(gh_close_calls, f"expected gh pr close --delete-branch; got {calls}")
        self.assertIn(branch, gh_close_calls[0])


if __name__ == "__main__":
    unittest.main()
