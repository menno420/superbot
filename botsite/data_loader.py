"""Load + validate the public ``site.json`` subset (stdlib only).

The bot site renders the committed ``botsite/data/site.json`` — the public subset
produced by ``scripts/export_dashboard_data.py`` (plan §2.2). This module is the one
read seam: it loads the file, falls back to a safe empty shape if it is missing or
corrupt (so the app never crashes on a bad/absent artifact — the same robustness the
dashboard's ``load_data`` has), and exposes the known top-level families with safe
defaults.

It is intentionally tiny and dependency-free (no ``disbot`` import, no third-party
import) so it can be unit-tested without the web stack installed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "site.json"

# The empty shape mirrors the producer's whitelist (see export_dashboard_data
# SITE_TOPLEVEL_KEYS) so every template can rely on the keys existing even when the
# artifact is absent at runtime — friendly empty states, never a KeyError.
_EMPTY: dict[str, Any] = {
    "meta": {"generated_at": "", "build": {}},
    "counts": {"commands": 0, "features": 0, "games": 0},
    "catalogue": [],
    "commands": [],
    "bot_changelog": [],
}


def load_site_data(path: Path = DATA_FILE) -> dict[str, Any]:
    """Load ``site.json``, returning a safe empty shape on any read/parse failure.

    The returned dict always carries the whitelisted top-level keys (missing ones
    are backfilled from :data:`_EMPTY`), so callers never guard for absent families.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty()
    if not isinstance(raw, dict):
        return _empty()
    data = _empty()
    for key in _EMPTY:
        if key in raw:
            data[key] = raw[key]
    return data


def _empty() -> dict[str, Any]:
    """A fresh copy of the empty data shape (never share the module-level dict)."""
    return json.loads(json.dumps(_EMPTY))


def build_meta(data: dict[str, Any]) -> dict[str, Any]:
    """Return the build provenance block for the "generated" freshness badge.

    The status/trust band renders this, honestly labelled "as of last deploy" (plan
    §3 — generated build-meta is the v1 source; the public site never reads the
    bot's live control API). Always a dict (possibly empty).
    """
    meta = data.get("meta", {})
    build = meta.get("build", {})
    return build if isinstance(build, dict) else {}


def commands_by_category(data: dict[str, Any]) -> list[tuple[str, list[dict]]]:
    """Group the public command reference by category, sorted (for the reference page).

    A read-only projection used by the wired ``/commands`` route; the template (a
    later unit) renders the groups. Pure, so it is unit-testable here.
    """
    grouped: dict[str, list[dict]] = {}
    for cmd in data.get("commands", []):
        grouped.setdefault(cmd.get("category") or "other", []).append(cmd)
    for cmds in grouped.values():
        cmds.sort(key=lambda c: c.get("name") or "")
    return sorted(grouped.items())


def features_by_category(data: dict[str, Any]) -> list[tuple[str, list[dict]]]:
    """Group the catalogue (features showcase) by category, sorted.

    Backs the wired ``/features`` route; the template lands in a later unit.
    """
    grouped: dict[str, list[dict]] = {}
    for entry in data.get("catalogue", []):
        grouped.setdefault(entry.get("category") or "other", []).append(entry)
    for entries in grouped.values():
        entries.sort(key=lambda e: e.get("display_name") or e.get("key") or "")
    return sorted(grouped.items())
