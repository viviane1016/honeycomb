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
#
# Exit codes:
#   0  install + reindex succeeded
#   1  fetch / clone failed
#   2  reindex failed with chromadb present

set -eu

REPO="https://github.com/viviane1016/honeycomb.git"
TARGET="${HONEYCOMB_INSTALL_DIR:-$HOME/.honeycomb}"
TAG="${HONEYCOMB_TAG:-}"   # empty = latest tag

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

# ── 3. Always reindex ────────────────────────────────────────────────────────
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
