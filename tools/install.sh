#!/usr/bin/env bash
# tools/install.sh — Install or update honeycomb at $HOME/.honeycomb.
#
# Pulls the latest tagged release of viviane1016/honeycomb into the install
# location, then always rebuilds the semantic index so the index can never
# drift from the canonical text content.
#
# Idempotent: safe to re-run any time. Picks up content updates from each
# patch release (v1.0.0 → v1.0.1 → …) without manual intervention.
#
# Usage:
#   bash tools/install.sh                  # install to $HOME/.honeycomb
#   HONEYCOMB_INSTALL_DIR=/opt/honeycomb bash tools/install.sh
#   HONEYCOMB_TAG=v1.0.1 bash tools/install.sh   # pin to a specific tag
#   bash tools/install.sh --tool bees --tool-version v1.18 --consumer myapp
#                                          # materialize scope-specific view
#
# Scope flags (all optional; any one triggers materialization):
#   --tool <T>             tool name (e.g. bees, scarab)
#   --tool-version <V>     tool version string (e.g. v1.18, >=v1.17)
#   --consumer <C>         consumer identifier (e.g. myapp)
#
# Exit codes:
#   0  install + reindex succeeded
#   1  fetch / clone failed
#   2  reindex failed with chromadb present

set -eu

REPO="https://github.com/viviane1016/honeycomb.git"
TARGET="${HONEYCOMB_INSTALL_DIR:-$HOME/.honeycomb}"
TAG="${HONEYCOMB_TAG:-}"   # empty = latest tag

TOOL=""
TOOL_VERSION=""
CONSUMER=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --tool)          TOOL="${2:-}";         shift 2 ;;
        --tool-version)  TOOL_VERSION="${2:-}"; shift 2 ;;
        --consumer)      CONSUMER="${2:-}";     shift 2 ;;
        *)               shift ;;
    esac
done

step() { printf "honeycomb-install: %s\n" "$*"; }
warn() { printf "honeycomb-install: warn: %s\n" "$*" >&2; }
die()  { printf "honeycomb-install: error: %s\n" "$*" >&2; exit 1; }

# ── 1. Resolve target tag ────────────────────────────────────────────────────
if [ -z "$TAG" ]; then
    if TAG="$(git ls-remote --tags "$REPO" 2>/dev/null \
                | awk -F/ '/refs\/tags\/v[0-9]/ {print $NF}' \
                | sort -V | tail -1)"; then
        : "${TAG:?could not resolve latest tag}"
        step "resolved latest tag: $TAG"
    else
        die "could not query tags from $REPO"
    fi
else
    step "using pinned tag: $TAG"
fi

# ── 2. Clone or update ───────────────────────────────────────────────────────
if [ -d "$TARGET/.git" ]; then
    step "updating $TARGET"
    (cd "$TARGET" && git fetch --tags --quiet && git checkout --quiet "$TAG") \
        || die "failed to update $TARGET to $TAG"
elif [ -d "$TARGET" ]; then
    die "$TARGET exists but is not a git checkout — refusing to clobber"
else
    step "cloning $REPO @ $TAG → $TARGET"
    git clone --depth 1 --branch "$TAG" --quiet "$REPO" "$TARGET" \
        || die "git clone failed"
fi

INSTALLED_VER="$(cat "$TARGET/VERSION" 2>/dev/null || echo unknown)"
step "installed honeycomb v$INSTALLED_VER at $TARGET"

# ── 3. Materialize scope-specific view (only when scope flags are supplied) ──
if [ -n "$TOOL" ] || [ -n "$TOOL_VERSION" ] || [ -n "$CONSUMER" ]; then
    _mat_json=$(python3 -c "
import sys, json
sys.path.insert(0, '$TARGET/lib')
from pathlib import Path
from honeycomb.overrides import materialize_flattened_view
ctx = {'tool': '$TOOL', 'tool_version': '$TOOL_VERSION', 'consumer': '$CONSUMER'}
ctx = {k: v for k, v in ctx.items() if v}
report = materialize_flattened_view(Path('$TARGET'), Path('$TARGET'), ctx)
print(json.dumps({
    'materialized': len(report.materialized),
    'overrides_used': len(report.overrides_used),
    'ambiguous': report.ambiguous,
    'removed_overrides': len(report.removed_overrides),
}))
") || die "materialization failed"
    _n=$(printf '%s' "$_mat_json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['materialized'])")
    _o=$(printf '%s' "$_mat_json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['overrides_used'])")
    step "materialized: $_n drawers, $_o overrides applied"
    printf '%s' "$_mat_json" \
        | python3 -c "import json,sys; [print(p) for p in json.load(sys.stdin).get('ambiguous', [])]" \
        | while IFS= read -r _p; do warn "ambiguous override: $_p"; done
fi

# ── 4. Always reindex ────────────────────────────────────────────────────────
# Content drift between text and DB is the single biggest correctness risk.
# We trade a few seconds at install time for a guarantee that recall is
# serving exactly the text we just installed.
step "rebuilding semantic index"
if python3 "$TARGET/tools/build_index.py" --hc-root "$TARGET"; then
    :
else
    rc=$?
    if [ "$rc" -ne 0 ]; then
        warn "build_index returned $rc — keyword recall still works"
    fi
fi

step "done. \$HONEYCOMB_ROOT=$TARGET (export this to use the install)"
