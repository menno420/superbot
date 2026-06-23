"""Shared hub child-discovery primitive.

A *mother hub* (Games, Community, Utility, …) surfaces the subsystems that
declare ``parent_hub == <hub key>`` as child buttons on its panel.  Before this
module each hub re-implemented the same "filter ``SUBSYSTEMS`` by ``parent_hub``,
sort deterministically" discovery by hand (``views.games.hub.discover_game_children``,
``views.community.hub.discover_community_children``,
``cogs.utility_cog.discover_utility_children``).  Three copies meant a hub could
silently drift — the exact class behind the *discoverability audit* general-cog
bug, where the Utility panel rendered none of its children.

This is the **one** discovery seam every hub now delegates to.  It is the data
half of the centralization the consolidation/ultracode fleet converges on; the
*button* half (the per-hub forwarding button + its Back-nav) stays in each hub
for now and is the first fleet consolidation unit
(``docs/planning/consolidation-fleet-plan-2026-06-23.md``).

Pure: no Discord objects, no I/O — just a deterministic read of the registry, so
it is trivially unit-testable and safe to call at view-construction time.
"""

from __future__ import annotations

from collections.abc import Mapping

from utils.subsystem_registry import SUBSYSTEMS

__all__ = ["discover_hub_children"]


def discover_hub_children(
    hub_key: str,
    *,
    group_order: Mapping[str, int] | None = None,
) -> list[tuple[str, dict]]:
    """Return the registry children of ``hub_key`` in deterministic UI order.

    A *child* is any ``SUBSYSTEMS`` entry whose ``parent_hub`` equals
    ``hub_key``.  Each result is ``(subsystem_key, dict(meta))`` — the meta is
    copied so callers can mutate it freely.

    Ordering is fully deterministic so the rendered button order is stable:

    * when ``group_order`` is given (the Games hub passes its
      ``hub_group`` → rank map), entries sort by **group rank first**, then
      ``ui_priority``, then key — competitive games before activities, etc.;
    * otherwise (Community / Utility and every future hub) entries sort by
      ``ui_priority`` then key.

    Unknown ``hub_group`` values rank last (99); missing ``ui_priority`` ranks
    last (99).  Mirrors the three hand-rolled copies this replaces exactly, so
    their existing tests pin the behaviour.
    """
    children = [
        (name, dict(meta))
        for name, meta in SUBSYSTEMS.items()
        if meta.get("parent_hub") == hub_key
    ]
    if group_order is None:
        children.sort(key=lambda item: (item[1].get("ui_priority", 99), item[0]))
    else:
        children.sort(
            key=lambda item: (
                group_order.get(item[1].get("hub_group") or "", 99),
                item[1].get("ui_priority", 99),
                item[0],
            ),
        )
    return children
