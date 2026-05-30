"""honeycomb.petitions — petition helpers: submit, list_pending, withdraw.

Public API
----------
submit(target, content, rationale, context, *, hc_root, overlay_root=None)
    Create a drawer-override file on a new branch in hc_root and open a
    GitHub PR via the ``gh`` CLI.  Returns a PetitionResult.

list_pending(consumer, *, hc_root, overlay_root=None)
    Enumerate *.queenfile_*.md overrides in canon and (optionally) an overlay.
    Returns list[PendingPetition] sorted by path.

withdraw(path, *, hc_root)
    Remove the override file from its petition branch, close the PR, and
    delete the remote branch via ``gh pr close --delete-branch``.

Dependencies
------------
* ``gh`` GitHub CLI must be installed and authenticated.
* ``hc_root`` must be a clean git worktree.
* honeycomb.overrides.parse_override_file (spec 001) handles frontmatter parsing.
"""
from __future__ import annotations

import hashlib
import pathlib
import subprocess
from dataclasses import dataclass

from honeycomb.overrides import parse_override_file


class PetitionError(RuntimeError):
    """Raised on missing gh CLI, dirty canon worktree, or subprocess non-zero exit."""


@dataclass(frozen=True)
class PetitionResult:
    branch: str
    pr_url: str | None
    overlay_path: pathlib.Path | None


@dataclass(frozen=True)
class PendingPetition:
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


def _branch_for_path(rel_path: str) -> str:
    return f"feat/petition-{hashlib.sha1(rel_path.encode('utf-8')).hexdigest()[:12]}"


def _build_override_content(
    target: str,
    scope: str,
    context: dict,
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

    # 4. Locate canonical drawer file (not an override).
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

    # 5. Compute override path; guard against clobbering.
    override_path = drawer_dir / f"{target}.queenfile_{scope}.md"
    if override_path.exists():
        raise PetitionError("override file already exists")

    # 6. Derive branch deterministically from the override file's relative path.
    rel_path = str(override_path.relative_to(hc_root))
    branch = _branch_for_path(rel_path)

    # 7. Checkout new branch.
    _run(["git", "checkout", "-b", branch], cwd=hc_root)

    # 8. Write override file.
    file_content = _build_override_content(target, scope, context, rationale, content)
    override_path.write_text(file_content, encoding="utf-8")

    # 9–10. Stage and commit.
    _run(["git", "add", rel_path], cwd=hc_root)
    _run(["git", "commit", "-m", f"petition: {target} for {scope}"], cwd=hc_root)

    # 11. Require gh CLI.
    try:
        _run(["which", "gh"], cwd=hc_root)
    except PetitionError:
        raise PetitionError("gh CLI not found")

    # 12. Open PR; last non-empty stdout line is the URL.
    pr_result = _run(
        ["gh", "pr", "create", "--title", f"petition: {target} for {scope}", "--body", rationale],
        cwd=hc_root,
    )
    pr_url: str | None = None
    for line in reversed(pr_result.stdout.splitlines()):
        if line.strip():
            pr_url = line.strip()
            break

    # 13. Mirror to overlay (unconditional on PR success).
    overlay_path: pathlib.Path | None = None
    if overlay_root is not None:
        overlay_file = overlay_root / override_path.relative_to(hc_root)
        overlay_file.parent.mkdir(parents=True, exist_ok=True)
        overlay_file.write_text(file_content, encoding="utf-8")
        overlay_path = overlay_file

    return PetitionResult(branch=branch, pr_url=pr_url, overlay_path=overlay_path)


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

                petition = PendingPetition(
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

    return sorted(entries.values(), key=lambda p: str(p.path))


def withdraw(path: str, *, hc_root: pathlib.Path) -> None:
    branch = _branch_for_path(path)

    # Verify branch exists.
    try:
        _run(["git", "rev-parse", "--verify", f"refs/heads/{branch}"], cwd=hc_root)
    except PetitionError:
        raise PetitionError("petition not found")

    # Checkout the petition branch.
    _run(["git", "checkout", branch], cwd=hc_root)

    # Remove and commit.
    _run(["git", "rm", path], cwd=hc_root)
    _run(["git", "commit", "-m", f"petition: withdraw {path}"], cwd=hc_root)

    # Close PR and delete branch.
    _run(["gh", "pr", "close", "--delete-branch", branch], cwd=hc_root)
