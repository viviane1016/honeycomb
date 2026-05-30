---
depends-on: [003]
output-files: [lib/honeycomb/manifest.py, tools/install.sh, tests/test_manifest.py]
scribe-model: claude-opus-4-7
---

# Spec 009 — Petition manifest generator + operator output

## Builder model

claude-sonnet-4-6

## Goal

Add `lib/honeycomb/manifest.py` that walks `git log <prev>..<curr>` for the canon repo, classifies commits by the `petition: adopted|declined|pending` prefix convention, and exposes helpers to write the manifest JSON and format a one-line operator summary; wire `tools/install.sh` to capture the pre-pull SHA, call the generator after the (existing) checkout + materialization steps, and print the summary alongside the install step output.

## Scope

**New `lib/honeycomb/manifest.py`** (stdlib only):

Public surface:
- `generate_manifest(hc_root: pathlib.Path, previous_sha: str | None, current_sha: str) -> dict`
- `write_manifest(manifest: dict, destination: pathlib.Path) -> None`
- `summary_line(manifest: dict, previous_sha: str | None) -> str`

`generate_manifest` behaviour:
- When `previous_sha` is `None` or equals `current_sha`, return `{"accepted": [], "declined": [], "pending": [], "previous_sha": previous_sha, "current_sha": current_sha, "warnings": []}` without invoking git (first-install / no-op case).
- Otherwise run `git -C <hc_root> log --format=%H%x00%s <previous_sha>..<current_sha>` via `subprocess.run(..., check=False, capture_output=True, text=True)`. If the command exits non-zero, return the empty manifest above with `warnings: ["git-log-failed: <stderr-first-line>"]` and DO NOT raise.
- Split stdout on `\n`; for each non-empty line, split once on `\x00` into `(sha, subject)`.
- Classify by the subject's prefix (case-sensitive, leading whitespace allowed):
  - Matches `^petition:\s*adopted\b` → append `{"sha": sha, "subject": subject}` to `accepted`.
  - Matches `^petition:\s*declined\b` → append to `declined`.
  - Matches `^petition:\s*pending\b` → append to `pending`.
  - Matches `petition` anywhere in the subject but does NOT match one of the three prefixes above → append to `pending` AND add a one-entry `"convention-not-followed: <sha-short>"` string to `warnings` (per the plan's "If the convention is not followed, all such commits classify as `pending`").
  - Subject does not mention `petition` at all → skip.
- The final dict shape: `{"accepted": [...], "declined": [...], "pending": [...], "previous_sha": str|None, "current_sha": str, "warnings": [str]}`. Each entry inside `accepted`/`declined`/`pending` is `{"sha": str, "subject": str}` — keep it minimal; richer parsing (target/scope extraction) is non-goal for v1.1.

`write_manifest` behaviour:
- `destination.parent.mkdir(parents=True, exist_ok=True)`
- Serialise with `json.dumps(manifest, indent=2, sort_keys=True)` and write atomically: write to `destination.with_suffix(destination.suffix + ".tmp")` then `os.replace(tmp, destination)`.

`summary_line` behaviour:
- Always returns a single line, no trailing newline.
- When `previous_sha is None`: `"Petitions: (first install — no prior range to scan)"`.
- When `previous_sha == manifest["current_sha"]`: `"Petitions: (no canon update — 0 commits in range)"`.
- Otherwise: `"Petitions: <N> accepted, <M> declined, <K> pending since <prev-short>"` where `<prev-short>` is `previous_sha[:8]`.
- If `manifest["warnings"]` is non-empty, append ` [warnings: <count>]` to the line.

**Edit `tools/install.sh`** (additive, no behavioural change when no commits are in range):

- Immediately after the `TARGET="${HONEYCOMB_INSTALL_DIR:-$HOME/.honeycomb}"` line (top-of-script context block), add `PREVIOUS_SHA=""` and, only when `[ -d "$TARGET/.git" ]`, capture `PREVIOUS_SHA="$(git -C "$TARGET" rev-parse HEAD 2>/dev/null || true)"`. This MUST run before the fetch/clone/checkout block so the SHA reflects the pre-pull state.
- After spec 003's materialization step and BEFORE the `build_index.py` invocation, add a manifest step:

```sh
# ── 4. Petition manifest ──────────────────────────────────────────────────────
CURRENT_SHA="$(git -C "$TARGET" rev-parse HEAD 2>/dev/null || echo "")"
if [ -n "$CURRENT_SHA" ]; then
    PREV_ARG="${PREVIOUS_SHA:-}"
    if PETITION_SUMMARY="$(PYTHONPATH="$TARGET/lib" python3 -c "
import sys, json
from pathlib import Path
from honeycomb.manifest import generate_manifest, write_manifest, summary_line
prev = sys.argv[1] or None
curr = sys.argv[2]
m = generate_manifest(Path(sys.argv[3]), prev, curr)
write_manifest(m, Path(sys.argv[3]) / '.petition-manifest.json')
print(summary_line(m, prev))
" "$PREV_ARG" "$CURRENT_SHA" "$TARGET")"; then
        step "$PETITION_SUMMARY"
    else
        warn "petition manifest generation failed (continuing)"
    fi
fi
```

  Failure of the python snippet emits a `warn` but does NOT `die` — manifest generation is observability, not correctness.

- Add a `bash tools/install.sh` usage-block bullet documenting the new `$TARGET/.petition-manifest.json` artifact and noting that the summary line classifies commits by the `petition: adopted|declined|pending` prefix convention.
- The build_index call stays as-is; it runs after the manifest step.

**New tests** `tests/test_manifest.py` (stdlib `unittest`, no third-party deps):

Helper at file top: a `_init_repo(tmpdir)` that runs `git init -q -b main`, `git config user.email t@t.t`, `git config user.name t`, and a `_commit(repo, subject)` that creates `git commit --allow-empty -m "<subject>"` and returns `git rev-parse HEAD`. Both via `subprocess.run(..., cwd=repo, check=True, capture_output=True)`.

Tests:
- `test_generate_manifest_classifies_three_prefixes`: seed three commits with subjects `petition: adopted drawer-a for bees-v1.18`, `petition: declined drawer-b for bees-v1.18`, `petition: pending drawer-c for scarab`. Capture SHAs of `prev` (initial commit before the three) and `curr` (HEAD). Assert each bucket has exactly one entry with the right SHA and subject, `warnings == []`.
- `test_generate_manifest_empty_when_prev_is_none`: pass `previous_sha=None`; assert all three buckets empty, no git invocation needed.
- `test_generate_manifest_empty_when_prev_equals_curr`: pass `previous_sha == current_sha`; assert all three buckets empty.
- `test_generate_manifest_non_petition_commits_skipped`: seed `chore: tidy` and `fix: typo` commits; assert no entries in any bucket.
- `test_generate_manifest_misclassified_falls_into_pending`: seed a commit with subject `petition: maybe-adopt drawer-x` (matches `petition` but not one of the three exact prefixes); assert it lands in `pending` AND `warnings` contains exactly one entry referencing its short SHA.
- `test_generate_manifest_handles_git_failure`: pass `previous_sha="0000000000000000000000000000000000000000"` (a SHA that won't resolve in the temp repo); assert the manifest comes back empty, `warnings` has one `git-log-failed:` entry, and the function does NOT raise.
- `test_write_manifest_atomic`: call `write_manifest(m, dest)` against a tmp path; assert the destination file exists, parses back via `json.loads`, and the round-tripped dict equals the input.
- `test_summary_line_first_install`: `summary_line({...empty...}, None)` ends with `"(first install — no prior range to scan)"`.
- `test_summary_line_no_change`: `previous_sha == current_sha` → `"(no canon update — 0 commits in range)"`.
- `test_summary_line_normal`: manifest with 2 accepted, 1 declined, 0 pending and `previous_sha="abcdef1234567890..."` → `"Petitions: 2 accepted, 1 declined, 0 pending since abcdef12"`.
- `test_summary_line_with_warnings`: appends `" [warnings: 1]"` when `warnings` non-empty.

**Non-goals**:
- No PR-status enrichment (we do not query `gh pr view` for adopted/declined commits — the manifest is built from commit metadata only).
- No richer per-entry parsing (target/scope extraction from subject) — that's a v1.2 candidate.
- No retention/rotation of `.petition-manifest.json` — each install overwrites it atomically.
- No coupling to spec 006's petition helpers — this module reads canon git log only and is unaware of overlay/petition state on the consumer side.

## Failing test

File: `tests/test_manifest.py`
Function: `TestManifest.test_generate_manifest_classifies_three_prefixes`
Reason: fails with `ImportError` because `lib/honeycomb/manifest.py` does not yet exist; the test imports `generate_manifest` at module top so every test in the file errors until the module is created. Once the builder implements `generate_manifest` per the prefix-classification rules above, this test passes (along with the rest of the suite).

## Builder prompt

You are building spec 009 of the honeycomb v1.1 rollout: the petition manifest generator and its install-time wire-up.

Repo layout you will touch (paths repo-relative):
- `lib/honeycomb/manifest.py` — new module, stdlib only.
- `tools/install.sh` — append a pre-pull SHA capture and a post-materialization manifest step.
- `tests/test_manifest.py` — new test module, stdlib `unittest`.

Specs 003 (install materialization), 004 (log writer), and others land in earlier units; do not modify their files. The only `tools/install.sh` regions you touch are: (a) one new line near the top to capture `PREVIOUS_SHA` before any fetch/clone, and (b) one new step after the materialization block and before the `build_index.py` invocation. Leave the existing tag-resolution, clone/update, materialization, and build-index regions untouched.

**`lib/honeycomb/manifest.py` public API**

```python
def generate_manifest(hc_root: pathlib.Path,
                      previous_sha: str | None,
                      current_sha: str) -> dict: ...
def write_manifest(manifest: dict, destination: pathlib.Path) -> None: ...
def summary_line(manifest: dict, previous_sha: str | None) -> str: ...
```

`generate_manifest`:
- If `previous_sha` is `None` or equals `current_sha`, return the empty manifest dict (see schema below) without invoking git.
- Otherwise run `git -C <hc_root> log --format=%H%x00%s <previous_sha>..<current_sha>` via `subprocess.run(..., check=False, capture_output=True, text=True)`. On non-zero exit, return the empty manifest with `warnings == ["git-log-failed: <stderr first line>"]` — never raise from git failure.
- For each `<sha>\x00<subject>` line, classify by prefix on the subject:
  - `^petition:\s*adopted\b` → `accepted` bucket
  - `^petition:\s*declined\b` → `declined` bucket
  - `^petition:\s*pending\b` → `pending` bucket
  - Subject contains `petition` (any case-insensitive substring) but matches none of the above three exact prefixes → `pending` bucket AND append `"convention-not-followed: <sha[:8]>"` to `warnings`.
  - Subject does not mention `petition` at all → skip.
- Each bucket entry is `{"sha": str, "subject": str}` — nothing more.

Manifest dict schema (every field always present):

```python
{
    "accepted":     [{"sha": str, "subject": str}, ...],
    "declined":     [{"sha": str, "subject": str}, ...],
    "pending":      [{"sha": str, "subject": str}, ...],
    "previous_sha": str | None,
    "current_sha":  str,
    "warnings":     [str, ...],
}
```

`write_manifest`:
- `destination.parent.mkdir(parents=True, exist_ok=True)`.
- Serialise with `json.dumps(manifest, indent=2, sort_keys=True)`.
- Write to `destination.with_suffix(destination.suffix + ".tmp")` then `os.replace(tmp, destination)` for atomic replace.

`summary_line`:
- One line, no trailing newline.
- `previous_sha is None` → `"Petitions: (first install — no prior range to scan)"`.
- `previous_sha == manifest["current_sha"]` → `"Petitions: (no canon update — 0 commits in range)"`.
- Otherwise → `"Petitions: <N> accepted, <M> declined, <K> pending since <previous_sha[:8]>"`.
- If `manifest["warnings"]` is non-empty, append `" [warnings: <count>]"` to the returned string.

**`tools/install.sh` changes**

1. Add `PREVIOUS_SHA=""` near the top alongside the existing `TARGET=...` declaration, and capture `PREVIOUS_SHA="$(git -C "$TARGET" rev-parse HEAD 2>/dev/null || true)"` ONLY when `[ -d "$TARGET/.git" ]`. This MUST run BEFORE the fetch/clone/checkout block so the SHA reflects the pre-pull state.
2. After spec 003's materialization region and BEFORE the `build_index.py` invocation, insert a manifest step (see Scope for the verbatim snippet). The snippet:
   - Captures `CURRENT_SHA` from the post-checkout state.
   - Skips silently when `CURRENT_SHA` is empty (no git state — shouldn't happen post-checkout, but be defensive).
   - Calls the Python helper via `PYTHONPATH="$TARGET/lib" python3 -c "..."` passing `(prev, curr, target)` as `sys.argv[1..3]`. The snippet invokes `generate_manifest`, `write_manifest`, and `summary_line` in sequence, prints the summary string, and the shell echoes it via `step "$PETITION_SUMMARY"`.
   - On python-snippet failure: emit `warn "petition manifest generation failed (continuing)"` and proceed to `build_index.py` — manifest is observability, not correctness, so MUST NOT `die`.
3. Update the usage block at the top of the file (the existing `# Usage:` comment) to add one bullet noting the `.petition-manifest.json` artifact and the `petition: adopted|declined|pending` prefix convention.

**`tests/test_manifest.py`** (stdlib `unittest` only, no third-party deps):

- Use `subprocess.run(["git", ...], cwd=repo, check=True, capture_output=True)` to set up tmp git repos under `tempfile.TemporaryDirectory()`. A small `_init_repo(repo)` helper at module scope is encouraged: runs `git init -q -b main`, configures `user.email`/`user.name`, and creates an initial empty commit so subsequent SHAs have a parent.
- Use `git commit --allow-empty -m "<subject>"` to seed commits with specific subjects without managing file changes.
- Capture SHAs via `subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()`.
- Implement all eleven tests enumerated in Scope. Importable as `from honeycomb.manifest import generate_manifest, write_manifest, summary_line`.
- Make sure `lib/` is on `sys.path` via the project's existing test convention (the prior specs' test files set this up — mirror their pattern; if they use a `tests/__init__.py` shim or per-file `sys.path.insert`, do the same).
- For the `test_generate_manifest_handles_git_failure` test, pass the literal 40-zero SHA string `"0" * 40` as `previous_sha`; git will fail to resolve it and the function should return the empty manifest with `git-log-failed:` in warnings.

**Constraints**:
- Stdlib only — `pathlib`, `subprocess`, `json`, `os`, `re`, `dataclasses` (optional), `tempfile`, `unittest`.
- Do not import from `honeycomb.recall`, `honeycomb.semantic`, `honeycomb.overrides`, `honeycomb.log`, `honeycomb.petitions`, or `honeycomb.__init__` — keep this module's dependency arrow inbound-only.
- Do not register the manifest helpers in `lib/honeycomb/__init__.py` — re-exports are handled by spec 013.
- Do not modify any file except the three in `output-files`.
- Match the existing `tools/install.sh` style: `step`/`warn`/`die` helpers, `set -eu`, no bashisms beyond what the file already uses.
- The python snippet inside `install.sh` MUST tolerate `$PREVIOUS_SHA` being empty by reading `sys.argv[1] or None` (Python sees an empty string from a missing/empty shell var and converts it to `None`).
- Keep the `petition:` prefix matching case-sensitive (lowercase `petition:`); the broader "subject mentions petition anywhere" check used for the warning bucket is case-insensitive.

**Success check**: run `python3 -m unittest discover -s tests` from the repo root; all eleven new tests in `tests/test_manifest.py` pass alongside the existing spec 001–008 suites. `git diff tools/install.sh` is contained to (a) the one-line `PREVIOUS_SHA` capture region near the top and (b) the new manifest step before `build_index.py`; the rest of the script is untouched. `cat $TARGET/.petition-manifest.json` (after a successful install against a canon with seeded `petition:` commits) parses as a JSON object with the documented schema.

## Success check

- `python3 -m unittest discover -s tests` exits 0 from the repo root; all eleven tests in `tests/test_manifest.py` pass and no prior-spec test regresses.
- Diff review confirms:
  - `lib/honeycomb/manifest.py` exposes exactly the three public symbols above and depends only on stdlib.
  - `tools/install.sh` changes are confined to the two regions (top-of-script SHA capture + post-materialization manifest step + one usage-comment bullet); the existing clone/update, materialization, and build-index regions are byte-identical to their pre-spec form.
  - The manifest step uses `warn` (not `die`) on python-snippet failure.
  - No new module imports from `honeycomb.*` siblings; dependency arrow is one-way.
- Manual smoke (optional, not required for spec sign-off): in a scratch git repo, seed three commits matching the three prefixes; call `generate_manifest(repo_path, prev_sha, head_sha)`; verify the returned dict matches the documented schema.

## Commit message

```
feat(manifest): petition manifest generator + install-time summary (#009)

Add lib/honeycomb/manifest.py with generate_manifest / write_manifest /
summary_line. The generator walks `git log <prev>..<curr>` on the canon
repo, classifies commit subjects by the `petition: adopted|declined|pending`
prefix convention, and returns a structured manifest dict. tools/install.sh
captures the pre-pull SHA, invokes the generator after materialization,
writes `.petition-manifest.json` to the install root, and prints a one-line
operator summary. Manifest failures warn but do not abort install — the
manifest is observability, not correctness.

Refs: .bees/honeycomb-v1-1/specs/009-petition-manifest-generator.md
```
