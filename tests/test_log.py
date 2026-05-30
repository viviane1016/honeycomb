import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import json
import os
import tempfile
import unittest
import unittest.mock

from lib.honeycomb import log


class TestWriteCallRecord(unittest.TestCase):

    def test_writes_jsonl_record_with_actor_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "BEES_REPO_ROOT": tmp,
                "BEES_FEATURE_SLUG": "feature-x",
                "BEES_ACTOR": "queen",
                "BEES_STAGE": "plan",
                "BEES_MODEL": "claude-opus-4-7",
            }
            with unittest.mock.patch.dict(os.environ, env, clear=False):
                log.write_call_record(
                    "palace_recall",
                    {"query": "foo"},
                    {"closets": []},
                    12.5,
                )
            dest = pathlib.Path(tmp) / ".bees" / "feature-x" / "mcp-calls.jsonl"
            lines = dest.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record["schema_version"], 1)
            self.assertEqual(record["tool"], "palace_recall")
            self.assertEqual(record["slug"], "feature-x")
            self.assertEqual(record["actor"], "queen")
            self.assertEqual(record["stage"], "plan")
            self.assertEqual(record["model"], "claude-opus-4-7")
            self.assertEqual(record["request"], {"query": "foo"})
            self.assertEqual(record["response"], {"closets": []})
            self.assertEqual(record["duration_ms"], 12.5)
            self.assertTrue(record["ts"])

    def test_falls_back_to_honeycomb_root_when_slug_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"HONEYCOMB_ROOT": tmp}
            remove_keys = ["BEES_REPO_ROOT", "BEES_FEATURE_SLUG"]
            with unittest.mock.patch.dict(os.environ, env, clear=False):
                for key in remove_keys:
                    os.environ.pop(key, None)
                log.write_call_record("some_tool", {}, {}, 1.0)
            dest = pathlib.Path(tmp) / ".calls.jsonl"
            self.assertTrue(dest.exists())
            lines = dest.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record["schema_version"], 1)

    def test_missing_actor_env_writes_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Set HONEYCOMB_ROOT so the fallback path lands in a known temp dir.
            # BEES_FEATURE_SLUG is absent, so resolve_destination uses HONEYCOMB_ROOT.
            env = {"BEES_REPO_ROOT": tmp, "HONEYCOMB_ROOT": tmp}
            remove_keys = ["BEES_ACTOR", "BEES_STAGE", "BEES_MODEL", "BEES_FEATURE_SLUG"]
            with unittest.mock.patch.dict(os.environ, env, clear=False):
                for key in remove_keys:
                    os.environ.pop(key, None)
                log.write_call_record("some_tool", {}, {}, 0.5)
            dest = pathlib.Path(tmp) / ".calls.jsonl"
            self.assertTrue(dest.exists())
            lines = dest.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record["actor"], "unknown")
            self.assertEqual(record["stage"], "unknown")
            self.assertEqual(record["model"], "unknown")
            self.assertEqual(record["slug"], "unknown")

    def test_concurrent_writes_do_not_corrupt_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "BEES_REPO_ROOT": tmp,
                "BEES_FEATURE_SLUG": "concurrent-test",
            }
            # Remove keys that might interfere
            with unittest.mock.patch.dict(os.environ, env, clear=False):
                dest = log.resolve_destination()

            pid1 = os.fork()
            if pid1 == 0:
                with unittest.mock.patch.dict(os.environ, env, clear=False):
                    for _ in range(50):
                        log.write_call_record("tool_a", {"i": _}, {}, float(_))
                os._exit(0)

            pid2 = os.fork()
            if pid2 == 0:
                with unittest.mock.patch.dict(os.environ, env, clear=False):
                    for _ in range(50):
                        log.write_call_record("tool_b", {"i": _}, {}, float(_))
                os._exit(0)

            os.waitpid(pid1, 0)
            os.waitpid(pid2, 0)

            lines = dest.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 100)
            for line in lines:
                record = json.loads(line)
                self.assertEqual(record["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
