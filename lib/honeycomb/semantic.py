# lib/honeycomb/semantic.py — ChromaDB-backed semantic recall over the
# four-level honeycomb structure. Best-effort: returns [] on any backend
# failure so callers can fall through to keyword recall.
#
# Adapted from legacy bees/lib/bees/hc_index.py:
#   • One vector per closet (not per flat room)
#   • Embedded text = closet name + closet body + truncated drawer concat
#   • Metadata carries wing/room/closet/hall/path
#   • Cache path: ~/.mempalace/honeycomb_v1/  (distinct from legacy v0.x
#     cache at ~/.mempalace/honeycomb/ so side-by-side install doesn't
#     collide)
#
# Return shape is identical to recall.palace_recall — composite `room` field.

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Iterable, Optional

from honeycomb.recall import _discover_closets, _default_root, _read_drawer_text, score_match

log = logging.getLogger(__name__)

HC_PALACE_PATH = Path("~/.mempalace/honeycomb_v1").expanduser()
HC_COLLECTION = "honeycomb_v1_closets"
VERSION_SENTINEL_ID = "__version__"


def _get_collection(db_path: Optional[Path] = None):
    """Open or create the honeycomb chroma collection. Returns None on any error."""
    try:
        import chromadb
    except ImportError:
        log.debug("honeycomb.semantic: chromadb not installed")
        return None
    # Silence chromadb 0.6 posthog telemetry signature mismatch (best-effort).
    try:
        import posthog
        posthog.capture = lambda *a, **kw: None  # noqa: E731
    except Exception:  # noqa: BLE001
        pass
    path = Path(db_path) if db_path is not None else HC_PALACE_PATH
    try:
        path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(path))
        try:
            return client.get_collection(HC_COLLECTION)
        except Exception:
            return client.create_collection(HC_COLLECTION)
    except Exception as e:  # noqa: BLE001
        log.warning("honeycomb.semantic: cannot open collection at %s: %s", path, e)
        return None


def _read_honeycomb_version(hc_root: Path) -> str:
    """Read the honeycomb VERSION file. Empty string if missing."""
    try:
        return (hc_root / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _embed_text(closet: dict) -> str:
    """Compose the text to embed for a closet.

    Closet text (≤500 chars by convention) is the authored summary — high
    signal. Drawer concat is appended truncated so body-only matches still
    work but closet signal dominates."""
    name_blob = f"{closet['wing']} {closet['room']} {closet['closet']}"
    closet_text = closet.get("closet_text") or ""
    drawer_text = _read_drawer_text(closet["full_dir"])[:1500]
    return f"{name_blob}\n\n{closet_text}\n\n{drawer_text}".strip()


def index_closets(
    hc_root: Optional[Path] = None,
    db_path: Optional[Path] = None,
) -> tuple[int, str]:
    """Build (or rebuild) the semantic index from the four-level honeycomb tree.

    Returns (n_closets_indexed, honeycomb_version). Raises RuntimeError if the
    chromadb backend can't be opened — callers decide whether to escalate."""
    root = Path(hc_root) if hc_root is not None else _default_root()
    col = _get_collection(db_path)
    if col is None:
        raise RuntimeError(
            "honeycomb.semantic: cannot open chroma collection — is chromadb installed?"
        )

    # Wipe existing entries for a clean rebuild (corpus is small).
    try:
        existing = col.get(include=[])
        existing_ids = existing.get("ids") or []
        if existing_ids:
            col.delete(ids=existing_ids)
    except Exception as e:  # noqa: BLE001
        log.warning("honeycomb.semantic: could not clear existing entries: %s", e)

    closets = _discover_closets(root)
    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict] = []
    for c in closets:
        text = _embed_text(c)
        if not text:
            continue
        ids.append(f"{c['wing']}/{c['room']}/{c['closet']}")
        docs.append(text)
        metas.append({
            "wing": c["wing"],
            "room": c["room"],
            "closet": c["closet"],
            "hall": c.get("hall") or "",
            "path": str(c["path"]),
            "closet_text": (c.get("closet_text") or "")[:2000],
        })

    if ids:
        col.add(ids=ids, documents=docs, metadatas=metas)

    version = _read_honeycomb_version(root)
    col.upsert(
        ids=[VERSION_SENTINEL_ID],
        documents=[f"honeycomb VERSION sentinel: {version}"],
        metadatas=[{"sentinel": "version", "version": version}],
    )
    return len(ids), version


def get_indexed_version(db_path: Optional[Path] = None) -> Optional[str]:
    col = _get_collection(db_path)
    if col is None:
        return None
    try:
        result = col.get(ids=[VERSION_SENTINEL_ID], include=["metadatas"])
    except Exception:
        return None
    metas = result.get("metadatas") or []
    if not metas:
        return None
    return metas[0].get("version")


