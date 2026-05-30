"""Tests for _load_log_writer module-level cache in bin/honeycomb-mcp."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent


def _load_mcp_module():
    # spec_from_file_location can't infer the loader for extension-less scripts;
    # provide SourceFileLoader explicitly.
    loader = SourceFileLoader(
        "honeycomb_mcp_under_test", str(_REPO / "bin" / "honeycomb-mcp")
    )
    spec = importlib.util.spec_from_loader("honeycomb_mcp_under_test", loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestLogWriterCache(unittest.TestCase):

    def test_load_log_writer_caches_writer_and_does_not_accumulate_sys_path(self):
        mod = _load_mcp_module()
        lib_path = str(mod._repo_root() / "lib")
        baseline = sys.path.count(lib_path)
        writers = [mod._load_log_writer() for _ in range(5)]
        after = sys.path.count(lib_path)
        # Identity-equal — proves the writer is cached, not re-imported each call.
        self.assertTrue(all(w is writers[0] for w in writers),
                        "expected identity-equal writer across calls")
        # sys.path grew by at most one (the first call's insertion if it was absent).
        self.assertLessEqual(after - baseline, 1,
                             f"sys.path accumulated: baseline={baseline} after={after}")


if __name__ == "__main__":
    unittest.main()
