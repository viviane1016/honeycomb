"""Tests for rank_by_specificity and resolve_overrides (spec 002)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure lib/ is on sys.path when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from honeycomb.overrides import (
    OverrideSpec,
    RankedMatch,
    ResolutionContext,
    rank_by_specificity,
    resolve_overrides,
)

_DUMMY = Path("dummy")


def _spec(**kwargs):
    return OverrideSpec(path=_DUMMY, target="t", **kwargs)


def _touch(directory, name):
    p = Path(directory) / name
    p.touch()
    return p


class TestResolveOverrides(unittest.TestCase):

    def test_axis_filtering(self):
        """Spec with tool='bees' is dropped when context tool='scarab'."""
        with tempfile.TemporaryDirectory() as d:
            p = _touch(d, "a.md")
            spec = _spec(tool="bees")
            ctx = ResolutionContext(tool="scarab")
            ranked = rank_by_specificity([(spec, p)], ctx)
            self.assertEqual(ranked, [])

    def test_wildcard_match(self):
        """Spec with tool=None survives any context but scores 0 axes_matched."""
        with tempfile.TemporaryDirectory() as d:
            p = _touch(d, "a.md")
            spec = _spec(tool=None)
            ctx = ResolutionContext(tool="scarab")
            ranked = rank_by_specificity([(spec, p)], ctx)
            self.assertEqual(len(ranked), 1)
            self.assertEqual(ranked[0].score[0], 0)  # axes_matched

    def test_version_exactness_beats_range(self):
        """Spec tool_version='==v1.18' beats '>=v1.17' when context is v1.18."""
        with tempfile.TemporaryDirectory() as d:
            p_exact = _touch(d, "exact.md")
            p_range = _touch(d, "range.md")
            os.utime(p_exact, (1000, 1000))
            os.utime(p_range, (1000, 1000))
            spec_exact = _spec(tool_version="==v1.18")
            spec_range = _spec(tool_version=">=v1.17")
            ctx = ResolutionContext(tool_version="v1.18")
            ranked = rank_by_specificity(
                [(spec_exact, p_exact), (spec_range, p_range)], ctx
            )
            self.assertEqual(len(ranked), 2)
            self.assertEqual(ranked[0].path, p_exact)

    def test_consumer_exactness_tiebreaker(self):
        """Named consumer beats wildcard when context matches."""
        with tempfile.TemporaryDirectory() as d:
            p_named = _touch(d, "named.md")
            p_wild = _touch(d, "wild.md")
            os.utime(p_named, (1000, 1000))
            os.utime(p_wild, (1000, 1000))
            spec_named = _spec(consumer="scarab")
            spec_wild = _spec(consumer=None)
            ctx = ResolutionContext(consumer="scarab")
            ranked = rank_by_specificity(
                [(spec_named, p_named), (spec_wild, p_wild)], ctx
            )
            self.assertEqual(len(ranked), 2)
            self.assertEqual(ranked[0].path, p_named)

    def test_mtime_tiebreaker(self):
        """Newer mtime wins when all other score components are equal."""
        with tempfile.TemporaryDirectory() as d:
            p_newer = _touch(d, "newer.md")
            p_older = _touch(d, "older.md")
            os.utime(p_newer, (2000, 2000))
            os.utime(p_older, (1000, 1000))
            spec1 = _spec()
            spec2 = _spec()
            ctx = ResolutionContext()
            ranked = rank_by_specificity([(spec1, p_newer), (spec2, p_older)], ctx)
            self.assertEqual(len(ranked), 2)
            self.assertEqual(ranked[0].path, p_newer)

    def test_ambiguous_overlap_flag(self):
        """Drawer key appears in ambiguous when candidates tie on first three rungs."""
        with tempfile.TemporaryDirectory() as d:
            p1 = _touch(d, "a.md")
            p2 = _touch(d, "b.md")
            os.utime(p1, (2000, 2000))
            os.utime(p2, (1000, 1000))
            spec1 = _spec()
            spec2 = _spec()
            candidates = {"wing/room/drawer": [(spec1, p1), (spec2, p2)]}
            winners, ambiguous = resolve_overrides(candidates, ResolutionContext())
            self.assertIn("wing/room/drawer", ambiguous)
            # Still exactly one winner
            self.assertEqual(len(winners), 1)
            self.assertIn("wing/room/drawer", winners)

    def test_multi_drawer_resolution(self):
        """Each drawer key gets its own independent winner."""
        with tempfile.TemporaryDirectory() as d:
            p1 = _touch(d, "d1.md")
            p2 = _touch(d, "d2.md")
            spec1 = _spec()
            spec2 = _spec()
            ctx = ResolutionContext()
            candidates = {
                "drawer/one": [(spec1, p1)],
                "drawer/two": [(spec2, p2)],
            }
            winners, ambiguous = resolve_overrides(candidates, ctx)
            self.assertIn("drawer/one", winners)
            self.assertIn("drawer/two", winners)
            self.assertEqual(winners["drawer/one"], p1)
            self.assertEqual(winners["drawer/two"], p2)
            self.assertEqual(ambiguous, [])

    def test_empty_input(self):
        """resolve_overrides on empty candidates returns ({}, [])."""
        ctx = ResolutionContext()
        winners, ambiguous = resolve_overrides({}, ctx)
        self.assertEqual(winners, {})
        self.assertEqual(ambiguous, [])

    def test_all_filtered_out_drawer(self):
        """Drawer omitted from winners and ambiguous when all candidates fail filtering."""
        with tempfile.TemporaryDirectory() as d:
            p = _touch(d, "override.md")
            spec = _spec(tool="bees")
            ctx = ResolutionContext(tool="scarab")
            candidates = {"some/drawer": [(spec, p)]}
            winners, ambiguous = resolve_overrides(candidates, ctx)
            self.assertNotIn("some/drawer", winners)
            self.assertNotIn("some/drawer", ambiguous)


if __name__ == "__main__":
    unittest.main()
