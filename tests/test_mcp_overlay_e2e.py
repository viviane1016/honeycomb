"""End-to-end overlay test: petition submit → palace_recall returns source="consumer-overlay"."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_CELL_ROOT = Path(__file__).resolve().parent.parent

_GH_SHIM_SH = """\
#!/bin/sh
echo "https://example.test/pulls/1"
exit 0
"""

_CLOSET_MD = """\
<!-- Hall: hall_pattern -->
Sample closet for overlay-target testing.
"""


def _git(args, cwd, env=None):
    result = subprocess.run(
        ["git"] + args, cwd=str(cwd), capture_output=True, text=True, check=False,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {args} failed: {result.stderr}")
    return result


def _spawn(env):
    return subprocess.Popen(
        [sys.executable, str(_CELL_ROOT / "bin" / "honeycomb-mcp")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )


def _send(proc, *messages):
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
    proc.wait(timeout=30)
    return responses


@unittest.skipUnless(shutil.which("git") is not None, "git not available")
class TestMCPOverlayE2E(unittest.TestCase):

    def setUp(self):
        self._td = tempfile.mkdtemp()
        td = Path(self._td)

        # hc/ — canon git repo; also contains the real lib/honeycomb so that
        # the MCP server (HONEYCOMB_ROOT=hc_dir) can import the real modules.
        self.hc_dir = td / "hc"
        shutil.copytree(
            str(_CELL_ROOT / "lib" / "honeycomb"),
            str(self.hc_dir / "lib" / "honeycomb"),
        )
        closet_dir = self.hc_dir / "wing_test" / "sample-room" / "sample-closet"
        closet_dir.mkdir(parents=True)
        (closet_dir / "closet.md").write_text(_CLOSET_MD, encoding="utf-8")
        (closet_dir / "overlay-target.md").write_text(
            "canon body for overlay-target", encoding="utf-8"
        )

        git_env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
        }
        _git(["init"], cwd=self.hc_dir, env=git_env)
        _git(["add", "."], cwd=self.hc_dir, env=git_env)
        _git(["commit", "-m", "init"], cwd=self.hc_dir, env=git_env)

        # bees/ — consumer repo root; create the overlay root dir so _overlay_root() returns it
        self.bees_dir = td / "bees"
        self.overlay_root = self.bees_dir / ".bees" / "honeycomb-overlay"
        self.overlay_root.mkdir(parents=True)

        # shims/ — gh shim
        self.shims_dir = td / "shims"
        self.shims_dir.mkdir()
        gh_shim = self.shims_dir / "gh"
        gh_shim.write_text(_GH_SHIM_SH, encoding="utf-8")
        gh_shim.chmod(0o755)

    def tearDown(self):
        shutil.rmtree(self._td, ignore_errors=True)

    def _env(self):
        return {
            **os.environ,
            "HONEYCOMB_ROOT": str(self.hc_dir),
            "BEES_REPO_ROOT": str(self.bees_dir),
            "BEES_FEATURE_SLUG": "test-overlay-e2e",
            "BEES_ACTOR": "scribe",
            "BEES_STAGE": "spec",
            "BEES_MODEL": "claude-sonnet-4-6",
            "PATH": str(self.shims_dir) + os.pathsep + os.environ["PATH"],
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
        }

    def test_petition_submitted_through_mcp_recallable_with_overlay_source(self):
        env = self._env()

        # Step 1: submit petition via MCP
        proc = _spawn(env)
        responses = _send(
            proc,
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {
                    "name": "palace_petition_submit",
                    "arguments": {
                        "target": "overlay-target",
                        "content": "overlay body content from petition",
                        "rationale": "test rationale",
                        "context": {
                            "tool": "claude-code",
                            "tool_version": "1.0",
                            "consumer": "scribe",
                        },
                    },
                },
            },
        )
        submit_resp = responses[1]
        self.assertNotIn("error", submit_resp,
                         f"petition submit returned error: {submit_resp}")

        # Step 2: assert palace_petition_submit mirrored the canonical closet.md
        # into the overlay closet directory. Without this, _discover_closets
        # would skip the overlay closet entirely, breaking the load-bearing
        # "submit a petition, recall it back" guarantee of ADR-0002.
        overlay_closet_dir = (
            self.overlay_root / "wing_test" / "sample-room" / "sample-closet"
        )
        self.assertTrue(overlay_closet_dir.exists(),
                        "petition submit should have created the overlay closet dir")
        self.assertTrue((overlay_closet_dir / "closet.md").exists(),
                        "petition submit must mirror canonical closet.md into the "
                        "overlay closet directory so _discover_closets walks it")

        # Step 3: recall the same target via a fresh MCP spawn
        proc2 = _spawn(env)
        responses2 = _send(
            proc2,
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {
                    "name": "palace_recall",
                    "arguments": {
                        "query": "overlay-target",
                        "top_k": 3,
                        "drawer": True,
                    },
                },
            },
        )
        recall_resp = responses2[1]
        self.assertNotIn("error", recall_resp,
                         f"palace_recall returned error: {recall_resp}")

        text = recall_resp["result"]["content"][0]["text"]
        results = json.loads(text)
        self.assertTrue(results, "expected at least one recall result")

        # Find the overlay entry — room composite is "sample-room/sample-closet"
        overlay_entry = next(
            (r for r in results
             if r.get("wing") == "wing_test" and r.get("room", "").endswith("sample-closet")),
            None,
        )
        self.assertIsNotNone(overlay_entry,
                             f"no wing_test/sample-*closet entry in results: {results}")

        self.assertEqual(
            overlay_entry.get("source"), "consumer-overlay",
            f"expected source='consumer-overlay', got: {overlay_entry.get('source')!r}",
        )
        drawer_text = overlay_entry.get("drawer", "")
        self.assertIn(
            "overlay body content from petition", drawer_text,
            f"petition content not in drawer: {drawer_text!r}",
        )


if __name__ == "__main__":
    unittest.main()
