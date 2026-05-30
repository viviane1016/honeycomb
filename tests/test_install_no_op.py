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
    """Hash of (relative path, content) pairs — ignores mtime and .git internals."""
    h = hashlib.sha256()
    files = sorted(
        p for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    )
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
