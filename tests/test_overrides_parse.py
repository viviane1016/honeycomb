import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# Ensure lib/ is on sys.path when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from honeycomb.overrides import (
    OverrideParseError,
    OverrideSpec,
    parse_override_file,
)


class ParseOverrideFileTests(unittest.TestCase):
    def _write(self, name: str, content: str) -> Path:
        d = Path(self._tmp.name)
        p = d / name
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_parses_tool_and_version_override(self) -> None:
        p = self._write(
            "behaviour.queenfile_bees-v1.18.md",
            """\
            <!-- behaviour.queenfile_bees-v1.18.md: bees v1.18 override.

            target: behaviour
            tool: bees
            tool_version: ">=v1.18"
            consumer: null
            rationale: |
              v1.18 introduces the scoped recall context. Builders need to pass
              tool_version through queries; spec contract documents this.
            -->
            <override content body — replaces behaviour.md when this scope applies>
            """,
        )
        spec = parse_override_file(p)
        self.assertEqual(spec.target, "behaviour")
        self.assertEqual(spec.tool, "bees")
        self.assertEqual(spec.tool_version, ">=v1.18")
        self.assertIsNone(spec.consumer)
        self.assertIn("v1.18 introduces the scoped recall context", spec.rationale)
        self.assertIn("tool_version through queries", spec.rationale)
        self.assertTrue(spec.body.startswith("<override content body"))

    def test_consumer_only_override(self) -> None:
        p = self._write(
            "behaviour.queenfile_scarab.md",
            """\
            <!-- consumer-scoped override.

            target: behaviour
            tool: null
            tool_version: null
            consumer: scarab
            -->

            Consumer-specific body.
            """,
        )
        spec = parse_override_file(p)
        self.assertEqual(spec.consumer, "scarab")
        self.assertIsNone(spec.tool)
        self.assertIsNone(spec.tool_version)

    def test_filename_is_hint_only(self) -> None:
        # Filename suggests bees scope but frontmatter declares scarab
        p = self._write(
            "behaviour.queenfile_bees-v1.18.md",
            """\
            <!-- frontmatter overrides filename.

            target: behaviour
            tool: scarab
            tool_version: "==v2.0"
            consumer: null
            -->

            Body here.
            """,
        )
        spec = parse_override_file(p)
        self.assertEqual(spec.tool, "scarab")
        self.assertEqual(spec.tool_version, "==v2.0")

    def test_missing_frontmatter_raises(self) -> None:
        p = self._write(
            "no_comment.md",
            """\
            target: behaviour
            tool: bees

            Body with no HTML comment wrapper.
            """,
        )
        with self.assertRaises(OverrideParseError):
            parse_override_file(p)

    def test_missing_target_raises(self) -> None:
        p = self._write(
            "no_target.md",
            """\
            <!--
            tool: bees
            tool_version: ">=v1.18"
            consumer: null
            -->

            Body with no target field.
            """,
        )
        with self.assertRaises(OverrideParseError):
            parse_override_file(p)

    def test_rationale_optional(self) -> None:
        p = self._write(
            "no_rationale.md",
            """\
            <!--
            target: behaviour
            tool: bees
            tool_version: "v1.0"
            -->

            Body without rationale.
            """,
        )
        spec = parse_override_file(p)
        self.assertEqual(spec.rationale, "")
        self.assertEqual(spec.target, "behaviour")


if __name__ == "__main__":
    unittest.main()
