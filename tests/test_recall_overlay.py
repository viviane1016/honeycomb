"""Tests for consumer overlay support in palace_recall and palace_recall_semantic."""

from __future__ import annotations

import sys
import os
import tempfile
import unittest
from pathlib import Path

# Ensure lib/ is on the path when run directly.
_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from honeycomb.recall import palace_recall


def _make_closet(root: Path, wing: str, room: str, closet: str, text: str) -> None:
    """Create a minimal closet directory with a closet.md."""
    d = root / wing / room / closet
    d.mkdir(parents=True, exist_ok=True)
    (d / "closet.md").write_text(text, encoding="utf-8")


class TestNoOverlay(unittest.TestCase):
    """palace_recall with no overlay must behave identically to v1.0."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.canon = Path(self._td.name) / "canon"
        _make_closet(self.canon, "wing_bees", "plan", "sample", "canon body text")

    def tearDown(self):
        self._td.cleanup()

    def test_no_overlay_matches_v1_behaviour(self):
        """Omitting overlay_root and passing overlay_root=None produce identical results."""
        res_implicit = palace_recall("sample", root=self.canon)
        res_explicit = palace_recall("sample", root=self.canon, overlay_root=None)
        self.assertEqual(len(res_implicit), len(res_explicit))
        for a, b in zip(res_implicit, res_explicit):
            self.assertEqual(a["closet"], b["closet"])
            self.assertEqual(a["wing"], b["wing"])
            self.assertEqual(a["room"], b["room"])

    def test_no_overlay_returns_canon_text(self):
        """Without overlay, canon closet text is returned."""
        res = palace_recall("sample", root=self.canon)
        self.assertTrue(any("canon body text" in r["closet"] for r in res))


class TestOverlayWins(unittest.TestCase):
    """Overlay closet replaces canon at the same (wing, room, closet) key."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.canon = Path(self._td.name) / "canon"
        self.overlay = Path(self._td.name) / "overlay"
        _make_closet(self.canon, "wing_bees", "plan", "sample", "canon body")
        _make_closet(self.overlay, "wing_bees", "plan", "sample", "overlay body")

    def tearDown(self):
        self._td.cleanup()

    def test_overlay_drawer_wins_over_canon(self):
        """This is the spec's named failing test."""
        results = palace_recall("sample", root=self.canon, overlay_root=self.overlay, drawer=True)
        self.assertTrue(results, "expected at least one result")
        first = results[0]
        self.assertIn("overlay body", first["closet"])
        self.assertNotIn("canon body", first["closet"])


class TestOverlayOnlyCloset(unittest.TestCase):
    """An overlay-only closet (not in canon) surfaces in results."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.canon = Path(self._td.name) / "canon"
        self.overlay = Path(self._td.name) / "overlay"
        # Canon has closet A; overlay has closet B (different room/closet).
        _make_closet(self.canon, "wing_bees", "plan", "alpha", "alpha text")
        _make_closet(self.overlay, "wing_bees", "build", "beta", "beta text")

    def tearDown(self):
        self._td.cleanup()

    def test_overlay_only_closet_surfaces(self):
        results = palace_recall("beta", root=self.canon, overlay_root=self.overlay)
        texts = [r["closet"] for r in results]
        self.assertTrue(any("beta text" in t for t in texts),
                        f"overlay-only closet not in results: {texts}")


class TestOverlayPathMissing(unittest.TestCase):
    """A non-existent overlay_root falls through to canon without error."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.canon = Path(self._td.name) / "canon"
        _make_closet(self.canon, "wing_bees", "plan", "sample", "canon only")

    def tearDown(self):
        self._td.cleanup()

    def test_overlay_path_missing_falls_through(self):
        missing = Path("/tmp/definitely-does-not-exist-12345")
        # Must not raise.
        results = palace_recall("sample", root=self.canon, overlay_root=missing)
        self.assertTrue(results, "expected canon results when overlay is missing")
        self.assertTrue(any("canon only" in r["closet"] for r in results))


class TestQueenfileSuffixStrip(unittest.TestCase):
    """queenfile_<scope> suffix in closet directory name is stripped for merge key."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.canon = Path(self._td.name) / "canon"
        self.overlay = Path(self._td.name) / "overlay"

    def tearDown(self):
        self._td.cleanup()

    def test_no_suffix_overlay_replaces_canon(self):
        """Overlay directory without suffix replaces canon closet at same key."""
        _make_closet(self.canon, "wing_bees", "plan", "sample", "canon text")
        _make_closet(self.overlay, "wing_bees", "plan", "sample", "overlay text no suffix")
        results = palace_recall("sample", root=self.canon, overlay_root=self.overlay)
        texts = [r["closet"] for r in results]
        self.assertTrue(any("overlay text no suffix" in t for t in texts))
        self.assertFalse(any("canon text" in t for t in texts))

    def test_queenfile_suffix_strips_for_merge_key(self):
        """Overlay directory named sample.queenfile_bees merges with canon 'sample'."""
        _make_closet(self.canon, "wing_bees", "plan", "sample", "canon text")
        # Overlay closet directory carries the queenfile suffix.
        _make_closet(self.overlay, "wing_bees", "plan", "sample.queenfile_bees",
                     "overlay queenfile text")
        results = palace_recall("sample", root=self.canon, overlay_root=self.overlay)
        texts = [r["closet"] for r in results]
        self.assertTrue(any("overlay queenfile text" in t for t in texts),
                        f"queenfile overlay not returned: {texts}")
        self.assertFalse(any("canon text" in t for t in texts),
                         "canon should be replaced by queenfile overlay")


_CHROMADB_AVAILABLE = False
try:
    import chromadb  # noqa: F401
    _CHROMADB_AVAILABLE = True
except ImportError:
    pass


@unittest.skipUnless(_CHROMADB_AVAILABLE, "chromadb not installed")
class TestSemanticOverlayMerge(unittest.TestCase):
    """palace_recall_semantic merges overlay closets via linear-scan."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.canon = Path(self._td.name) / "canon"
        self.overlay = Path(self._td.name) / "overlay"
        self.db = Path(self._td.name) / "db"
        _make_closet(self.canon, "wing_bees", "plan", "sample",
                     "canon semantic body for sample query")
        _make_closet(self.overlay, "wing_bees", "plan", "sample",
                     "overlay semantic body for sample query")

    def tearDown(self):
        self._td.cleanup()

    def test_semantic_overlay_merge(self):
        from honeycomb.semantic import palace_recall_semantic, index_closets

        # Index canon only.
        index_closets(hc_root=self.canon, db_path=self.db)

        results = palace_recall_semantic(
            "sample query",
            overlay_root=self.overlay,
            db_path=self.db,
            top_k=3,
        )
        self.assertTrue(results, "expected at least one result")
        texts = [r["closet"] for r in results]
        self.assertTrue(any("overlay semantic body" in t for t in texts),
                        f"overlay did not win in semantic results: {texts}")
        self.assertFalse(any("canon semantic body" in t for t in texts),
                         "canon entry should be replaced by overlay")


if __name__ == "__main__":
    unittest.main()
