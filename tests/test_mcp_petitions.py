import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_CELL_ROOT = Path(__file__).resolve().parent.parent

# Stub petitions module written into each test's fake HONEYCOMB_ROOT.
# Uses PETITION_STUB_MODE env var (default "success") and records call args
# to $BEES_REPO_ROOT/petition_call_record.json for cross-process inspection.
_STUB_PETITIONS_CODE = '''\
import json
import os
from pathlib import Path


class PetitionError(RuntimeError):
    pass


def _record(func_name, kwargs):
    bees_root = os.environ.get("BEES_REPO_ROOT")
    if bees_root:
        record = {"func": func_name, "kwargs": {}}
        for k, v in kwargs.items():
            record["kwargs"][k] = str(v) if isinstance(v, Path) else v
        (Path(bees_root) / "petition_call_record.json").write_text(
            json.dumps(record), encoding="utf-8"
        )


def submit(target, content, rationale, context, *, hc_root, overlay_root=None):
    _record("submit", {"target": target, "content": content, "rationale": rationale})
    if os.environ.get("PETITION_STUB_MODE") == "error":
        raise PetitionError(os.environ.get("PETITION_STUB_ERROR", "stub error"))
    return {
        "petition_id": "p123",
        "branch": "feat/petition-p123",
        "pr_url": "https://github.com/x/y/pull/1",
        "overlay_path": None,
    }


def list_pending(consumer, *, hc_root, overlay_root=None):
    _record("list_pending", {"consumer": consumer})
    if os.environ.get("PETITION_STUB_MODE") == "error":
        raise PetitionError(os.environ.get("PETITION_STUB_ERROR", "stub error"))
    return []


def withdraw(petition_id, *, hc_root):
    _record("withdraw", {"petition_id": petition_id})
    if os.environ.get("PETITION_STUB_MODE") == "error":
        raise PetitionError(os.environ.get("PETITION_STUB_ERROR", "stub error"))
    return None
'''


def _make_stub_hc_root(base_dir: Path) -> Path:
    """Create a stub HONEYCOMB_ROOT with petitions stub + real log writer."""
    lib_dir = base_dir / "lib" / "honeycomb"
    lib_dir.mkdir(parents=True)
    (lib_dir / "__init__.py").write_text("", encoding="utf-8")
    (lib_dir / "petitions.py").write_text(_STUB_PETITIONS_CODE, encoding="utf-8")
    shutil.copy(str(_CELL_ROOT / "lib" / "honeycomb" / "log.py"), str(lib_dir / "log.py"))
    return base_dir


def _build_env(hc_dir: Path, bees_dir: Path, **extra) -> dict:
    return {
        **os.environ,
        "HONEYCOMB_ROOT": str(hc_dir),
        "BEES_REPO_ROOT": str(bees_dir),
        "BEES_FEATURE_SLUG": "test-spec-007",
        "BEES_ACTOR": "scribe",
        "BEES_STAGE": "spec",
        "BEES_MODEL": "claude-sonnet-4-6",
        **extra,
    }


def _send(proc, *messages):
    """Write JSON-RPC messages to proc stdin and read one response per message."""
    payload = "".join(json.dumps(m) + "\n" for m in messages)
    proc.stdin.write(payload)
    proc.stdin.close()
    responses = []
    for _ in messages:
        line = proc.stdout.readline()
        if not line:
            break
        responses.append(json.loads(line))
    proc.stdout.close()
    proc.wait(timeout=15)
    return responses


