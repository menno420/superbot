"""Pure-function decoder for BTD6 ``_towers`` restriction arrays.

Lives in ``utils/`` so both ``cogs/btd6`` (event-detail embed) and
``services/btd6_live_query_service`` (live restriction lookup) can
import it without violating layer rules. No I/O, no Discord types.
"""

from __future__ import annotations

from typing import Any


def render_tower_restrictions(
    towers: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Group ``_towers`` entries into UI-ready categories.

    The race / boss / odyssey ``_btd6challengedocument`` body carries a
    ``_towers`` array (43 entries in the Reversed Loop fixture). Each
    entry has ``tower`` (name), ``max`` (0 = banned, N>=1 = limited,
    missing = unlimited), ``path1NumBlockedTiers`` / ``path2`` /
    ``path3`` (top-N tier blocks per path), and ``isHero`` (True for
    hero entries).

    Returns ``{category: [human strings]}`` covering: ``banned``,
    ``limited``, ``path_blocked``, ``heroes_banned``. Empty categories
    are omitted from the result so the caller can `if foo:` cleanly.
    """
    banned: list[str] = []
    limited: list[str] = []
    path_blocked: list[str] = []
    heroes_banned: list[str] = []

    for entry in towers:
        if not isinstance(entry, dict):
            continue
        tower = entry.get("tower")
        if not isinstance(tower, str) or not tower:
            continue
        is_hero = bool(entry.get("isHero", False))
        max_val = entry.get("max")
        max_int = max_val if isinstance(max_val, int) else None
        p1 = entry.get("path1NumBlockedTiers") or 0
        p2 = entry.get("path2NumBlockedTiers") or 0
        p3 = entry.get("path3NumBlockedTiers") or 0

        if is_hero and max_int == 0:
            heroes_banned.append(tower)
            continue
        if max_int == 0:
            banned.append(tower)
            continue
        if max_int is not None and max_int >= 1:
            limited.append(f"{tower} (max {max_int})")
            continue
        if p1 > 0 or p2 > 0 or p3 > 0:
            parts = []
            if p1:
                parts.append(f"path1 top {p1}")
            if p2:
                parts.append(f"path2 top {p2}")
            if p3:
                parts.append(f"path3 top {p3}")
            path_blocked.append(f"{tower} ({', '.join(parts)})")

    out: dict[str, list[str]] = {}
    if banned:
        out["banned"] = banned
    if limited:
        out["limited"] = limited
    if path_blocked:
        out["path_blocked"] = path_blocked
    if heroes_banned:
        out["heroes_banned"] = heroes_banned
    return out


__all__ = ["render_tower_restrictions"]