def is_index_current(
    hc_root: Optional[Path] = None,
    db_path: Optional[Path] = None,
) -> bool:
    root = Path(hc_root) if hc_root is not None else _default_root()
    expected = _read_honeycomb_version(root)
    actual = get_indexed_version(db_path)
    return bool(expected) and expected == actual


# ── Filter normalisation (mirrors recall.py for API symmetry) ────────────────


def _normalize_filter(values: Optional[Iterable[str]], prefix: str) -> Optional[set[str]]:
    if values is None:
        return None
    out: set[str] = set()
    for v in values:
        if not v:
            continue
        out.add(v if v.startswith(prefix) else f"{prefix}{v}")
    return out


# ── Public API ───────────────────────────────────────────────────────────────


def palace_recall_semantic(
    query: str,
    wings: Optional[Iterable[str]] = None,
    halls: Optional[Iterable[str]] = None,
    top_k: int = 3,
    *,
    # v1.1 extension points (accepted-and-ignored for forward compat):
    scope: Optional[str] = None,
    tools: Optional[Iterable[str]] = None,
    models: Optional[Iterable[str]] = None,
    project: Optional[str] = None,
    overlay_root: Optional[Path] = None,
    db_path: Optional[Path] = None,
) -> list[dict]:
    """Vector recall over honeycomb closets. Returns the same shape as
    palace_recall (composite `room` field).

    Returns [] on any backend failure (chromadb missing, no index built,
    query error) — callers fall through to keyword recall.

    overlay_root: Optional consumer-side overlay tree; when set and existing,
        overlay drawer files win over canon at matching (wing, room, closet)
        keys via linear-scan keyword scoring. Absent or non-existent path =
        canon-only (v1.0 behaviour).
    """
    col = _get_collection(db_path)
    if col is None or not query or not str(query).strip():
        return []
    wing_filter = _normalize_filter(wings, "wing_")
    hall_filter = _normalize_filter(halls, "hall_")

    # Over-fetch to leave room for filtering out the version sentinel and
    # any non-matching wings/halls after the chroma query.
    n_fetch = max(int(top_k) * 4, int(top_k) + 4)

    try:
        result = col.query(
            query_texts=[query],
            n_results=n_fetch,
            include=["metadatas", "distances"],
        )
    except Exception as e:  # noqa: BLE001
        log.warning("honeycomb.semantic: query failed: %s", e)
        return []

    ids_list = (result.get("ids") or [[]])[0]
    metas_list = (result.get("metadatas") or [[]])[0]
    out: list[dict] = []
    for rid, meta in zip(ids_list, metas_list):
        if rid == VERSION_SENTINEL_ID:
            continue
        wing = meta.get("wing")
        hall = meta.get("hall") or None
        if wing_filter is not None and wing not in wing_filter:
            continue
        if hall_filter is not None and hall not in hall_filter:
            continue
        room_name = meta.get("room") or ""
        closet_name = meta.get("closet") or ""
        out.append({
            "wing": wing,
            "room": f"{room_name}/{closet_name}",  # composite, matches keyword API
            "hall": hall,
            "path": meta.get("path"),
            "closet": meta.get("closet_text") or "",
        })
        if len(out) >= int(top_k):
            break

    # Overlay merge: linear-scan keyword pass over overlay closets.
    if overlay_root is not None and Path(overlay_root).is_dir():
        overlay_closets = _discover_closets(Path(overlay_root))
        overlay_matches: list[tuple[int, dict]] = []
        for oc in overlay_closets:
            if wing_filter is not None and oc["wing"] not in wing_filter:
                continue
            if hall_filter is not None and oc.get("hall") not in hall_filter:
                continue
            s = score_match(query, oc)
            if s > 0:
                closet_key = re.sub(r"\.queenfile_[^.]+$", "", oc["closet"])
                if closet_key != oc["closet"]:
                    oc = dict(oc, closet=closet_key)
                overlay_matches.append((s, oc))

        if overlay_matches:
            # Build index from canon results: composite room -> position.
            # composite room = "room_name/closet_name" — split on last "/"
            canon_keys: dict[tuple, int] = {}
            for i, item in enumerate(out):
                parts = item["room"].rsplit("/", 1)
                r, cl = (parts[0], parts[1]) if len(parts) == 2 else (item["room"], "")
                canon_keys[(item["wing"], r, cl)] = i

            for _s, oc in overlay_matches:
                key = (oc["wing"], oc["room"], oc["closet"])
                overlay_entry = {
                    "wing": oc["wing"],
                    "room": f"{oc['room']}/{oc['closet']}",
                    "hall": oc.get("hall"),
                    "path": str(oc["path"]),
                    "closet": oc.get("closet_text") or "",
                }
                if key in canon_keys:
                    out[canon_keys[key]] = overlay_entry
                else:
                    out.append(overlay_entry)

            out = out[:max(0, int(top_k))]

    return out
