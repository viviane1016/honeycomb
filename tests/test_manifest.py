"""Tests for honeycomb.manifest (spec 009)."""

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))

from honeycomb.manifest import generate_manifest, write_manifest, summary_line


def _run(args, cwd):
    subprocess.run(args, cwd=str(cwd), check=True, capture_output=True)


def _init_repo(tmpdir):
    repo = pathlib.Path(tmpdir)
    _run(["git", "init", "-q", "-b", "main"], repo)
    _run(["git", "config", "user.email", "t@t.t"], repo)
    _run(["git", "config", "user.name", "t"], repo)
    _run(["git", "commit", "--allow-empty", "-m", "init"], repo)
    return repo


def _commit(repo, subject):
    _run(["git", "commit", "--allow-empty", "-m", subject], repo)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo), check=True, capture_output=True, text=True,
    ).stdout.strip()


def _head(repo):
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo), check=True, capture_output=True, text=True,
    ).stdout.strip()


class TestManifest(unittest.TestCase):

    def test_generate_manifest_classifies_three_prefixes(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(td)
            prev = _head(repo)
            sha_adopted = _commit(repo, "petition: adopted drawer-a for bees-v1.18")
            sha_declined = _commit(repo, "petition: declined drawer-b for bees-v1.18")
            sha_pending = _commit(repo, "petition: pending drawer-c for scarab")
            curr = _head(repo)

            m = generate_manifest(repo, prev, curr)

            self.assertEqual(len(m["accepted"]), 1)
            self.assertEqual(m["accepted"][0]["sha"], sha_adopted)
            self.assertEqual(m["accepted"][0]["subject"], "petition: adopted drawer-a for bees-v1.18")

            self.assertEqual(len(m["declined"]), 1)
            self.assertEqual(m["declined"][0]["sha"], sha_declined)
            self.assertEqual(m["declined"][0]["subject"], "petition: declined drawer-b for bees-v1.18")

            self.assertEqual(len(m["pending"]), 1)
            self.assertEqual(m["pending"][0]["sha"], sha_pending)
            self.assertEqual(m["pending"][0]["subject"], "petition: pending drawer-c for scarab")

            self.assertEqual(m["warnings"], [])

    def test_generate_manifest_empty_when_prev_is_none(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(td)
            curr = _head(repo)
            m = generate_manifest(repo, None, curr)
            self.assertEqual(m["accepted"], [])
            self.assertEqual(m["declined"], [])
            self.assertEqual(m["pending"], [])

    def test_generate_manifest_empty_when_prev_equals_curr(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(td)
            curr = _head(repo)
            m = generate_manifest(repo, curr, curr)
            self.assertEqual(m["accepted"], [])
            self.assertEqual(m["declined"], [])
            self.assertEqual(m["pending"], [])

    def test_generate_manifest_non_petition_commits_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(td)
            prev = _head(repo)
            _commit(repo, "chore: tidy")
            _commit(repo, "fix: typo")
            curr = _head(repo)
            m = generate_manifest(repo, prev, curr)
            self.assertEqual(m["accepted"], [])
            self.assertEqual(m["declined"], [])
            self.assertEqual(m["pending"], [])

    def test_generate_manifest_misclassified_falls_into_pending(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(td)
            prev = _head(repo)
            sha = _commit(repo, "petition: maybe-adopt drawer-x")
            curr = _head(repo)
            m = generate_manifest(repo, prev, curr)
            self.assertEqual(len(m["pending"]), 1)
            self.assertEqual(m["pending"][0]["sha"], sha)
            self.assertEqual(len(m["warnings"]), 1)
            self.assertIn(sha[:8], m["warnings"][0])

    def test_generate_manifest_handles_git_failure(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(td)
            curr = _head(repo)
            bad_sha = "0" * 40
            m = generate_manifest(repo, bad_sha, curr)
            self.assertEqual(m["accepted"], [])
            self.assertEqual(m["declined"], [])
            self.assertEqual(m["pending"], [])
            self.assertEqual(len(m["warnings"]), 1)
            self.assertTrue(m["warnings"][0].startswith("git-log-failed:"))

    def test_write_manifest_atomic(self):
        with tempfile.TemporaryDirectory() as td:
            dest = pathlib.Path(td) / "sub" / "manifest.json"
            m = {
                "accepted": [{"sha": "abc", "subject": "s"}],
                "declined": [],
                "pending": [],
                "previous_sha": "prev",
                "current_sha": "curr",
                "warnings": [],
            }
            write_manifest(m, dest)
            self.assertTrue(dest.exists())
            loaded = json.loads(dest.read_text())
            self.assertEqual(loaded, m)

    def test_summary_line_first_install(self):
        m = {"accepted": [], "declined": [], "pending": [],
             "previous_sha": None, "current_sha": "abc", "warnings": []}
        result = summary_line(m, None)
        self.assertTrue(result.endswith("(first install — no prior range to scan)"))

    def test_summary_line_no_change(self):
        m = {"accepted": [], "declined": [], "pending": [],
             "previous_sha": "abc", "current_sha": "abc", "warnings": []}
        result = summary_line(m, "abc")
        self.assertIn("(no canon update — 0 commits in range)", result)

    def test_summary_line_normal(self):
        m = {
            "accepted": [{"sha": "s1", "subject": "x"}, {"sha": "s2", "subject": "y"}],
            "declined": [{"sha": "s3", "subject": "z"}],
            "pending": [],
            "previous_sha": "abcdef1234567890",
            "current_sha": "xyz",
            "warnings": [],
        }
        result = summary_line(m, "abcdef1234567890")
        self.assertEqual(result, "Petitions: 2 accepted, 1 declined, 0 pending since abcdef12")

    def test_summary_line_with_warnings(self):
        m = {"accepted": [], "declined": [], "pending": [],
             "previous_sha": "abcdef12", "current_sha": "xyz",
             "warnings": ["convention-not-followed: 1234abcd"]}
        result = summary_line(m, "abcdef12")
        self.assertTrue(result.endswith("[warnings: 1]"))


if __name__ == "__main__":
    unittest.main()
