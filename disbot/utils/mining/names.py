"""Fuzzy item-name resolution — the old crafting cog's matcher, modernized.

The legacy system resolved free-typed item names through an alias file +
``difflib`` ratios; the restored commands required exact lowercase names.
This brings the forgiveness back as one shared, pure resolver: commands
resolve the user's text against the *relevant* candidate set (recipes for
crafting, the shop for buying, equippables for equipping…) before calling
:mod:`services.mining_workflow` — so workflow error copy stays pinned and
only fires for genuinely unknown names.
"""

from __future__ import annotations

import difflib
from collections.abc import Iterable

# Hand-curated shorthand the fuzzy ratio alone wouldn't catch.  Values must
# be canonical catalog names.
ALIASES: dict[str, str] = {
    "pick": "pickaxe",
    "ipick": "iron pickaxe",
    "iron pick": "iron pickaxe",
    "gpick": "gold pickaxe",
    "gold pick": "gold pickaxe",
    "dpick": "diamond pickaxe",
    "diamond pick": "diamond pickaxe",
    "lamp": "lantern",
    "dlantern": "diamond lantern",
    "charm": "lucky charm",
    "dsword": "diamond sword",
    # The pre-set "armor"/"diamond armor" items became chestplates
    # (migration 068, V-16 set-piece model) — keep the muscle-memory names.
    "armor": "iron chestplate",
    "darmor": "diamond chestplate",
    "diamond armor": "diamond chestplate",
    "tnt": "dynamite",
}


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().replace("_", " ").split())


def resolve_item_name(
    query: str,
    candidates: Iterable[str],
    *,
    aliases: dict[str, str] | None = None,
    cutoff: float = 0.7,
) -> str | None:
    """Resolve free-typed *query* to one of *candidates*, or None.

    Resolution order: exact (normalized) → alias map → ``difflib`` closest
    match at *cutoff*.  Only ever returns a member of *candidates*, so a
    caller can trust the result as a canonical name.
    """
    pool = {c.lower(): c for c in candidates}
    if not pool:
        return None
    norm = _normalize(query)
    if norm in pool:
        return pool[norm]
    alias_target = (aliases or ALIASES).get(norm)
    if alias_target and alias_target in pool:
        return pool[alias_target]
    close = difflib.get_close_matches(norm, list(pool), n=1, cutoff=cutoff)
    return pool[close[0]] if close else None


__all__ = ["ALIASES", "resolve_item_name"]
