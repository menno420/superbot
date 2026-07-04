"""Fishing curios — cosmetic carvings crafted from coral (the second rare drop).

The fishing rare-material pattern's *second* instance (the roadmap's "▶ next
offline successor" — a dedicated craft material that feeds a **new** craft target
rather than the premium bait). The **pearl** (:data:`utils.fishing.rewards.PEARL_ITEM`)
sinks into a *bait*; **coral** (:data:`utils.fishing.rewards.CORAL_ITEM`, a
deepwater-only reef drop) sinks into a *cosmetic collection* — carved "curios".

A curio is a purely-cosmetic collectible: an :class:`utils.mining.items.ItemKind`
``TREASURE`` item (non-sellable, no crafting use) stored in the shared
``mining_inventory``, so it needs **no migration** and is shown by the existing
inventory browser. The value is the *collection* — a completionist goal like the
Fishdex or the trophy board — and a perpetual home for coral: a lucky deep-sea
fisher can carve the whole shelf.

Pure + stdlib-only (no Discord, no DB): :mod:`services.fishing_workflow` owns the
craft write (debit coral, grant the curio in one transaction); the cog reads this
catalog. Mirrors :mod:`utils.fishing.bait`'s recipe helpers exactly. Numbers
sim-pinned in ``docs/planning/fishing-coral-numbers-2026-07-01.md``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Curio:
    """One carved curio — a cosmetic collectible crafted from coral.

    ``item`` is the stable ``mining_inventory`` key (also the display name, kept
    lower-cased to match how inventory keys are stored); ``coral_cost`` coral are
    consumed to carve one. Rarer curios cost more coral — the collection's
    long-tail. Purely cosmetic: no gameplay effect, never sold.
    """

    key: str  # stable lookup key (also the inventory item key)
    item: str  # the mining_inventory item name (== key; explicit for clarity)
    name: str  # display name
    emoji: str
    coral_cost: int
    rarity: str  # display rarity (Uncommon / Rare / Epic) — cosmetic only


#: The curio shelf, cheapest first. Each entry is one carving craftable from coral;
#: the ascending coral cost makes the top curio a genuine deep-sea trophy. Tunable
#: constants — pin changes in the numbers doc + the test.
CURIO_CATALOG: tuple[Curio, ...] = (
    Curio(
        "coral shell",
        "coral shell",
        "Carved Coral Shell",
        "🐚",
        coral_cost=2,
        rarity="Uncommon",
    ),
    Curio(
        "coral seahorse",
        "coral seahorse",
        "Coral Seahorse",
        "🌊",
        coral_cost=4,
        rarity="Rare",
    ),
    Curio("coral idol", "coral idol", "Coral Idol", "🗿", coral_cost=8, rarity="Epic"),
    Curio(
        "coral leviathan",
        "coral leviathan",
        "Coral Leviathan",
        "🐉",
        coral_cost=16,
        rarity="Legendary",
    ),
)

_BY_KEY: dict[str, Curio] = {c.key: c for c in CURIO_CATALOG}

#: The stable keys, in shelf order (for selects / validation).
CURIO_KEYS: tuple[str, ...] = tuple(c.key for c in CURIO_CATALOG)

#: The inventory item names every curio occupies — used to tally a player's
#: collection ("2 of 3 curios carved") without re-deriving it at each call site.
CURIO_ITEMS: tuple[str, ...] = tuple(c.item for c in CURIO_CATALOG)


def curio_by_key(key: str | None) -> Curio | None:
    """The :class:`Curio` for *key*, or ``None`` for an unknown / empty key."""
    if not key:
        return None
    return _BY_KEY.get(key)


def cost_text(curio: Curio) -> str:
    """A short human label of a curio's cost, e.g. ``4 🪸 coral``."""
    return f"{curio.coral_cost} 🪸 coral"


def craftable_key_for(text: str | None) -> str | None:
    """Resolve typed *text* (a key or a display name) to a curio key.

    Case-insensitive; matches either the stable key (``coral idol``) or the
    display name (``Coral Idol``). Returns ``None`` for empty input or an
    unrecognised curio — so ``!craftcurio "coral idol"`` and ``!craftcurio idol``…
    (the latter is *not* a full key, so it does not resolve) behave predictably.
    """
    if not text:
        return None
    needle = text.strip().lower()
    for key in CURIO_KEYS:
        curio = _BY_KEY.get(key)
        if curio is None:
            continue
        if needle in (key.lower(), curio.name.lower()):
            return key
    return None


def collection_progress(inventory: dict[str, int]) -> tuple[int, int]:
    """``(owned, total)`` — how many distinct curios *inventory* holds vs. the set.

    A curio is "owned" when its item key is present with a positive quantity.
    Pure over an ``{item: qty}`` map; the cog renders the count.
    """
    owned = sum(1 for item in CURIO_ITEMS if inventory.get(item, 0) > 0)
    return owned, len(CURIO_ITEMS)


__all__ = [
    "Curio",
    "CURIO_CATALOG",
    "CURIO_KEYS",
    "CURIO_ITEMS",
    "curio_by_key",
    "cost_text",
    "craftable_key_for",
    "collection_progress",
]
