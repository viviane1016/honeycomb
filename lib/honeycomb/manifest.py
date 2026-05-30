"""Petition manifest generator for honeycomb canon installs (spec 009)."""

import json
import os
import pathlib
import re
import subprocess

_RE_ADOPTED = re.compile(r'^\s*petition:\s*adopted\b')
_RE_DECLINED = re.compile(r'^\s*petition:\s*declined\b')
_RE_PENDING_PREFIX = re.compile(r'^\s*petition:\s*pending\b')
_RE_PETITION_CI = re.compile(r'petition', re.IGNORECASE)


def _empty_manifest(previous_sha, current_sha):
    return {
        "accepted": [],
        "declined": [],
        "pending": [],
        "previous_sha": previous_sha,
        "current_sha": current_sha,
        "warnings": [],
    }


def generate_manifest(hc_root: pathlib.Path,
                      previous_sha: "str | None",
                      current_sha: str) -> dict:
    if previous_sha is None or previous_sha == current_sha:
        return _empty_manifest(previous_sha, current_sha)

    result = subprocess.run(
        ["git", "-C", str(hc_root), "log",
         "--format=%H%x00%s",
         f"{previous_sha}..{current_sha}"],
        check=False,
        capture_output=True,
        text=True,
    )
    manifest = _empty_manifest(previous_sha, current_sha)
    if result.returncode != 0:
        stderr = result.stderr or ""
        first_line = stderr.splitlines()[0] if stderr.strip() else ""
        manifest["warnings"].append(f"git-log-failed: {first_line}")
        return manifest

    for line in result.stdout.split("\n"):
        if not line:
            continue
        parts = line.split("\x00", 1)
        if len(parts) != 2:
            continue
        sha, subject = parts
        if _RE_ADOPTED.match(subject):
            manifest["accepted"].append({"sha": sha, "subject": subject})
        elif _RE_DECLINED.match(subject):
            manifest["declined"].append({"sha": sha, "subject": subject})
        elif _RE_PENDING_PREFIX.match(subject):
            manifest["pending"].append({"sha": sha, "subject": subject})
        elif _RE_PETITION_CI.search(subject):
            manifest["pending"].append({"sha": sha, "subject": subject})
            manifest["warnings"].append(f"convention-not-followed: {sha[:8]}")

    return manifest


def write_manifest(manifest: dict, destination: pathlib.Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(manifest, indent=2, sort_keys=True)
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    tmp.write_text(content)
    os.replace(tmp, destination)


def summary_line(manifest: dict, previous_sha: "str | None") -> str:
    if previous_sha is None:
        line = "Petitions: (first install — no prior range to scan)"
    elif previous_sha == manifest["current_sha"]:
        line = "Petitions: (no canon update — 0 commits in range)"
    else:
        n = len(manifest["accepted"])
        m = len(manifest["declined"])
        k = len(manifest["pending"])
        line = f"Petitions: {n} accepted, {m} declined, {k} pending since {previous_sha[:8]}"

    if manifest.get("warnings"):
        line += f" [warnings: {len(manifest['warnings'])}]"

    return line
