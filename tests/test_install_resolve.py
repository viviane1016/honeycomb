"""Tests for materialize_flattened_view (spec 003)."""

import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from honeycomb.overrides import materialize_flattened_view, parse_override_file


def _tree_checksum(root: Path) -> str:
    """SHA-256 over sorted (relpath, file_contents) tuples."""
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            h.update(rel.encode("utf-8"))
            h.update(p.read_bytes())
    return h.hexdigest()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


_OVERRIDE_FMT = (
    "<!-- {filename}: override for {desc}.\n\n"
    "target: {target}\n"
    "tool: {tool}\n"
    'tool_version: "{tool_version}"\n'
    "consumer: null\n"
    "-->\n"
    "{body}\n"
)


class TestInstallResolve(unittest.TestCase):

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _canon(self) -> Path:
        return Path(self._tmp.name) / "canon"

    def _target(self) -> Path:
        return Path(self._tmp.name) / "target"

    # ------------------------------------------------------------------

    def test_default_flags_preserves_canon(self) -> None:
        canon = self._canon()
        drawer = canon / "wing_foo" / "room_a" / "closet_x" / "drawer1.md"
        _write(drawer, "canonical drawer content\n")

        target = self._target()
        report = materialize_flattened_view(canon, target, {})

        target_file = target / "wing_foo" / "room_a" / "closet_x" / "drawer1.md"
        self.assertTrue(target_file.exists())
        self.assertEqual(target_file.read_bytes(), drawer.read_bytes())
        self.assertEqual(report.overrides_used, {})

    def test_override_wins_when_axes_match(self) -> None:
        canon = self._canon()
        closet_dir = canon / "wing_foo" / "room_a" / "closet_x"
        canon_drawer = closet_dir / "drawer1.md"
        override_file = closet_dir / "drawer1.queenfile_bees-v1.18.md"
        _write(canon_drawer, "canonical body\n")
        _write(
            override_file,
            _OVERRIDE_FMT.format(
                filename="drawer1.queenfile_bees-v1.18.md",
                desc="bees v1.18",
                target="drawer1",
                tool="bees",
                tool_version="v1.18",
                body="bees v1.18 override body",
            ),
        )

        target = self._target()
        report = materialize_flattened_view(
            canon, target, {"tool": "bees", "tool_version": "v1.18"}
        )

        # The materialized drawer must equal the override body (header stripped)
        spec = parse_override_file(override_file)
        target_drawer = target / "wing_foo" / "room_a" / "closet_x" / "drawer1.md"
        self.assertTrue(target_drawer.exists())
        expected = spec.body.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        self.assertEqual(target_drawer.read_bytes(), expected)

        # Override file must not appear in target
        self.assertFalse(
            (target / "wing_foo" / "room_a" / "closet_x" / "drawer1.queenfile_bees-v1.18.md").exists()
        )

        # Report records the substitution
        rel_key = "wing_foo/room_a/closet_x/drawer1.md"
        self.assertIn(rel_key, report.overrides_used)
        self.assertEqual(report.overrides_used[rel_key], "drawer1.queenfile_bees-v1.18.md")

    def test_idempotent_in_place_materialization(self) -> None:
        # Build a canon tree with one override sibling
        canon = self._canon()
        closet_dir = canon / "wing_foo" / "room_a" / "closet_x"
        _write(closet_dir / "drawer1.md", "canonical body\n")
        _write(
            closet_dir / "drawer1.queenfile_bees-v1.18.md",
            _OVERRIDE_FMT.format(
                filename="drawer1.queenfile_bees-v1.18.md",
                desc="bees v1.18",
                target="drawer1",
                tool="bees",
                tool_version="v1.18",
                body="bees v1.18 override body",
            ),
        )

        # Copy to a fresh tmp so in_place operates on it
        work = Path(self._tmp.name) / "work"
        shutil.copytree(str(canon), str(work))

        ctx = {"tool": "bees", "tool_version": "v1.18"}
        materialize_flattened_view(work, work, ctx)
        checksum1 = _tree_checksum(work)

        materialize_flattened_view(work, work, ctx)
        checksum2 = _tree_checksum(work)

        self.assertEqual(checksum1, checksum2)

    def test_default_context_keeps_canonical_drawer_when_overrides_present(self) -> None:
        canon = self._canon()
        closet_dir = canon / "wing_foo" / "room_a" / "closet_x"
        canon_drawer = closet_dir / "drawer1.md"
        _write(canon_drawer, "canonical drawer body\n")
        _write(
            closet_dir / "drawer1.queenfile_other-v1.0.md",
            _OVERRIDE_FMT.format(
                filename="drawer1.queenfile_other-v1.0.md",
                desc="other v1.0",
                target="drawer1",
                tool="other",
                tool_version="v1.0",
                body="other override body",
            ),
        )

        target = self._target()
        report = materialize_flattened_view(canon, target, {})

        target_drawer = target / "wing_foo" / "room_a" / "closet_x" / "drawer1.md"
        self.assertEqual(target_drawer.read_bytes(), canon_drawer.read_bytes())
        self.assertIn("wing_foo/room_a/closet_x/drawer1.md", report.canonical_kept)

    def test_non_drawer_files_copied_verbatim(self) -> None:
        canon = self._canon()
        closet_dir = canon / "wing_foo" / "room_a" / "closet_x"
        _write(closet_dir / "closet.md", "closet description\n")
        _write(closet_dir / "index.md", "index content\n")
        _write(closet_dir / "drawer1.md", "drawer1 content\n")

        target = self._target()
        materialize_flattened_view(canon, target, {})

        for name in ("closet.md", "index.md", "drawer1.md"):
            src = closet_dir / name
            dst = target / "wing_foo" / "room_a" / "closet_x" / name
            self.assertTrue(dst.exists(), f"{name} missing from target")
            self.assertEqual(dst.read_bytes(), src.read_bytes(), f"{name} bytes differ")


if __name__ == "__main__":
    unittest.main()
