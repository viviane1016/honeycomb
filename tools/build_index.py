#!/usr/bin/env python3
# tools/build_index.py — Build/rebuild the ChromaDB semantic index over the
# four-level honeycomb structure.
#
# Always rebuilds from text — install.sh calls this on every install/update
# so the index can never drift from the canonical text content.
#
# Best-effort: when chromadb is not installed, exits 0 with a hint so the
# install hook stays green. Keyword recall continues to work without an
# index; semantic recall falls through to [].
#
# Usage:
#   tools/build_index.py                  # rebuild from $HONEYCOMB_ROOT or repo root
#   tools/build_index.py --hc-root PATH   # explicit honeycomb root
#   tools/build_index.py --check          # exit 0 iff indexed VERSION matches text VERSION

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib"))


def _deps_available() -> bool:
    try:
        import chromadb  # noqa: F401
        return True
    except ImportError:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build or check the honeycomb semantic recall index."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 0 if indexed VERSION matches on-disk; non-zero otherwise",
    )
    parser.add_argument(
        "--hc-root",
        type=Path,
        default=None,
        help="honeycomb root (default: $HONEYCOMB_ROOT or repo root)",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="chroma store path (default: ~/.mempalace/honeycomb_v1)",
    )
    args = parser.parse_args(argv)

    if not _deps_available():
        msg = (
            "chromadb not installed — semantic recall disabled "
            "(keyword recall still works). Install with: pip install chromadb"
        )
        if args.check:
            print(msg)
            return 0
        print(msg, file=sys.stderr)
        return 0  # don't fail install when semantic is optional

    from honeycomb.semantic import index_closets, is_index_current, get_indexed_version

    if args.check:
        current = is_index_current(args.hc_root, args.db_path)
        indexed = get_indexed_version(args.db_path)
        if current:
            print(f"build_index: current (honeycomb v{indexed})")
            return 0
        print(f"build_index: stale (indexed v{indexed or 'none'})")
        return 1

    t0 = time.monotonic()
    try:
        n, version = index_closets(args.hc_root, args.db_path)
    except RuntimeError as e:
        print(f"build_index: {e}", file=sys.stderr)
        return 1
    elapsed = time.monotonic() - t0
    print(f"build_index: indexed {n} closets at honeycomb v{version} in {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