def _spawn(env):
    return subprocess.Popen(
        [sys.executable, str(_CELL_ROOT / "bin" / "honeycomb-mcp")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )


class TestMCPPetitions(unittest.TestCase):

    def setUp(self):
        self.hc_tmp = tempfile.mkdtemp()
        self.bees_tmp = tempfile.mkdtemp()
        _make_stub_hc_root(Path(self.hc_tmp))

    def tearDown(self):
        shutil.rmtree(self.hc_tmp, ignore_errors=True)
        shutil.rmtree(self.bees_tmp, ignore_errors=True)

    def _env(self, **extra):
        return _build_env(Path(self.hc_tmp), Path(self.bees_tmp), **extra)

    # ── tests ──────────────────────────────────────────────────────────────────

    def test_tools_list_includes_petition_descriptors(self):
        env = self._env()
        proc = _spawn(env)
        responses = _send(
            proc,
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        list_resp = responses[1]
        self.assertNotIn("error", list_resp, list_resp)
        tools = list_resp["result"]["tools"]
        names = [t["name"] for t in tools]
        self.assertEqual(len(tools), 5)
        self.assertEqual(
            set(names),
            {"palace_recall", "palace_recall_semantic",
             "palace_petition_submit", "palace_petition_list",
             "palace_petition_withdraw"},
        )

    def test_petition_submit_dispatches_to_helper(self):
        env = self._env()
        proc = _spawn(env)
        responses = _send(
            proc,
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {
                    "name": "palace_petition_submit",
                    "arguments": {
                        "target": "some_drawer",
                        "content": "new content",
                        "rationale": "because",
                        "context": {"tool": "claude-code", "tool_version": "1.0", "consumer": "scribe"},
                    },
                },
            },
        )
        call_resp = responses[1]
        self.assertNotIn("error", call_resp, call_resp)
        text = call_resp["result"]["content"][0]["text"]
        result = json.loads(text)
        self.assertEqual(result["petition_id"], "p123")
        self.assertEqual(result["branch"], "feat/petition-p123")
        self.assertEqual(result["pr_url"], "https://github.com/x/y/pull/1")
        self.assertIsNone(result["overlay_path"])

    def test_petition_submit_logs_call(self):
        env = self._env()
        proc = _spawn(env)
        _send(
            proc,
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {
                    "name": "palace_petition_submit",
                    "arguments": {
                        "target": "some_drawer",
                        "content": "new content",
                        "rationale": "because",
                        "context": {"tool": "claude-code", "tool_version": "1.0", "consumer": "scribe"},
                    },
                },
            },
        )
        log_file = Path(self.bees_tmp) / ".bees" / "test-spec-007" / "mcp-calls.jsonl"
        self.assertTrue(log_file.exists(), f"Log file not created: {log_file}")
        lines = log_file.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["tool"], "palace_petition_submit")
        self.assertEqual(record["actor"], "scribe")
        self.assertEqual(record["stage"], "spec")
        self.assertEqual(record["model"], "claude-sonnet-4-6")

    def test_petition_error_returns_jsonrpc_error(self):
        env = self._env(PETITION_STUB_MODE="error", PETITION_STUB_ERROR="gh CLI not found")
        proc = _spawn(env)
        responses = _send(
            proc,
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {
                    "name": "palace_petition_submit",
                    "arguments": {
                        "target": "some_drawer",
                        "content": "new content",
                        "rationale": "because",
                        "context": {"tool": "claude-code", "tool_version": "1.0", "consumer": "scribe"},
                    },
                },
            },
        )
        call_resp = responses[1]
        self.assertIn("error", call_resp, call_resp)
        self.assertEqual(call_resp["error"]["code"], -32603)
        self.assertIn("gh CLI not found", call_resp["error"]["message"])

    def test_petition_list_no_consumer_passes_none(self):
        env = self._env()
        proc = _spawn(env)
        _send(
            proc,
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "palace_petition_list", "arguments": {}},
            },
        )
        record_file = Path(self.bees_tmp) / "petition_call_record.json"
        self.assertTrue(record_file.exists(), "Stub did not write call record")
        call_record = json.loads(record_file.read_text(encoding="utf-8"))
        self.assertEqual(call_record["func"], "list_pending")
        self.assertIsNone(call_record["kwargs"]["consumer"])


if __name__ == "__main__":
    unittest.main()
