import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_CELL_ROOT = Path(__file__).resolve().parent.parent


def _build_env(hc_dir, bees_dir):
    """Build subprocess env with PYTHONPATH set so lib/ is importable."""
    existing = os.environ.get("PYTHONPATH", "")
    lib_path = str(_CELL_ROOT / "lib")
    pythonpath = f"{lib_path}{os.pathsep}{existing}" if existing else lib_path
    return {
        **os.environ,
        "HONEYCOMB_ROOT": str(hc_dir),
        "BEES_REPO_ROOT": str(bees_dir),
        "BEES_FEATURE_SLUG": "test-slug",
        "BEES_ACTOR": "test-actor",
        "BEES_STAGE": "spec",
        "BEES_MODEL": "claude-sonnet-4-6",
        "PYTHONPATH": pythonpath,
    }


def _call_tool(tool_name, query, env):
    """Spawn MCP server, send initialize + tools/call, return (init_resp, call_resp)."""
    proc = subprocess.Popen(
        [sys.executable, str(_CELL_ROOT / "bin" / "honeycomb-mcp")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        init_msg = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) + "\n"
        call_msg = json.dumps({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": tool_name, "arguments": {"query": query}},
        }) + "\n"
        proc.stdin.write(init_msg + call_msg)
        proc.stdin.close()
        init_resp = json.loads(proc.stdout.readline())
        call_resp = json.loads(proc.stdout.readline())
        return init_resp, call_resp
    finally:
        proc.stdout.close()
        proc.wait(timeout=15)


class TestMCPLogIntegration(unittest.TestCase):

    def setUp(self):
        # Seed honeycomb: minimal wing tree with "queen" in closet body
        self.hc_dir = tempfile.mkdtemp()
        closet_dir = Path(self.hc_dir) / "wing_bees" / "architecture" / "sample"
        closet_dir.mkdir(parents=True)
        (closet_dir / "closet.md").write_text(
            "The queen orchestrates the bees workflow.\n", encoding="utf-8"
        )

        # Log destination root
        self.bees_dir = tempfile.mkdtemp()
        self.env = _build_env(self.hc_dir, self.bees_dir)

    def tearDown(self):
        shutil.rmtree(self.hc_dir, ignore_errors=True)
        shutil.rmtree(self.bees_dir, ignore_errors=True)

    def test_palace_recall_writes_log_record(self):
        _init, call_resp = _call_tool("palace_recall", "queen", self.env)

        self.assertNotIn("error", call_resp, f"Unexpected error: {call_resp}")
        self.assertIn("result", call_resp)

        log_file = Path(self.bees_dir) / ".bees" / "test-slug" / "mcp-calls.jsonl"
        self.assertTrue(log_file.exists(), f"Log file not created: {log_file}")
        lines = log_file.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1, f"Expected 1 log line, got {len(lines)}")

        record = json.loads(lines[0])
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(record["tool"], "palace_recall")
        self.assertEqual(record["slug"], "test-slug")
        self.assertEqual(record["actor"], "test-actor")
        self.assertEqual(record["stage"], "spec")
        self.assertEqual(record["model"], "claude-sonnet-4-6")
        self.assertTrue(record.get("ts"), "Missing ts field")
        self.assertEqual(record["request"]["query"], "queen")
        self.assertGreater(record["response"]["bytes"], 0)
        self.assertRegex(record["response"]["content_sha"], r"^[0-9a-f]{64}$")
        self.assertIsInstance(record["duration_ms"], int)
        self.assertGreaterEqual(record["duration_ms"], 0)

    def test_palace_recall_semantic_writes_log_record(self):
        _init, call_resp = _call_tool("palace_recall_semantic", "queen", self.env)

        self.assertNotIn("error", call_resp, f"Unexpected error: {call_resp}")
        self.assertIn("result", call_resp)

        log_file = Path(self.bees_dir) / ".bees" / "test-slug" / "mcp-calls.jsonl"
        self.assertTrue(log_file.exists(), f"Log file not created: {log_file}")
        lines = log_file.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1, f"Expected 1 log line, got {len(lines)}")

        record = json.loads(lines[0])
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(record["tool"], "palace_recall_semantic")
        self.assertEqual(record["slug"], "test-slug")
        self.assertEqual(record["actor"], "test-actor")
        self.assertEqual(record["stage"], "spec")
        # semantic backend may return empty when chromadb/index missing
        self.assertIn("result_count", record["response"])
        self.assertIsInstance(record["duration_ms"], int)
        self.assertGreaterEqual(record["duration_ms"], 0)

    def test_logging_failure_does_not_break_response(self):
        readonly_dir = tempfile.mkdtemp()
        try:
            os.chmod(readonly_dir, 0o555)
            env = {
                **self.env,
                "BEES_REPO_ROOT": os.path.join(readonly_dir, "sub"),
            }
            _init, call_resp = _call_tool("palace_recall", "queen", env)
            # MCP response must be a normal success despite the log write failing
            self.assertNotIn("error", call_resp, f"Got error instead of success: {call_resp}")
            self.assertIn("result", call_resp)
        finally:
            os.chmod(readonly_dir, 0o755)
            shutil.rmtree(readonly_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
