"""honeycomb.petitions — petition helpers: submit, list_pending, withdraw.

Public API
----------
submit(target, content, rationale, context, *, hc_root, overlay_root=None)
    Create a drawer-override file on a new branch in hc_root and open a
    GitHub PR via the ``gh`` CLI.  Returns a PetitionResult.

list_pending(consumer, *, hc_root, overlay_root=None)
    Enumerate *.queenfile_*.md overrides in canon and (optionally) an overlay.
    Returns list[PendingPetition] sorted by petition_id.

withdraw(petition_id, *, hc_root)
    Remove the override file from its petition branch, close the PR, and
    delete the remote branch via ``gh pr close --delete-branch``.

Dependencies
------------
* ``gh`` GitHub CLI must be installed and authenticated.
* ``hc_root`` must be a clean git worktree.
* honeycomb.overrides.parse_override_file (spec 001) handles frontmatter parsing.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
from dataclasses import dataclass

from honeycomb.overrides import parse_override_file


class PetitionError(RuntimeError):
    """Raised on missing gh CLI, dirty canon worktree, or subprocess non-zero exit."""


@dataclass(frozen=True)
class PetitionResult:
    petition_id: str
    branch: str
    pr_url: str | None
    overlay_path: pathlib.Path | None


@dataclass(frozen=True)
class PendingPetition:
    petition_id: str
    target: str
    consumer: str | None
    tool: str | None
    tool_version: str | None
    path: pathlib.Path
    source: str  # "canon" or "overlay"
    rationale: str


def _run(argv: list[str], *, cwd: pathlib.Path) -> subprocess.CompletedProcess:
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise PetitionError(f"{argv[0]} failed: {result.stderr}")
    return result


_COMMENT_BLOCK_RE = re.compile(r"\A\s*<!--(.*?)-->", re.DOTALL)
_PETITION_ID_LINE_RE = re.compile(r"^\s*petition_id:\s*(.+?)\s*$", re.MULTILINE)


def _read_petition_id(path: pathlib.Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = _COMMENT_BLOCK_RE.match(text)
    if m is None:
        return None
    hit = _PETITION_ID_LINE_RE.search(m.group(1))
    return hit.group(1) if hit else None


def _scope_from_filename(filename: str) -> str:
    sep = ".queenfile_"
    idx = filename.find(sep)
    if idx == -1:
        return filename
    after = filename[idx + len(sep):]
    return after[:-3] if after.endswith(".md") else after


def _build_override_content(
    target: str,
    scope: str,
    context: dict,
    petition_id: str,
    rationale: str,
    content: str,
) -> str:
    tool = context.get("tool") or "null"
    tool_version = context.get("tool_version") or "null"
    consumer = context.get("consumer") or "null"
    rationale_block = "\n".join(f"  {line}" for line in rationale.splitlines()) if rationale else "  "
    return (
        f"<!-- {target}.queenfile_{scope}.md\n"
        f"target: {target}\n"
        f"tool: {tool}\n"
        f"tool_version: {tool_version}\n"
        f"consumer: {consumer}\n"
        f"petition_id: {petition_id}\n"
        f"rationale: |\n"
        f"{rationale_block}\n"
        f"-->\n\n"
        f"{content}\n"
    )


def submit(
    target: str,
    content: str,
    rationale: str,
    context: dict,
    *,
    hc_root: pathlib.Path,
    overlay_root: pathlib.Path | None = None,
) -> PetitionResult:
    # 1. Verify hc_root is a git repo.
    _run(["git", "rev-parse", "--git-dir"], cwd=hc_root)

    # 2. Require clean worktree.
    status = _run(["git", "status", "--porcelain"], cwd=hc_root)
    if status.stdout.strip():
        raise PetitionError("canon worktree dirty")

    # 3. Compute scope tag from context.
    tool = context.get("tool")
    tool_version = context.get("tool_version")
    consumer = context.get("consumer")

    if tool and tool_version and consumer:
        scope = f"{tool}-{tool_version}_{consumer}"
    elif tool and tool_version:
        scope = f"{tool}-{tool_version}"
    elif consumer:
        scope = consumer
    else:
        raise PetitionError("petition context must include at least tool+tool_version or consumer")

    # 4. Derive date from git log — deterministic, avoids datetime.now.
    log_result = _run(["git", "log", "-1", "--format=%cI", "HEAD"], cwd=hc_root)
    date_part = log_result.stdout.strip()[:10].replace("-", "")  # YYYYMMDD

    # 5. Count existing queenfile files to compute sequence number.
    existing_count = 0
    for wing_dir in hc_root.glob("wing_*"):
        existing_count += sum(1 for _ in wing_dir.rglob("*.queenfile_*.md"))

    # 6. Build petition_id and branch name.
    petition_id = f"{date_part}-{existing_count:03d}-{scope}"
    branch = f"feat/petition-{petition_id}"

    # 7. Locate canonical drawer file (not an override).
    canonical_matches: list[pathlib.Path] = []
    for wing_dir in hc_root.glob("wing_*"):
        for p in wing_dir.rglob(f"{target}.md"):
            if ".queenfile_" not in p.name:
                canonical_matches.append(p)

    if len(canonical_matches) == 0:
        raise PetitionError(f"canonical drawer '{target}.md' not found under {hc_root}")
    if len(canonical_matches) > 1:
        raise PetitionError(f"canonical drawer '{target}.md' is ambiguous: {canonical_matches}")

    drawer_dir = canonical_matches[0].parent

    # 8. Compute override path; guard against clobbering.
    override_path = drawer_dir / f"{target}.queenfile_{scope}.md"
    if override_path.exists():
        raise PetitionError("override file already exists")

    # 9. Checkout new branch.
    _run(["git", "checkout", "-b", branch], cwd=hc_root)

    # 10. Write override file.
    file_content = _build_override_content(target, scope, context, petition_id, rationale, content)
    override_path.write_text(file_content, encoding="utf-8")

    # 11–12. Stage and commit.
    rel_path = str(override_path.relative_to(hc_root))
    _run(["git", "add", rel_path], cwd=hc_root)
    _run(["git", "commit", "-m", f"petition: {target} for {scope}"], cwd=hc_root)

    # 13. Require gh CLI.
    try:
        _run(["which", "gh"], cwd=hc_root)
    except PetitionError:
        raise PetitionError("gh CLI not found")

    # 14. Open PR; last non-empty stdout line is the URL.
    pr_result = _run(
        ["gh", "pr", "create", "--title", f"petition: {target} for {scope}", "--body", rationale],
        cwd=hc_root,
    )
    pr_url: str | None = None
    for line in reversed(pr_result.stdout.splitlines()):
        if line.strip():
            pr_url = line.strip()
            break

    # 15. Mirror to overlay (unconditional on PR success).
    overlay_path: pathlib.Path | None = None
    if overlay_root is not None:
        overlay_file = overlay_root / override_path.relative_to(hc_root)
        overlay_file.parent.mkdir(parents=True, exist_ok=True)
        overlay_file.write_text(file_content, encoding="utf-8")
        overlay_path = overlay_file

    return PetitionResult(petition_id, branch, pr_url, overlay_path)


def list_pending(
    consumer: str | None,
    *,
    hc_root: pathlib.Path,
    overlay_root: pathlib.Path | None = None,
) -> list[PendingPetition]:
    entries: dict[str, PendingPetition] = {}

    def _collect(root: pathlib.Path, source: str) -> None:
        for wing_dir in root.glob("wing_*"):
            if not wing_dir.is_dir():
                continue
            for p in wing_dir.rglob("*.queenfile_*.md"):
                try:
                    spec = parse_override_file(p)
                except Exception:
                    continue

                # Filter by consumer: None means "all"; None spec.consumer means "canon-wide".
                if consumer is not None and spec.consumer != consumer and spec.consumer is not None:
                    continue

                pid = _read_petition_id(p)
                if pid is None:
                    pid = f"unknown-{_scope_from_filename(p.name)}"

                petition = PendingPetition(
                    petition_id=pid,
                    target=spec.target,
                    consumer=spec.consumer,
                    tool=spec.tool,
                    tool_version=spec.tool_version,
                    path=p,
                    source=source,
                    rationale=spec.rationale,
                )
                rel_key = str(p.relative_to(root))
                # Overlay wins when the same relative path appears in both roots.
                if rel_key not in entries or source == "overlay":
                    entries[rel_key] = petition

    _collect(hc_root, "canon")
    if overlay_root is not None and overlay_root.exists():
        _collect(overlay_root, "overlay")

    return sorted(entries.values(), key=lambda p: p.petition_id)


def withdraw(petition_id: str, *, hc_root: pathlib.Path) -> None:
    branch = f"feat/petition-{petition_id}"

    # Verify branch exists.
    try:
        _run(["git", "rev-parse", "--verify", f"refs/heads/{branch}"], cwd=hc_root)
    except PetitionError:
        raise PetitionError("petition not found")

    # Checkout the petition branch.
    _run(["git", "checkout", branch], cwd=hc_root)

    # Find the override file from the tip commit.
    diff_result = _run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
        cwd=hc_root,
    )
    override_rel_path = diff_result.stdout.strip()

    # Remove and commit.
    _run(["git", "rm", override_rel_path], cwd=hc_root)
    _run(["git", "commit", "-m", f"petition: withdraw {petition_id}"], cwd=hc_root)

    # Close PR and delete branch.
    _run(["gh", "pr", "close", "--delete-branch", branch], cwd=hc_root)
