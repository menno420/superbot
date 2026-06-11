"""Equipment — pure, cross-game gear→stats model.

Maps the items a player has *equipped* into slots onto a generic
:class:`EffectiveStats` block that game logic reads.  This is the cross-game
"what is my character good at?" read model: a game asks for the stats, never
for specific item names.

It lives in ``utils/`` (stdlib-only, no Discord/DB/state) precisely *because*
it is shared: mining reads ``mining_power``/``light_radius``/``depth_access``,
deathmatch reads ``damage``/``defense``/``max_health``, and a future stat
service (``services/``, which may not import ``cogs/``) can build on it too.
This realises the brainstorm §7.4 "relocate the pure stat model to a shared
layer" step — extracted the moment a second game (deathmatch) needed it.

Slots and per-item stats are deliberately data (``_GEAR``): extend by adding
rows.  The combat slots follow the set-piece model (V-16 phase 1, owner
decision Q-0092): weapon + shield + the four armor pieces, each a 5-tier
family (bronze < iron < silver < gold < diamond), with a small same-tier
full-set bonus so collecting a complete set is a goal.  The full numbers
rationale (stat ladders, totals vs the duel constants, sim bands) lives in
``docs/planning/gear-set-numbers-2026-06-11.md``.
"""

from __future__ import annotations

from dataclasses import dataclass

# Equipment slots — each holds at most one item.  Mining slots (tool/light/
# charm) feed the mining stats; the six combat slots (weapon/shield + the four
# armor pieces) feed the deathmatch stats.  One equip/unequip path serves
# every slot.
TOOL = "tool"
LIGHT = "light"
CHARM = "charm"
WEAPON = "weapon"
SHIELD = "shield"
HELMET = "helmet"
CHESTPLATE = "chestplate"
LEGGINGS = "leggings"
BOOTS = "boots"
SLOTS: tuple[str, ...] = (
    TOOL,
    LIGHT,
    CHARM,
    WEAPON,
    SHIELD,
    HELMET,
    CHESTPLATE,
    LEGGINGS,
    BOOTS,
)

# The set-piece slots: a full same-tier loadout across these six grants the
# set bonus.  Mining slots are deliberately excluded — sets are a combat goal.
SET_SLOTS: tuple[str, ...] = (WEAPON, SHIELD, HELMET, CHESTPLATE, LEGGINGS, BOOTS)

# Gear tiers, weakest → strongest.  Bronze and silver are real mining ores
# (utils.mining.rewards loot rows), so every tier has a smelt-the-ore →
# forge-the-gear path.  Tier names double as the sprite-manifest vocabulary
# (utils.character_render: ``{family}_{tier}.png``).
TIER_ORDER: tuple[str, ...] = ("bronze", "iron", "silver", "gold", "diamond")


@dataclass(frozen=True)
class EffectiveStats:
    """Generic, game-neutral stat block computed from equipped gear (and,
    later, skills).  Each game reads only the subset it cares about — no game
    imports the item catalog.
    """

    mining_power: int = 0
    light_radius: int = 0
    depth_access: int = 0
    luck: int = 0
    loot_bonus: int = 0
    # Reserved for combat gear (deathmatch / PvP); zero until it exists.
    damage: int = 0
    defense: int = 0
    max_health: int = 0

    def __add__(self, other: EffectiveStats) -> EffectiveStats:
        return EffectiveStats(
            mining_power=self.mining_power + other.mining_power,
            light_radius=self.light_radius + other.light_radius,
            depth_access=self.depth_access + other.depth_access,
            luck=self.luck + other.luck,
            loot_bonus=self.loot_bonus + other.loot_bonus,
            damage=self.damage + other.damage,
            defense=self.defense + other.defense,
            max_health=self.max_health + other.max_health,
        )


# Display labels for the stat fields, in display order.  Keys MUST match the
# EffectiveStats field names (asserted in tests).
STAT_LABELS: dict[str, str] = {
    "mining_power": "Mining power",
    "light_radius": "Light",
    "depth_access": "Depth access",
    "luck": "Luck",
    "loot_bonus": "Loot bonus",
    "damage": "Damage",
    "defense": "Defense",
    "max_health": "Max health",
}


# Which slot each gear item fits, and the stats it contributes.
#
# Combat numbers are bounded by the duel constants (cogs/deathmatch_cog.py:
# 15 base damage / 100 base HP, flat defense reduction floored at 1): the
# full-diamond defense total (14) stays below the 15 base attack so a bare
# fighter's hits always land, and same/adjacent-tier fights stay competitive.
# Full design record: docs/planning/gear-set-numbers-2026-06-11.md.
_GEAR: dict[str, tuple[str, EffectiveStats]] = {
    # Mining gear → mining stats.  The "deeper ladders" tiers (gold/diamond,
    # 2026-06-10 owner decision: curated economy + deeper ladders) extend each
    # family; the diamond lantern's depth_access=3 is what makes MAGMA — and
    # its magma-only finds — reachable at all (no earlier light reached it).
    "pickaxe": (TOOL, EffectiveStats(mining_power=2)),
    "iron pickaxe": (TOOL, EffectiveStats(mining_power=4)),
    "gold pickaxe": (TOOL, EffectiveStats(mining_power=6)),
    "diamond pickaxe": (TOOL, EffectiveStats(mining_power=8, luck=1)),
    "torch": (LIGHT, EffectiveStats(light_radius=1, depth_access=1)),
    "lantern": (LIGHT, EffectiveStats(light_radius=2, depth_access=2)),
    "diamond lantern": (LIGHT, EffectiveStats(light_radius=3, depth_access=3)),
    "lucky charm": (CHARM, EffectiveStats(luck=1, loot_bonus=1)),
    # Starter combat gear — pre-metal entry pieces, strictly below bronze.
    "sword": (WEAPON, EffectiveStats(damage=3)),
    "shield": (SHIELD, EffectiveStats(defense=2, max_health=10)),
    # Swords (weapon slot) — damage ladder anchored to the pre-set values
    # (iron 6 / diamond 10 predate the set model and are preserved).
    "bronze sword": (WEAPON, EffectiveStats(damage=4)),
    "iron sword": (WEAPON, EffectiveStats(damage=6)),
    "silver sword": (WEAPON, EffectiveStats(damage=7)),
    "gold sword": (WEAPON, EffectiveStats(damage=8)),
    "diamond sword": (WEAPON, EffectiveStats(damage=10)),
    # Shields — the heaviest single defense piece (and the HP anchor).
    "bronze shield": (SHIELD, EffectiveStats(defense=2, max_health=12)),
    "iron shield": (SHIELD, EffectiveStats(defense=3, max_health=14)),
    "silver shield": (SHIELD, EffectiveStats(defense=3, max_health=16)),
    "gold shield": (SHIELD, EffectiveStats(defense=4, max_health=18)),
    "diamond shield": (SHIELD, EffectiveStats(defense=4, max_health=20)),
    # Helmets.
    "bronze helmet": (HELMET, EffectiveStats(defense=1, max_health=2)),
    "iron helmet": (HELMET, EffectiveStats(defense=1, max_health=3)),
    "silver helmet": (HELMET, EffectiveStats(defense=2, max_health=4)),
    "gold helmet": (HELMET, EffectiveStats(defense=2, max_health=5)),
    "diamond helmet": (HELMET, EffectiveStats(defense=2, max_health=6)),
    # Chestplates — the biggest armor piece.  "iron chestplate" and
    # "diamond chestplate" absorb the legacy "armor"/"diamond armor" items
    # (migration 068), rebalanced for five stacking defense pieces.
    "bronze chestplate": (CHESTPLATE, EffectiveStats(defense=2, max_health=6)),
    "iron chestplate": (CHESTPLATE, EffectiveStats(defense=2, max_health=8)),
    "silver chestplate": (CHESTPLATE, EffectiveStats(defense=3, max_health=10)),
    "gold chestplate": (CHESTPLATE, EffectiveStats(defense=3, max_health=12)),
    "diamond chestplate": (CHESTPLATE, EffectiveStats(defense=4, max_health=15)),
    # Leggings.
    "bronze leggings": (LEGGINGS, EffectiveStats(defense=1, max_health=4)),
    "iron leggings": (LEGGINGS, EffectiveStats(defense=1, max_health=5)),
    "silver leggings": (LEGGINGS, EffectiveStats(defense=2, max_health=6)),
    "gold leggings": (LEGGINGS, EffectiveStats(defense=2, max_health=8)),
    "diamond leggings": (LEGGINGS, EffectiveStats(defense=2, max_health=10)),
    # Boots.
    "bronze boots": (BOOTS, EffectiveStats(defense=1, max_health=2)),
    "iron boots": (BOOTS, EffectiveStats(defense=1, max_health=3)),
    "silver boots": (BOOTS, EffectiveStats(defense=1, max_health=4)),
    "gold boots": (BOOTS, EffectiveStats(defense=2, max_health=5)),
    "diamond boots": (BOOTS, EffectiveStats(defense=2, max_health=6)),
}

# Same-tier full-set bonus (Q-0092): equipping all six SET_SLOTS with gear of
# one tier adds ``damage = tier_index`` and ``max_health = 3 × tier_index``
# (bronze +1/+3 … diamond +5/+15).  Small on purpose — the set is a collection
# goal, not a power cliff; defense is deliberately NOT in the bonus so the
# full-diamond defense total stays below the 15 base attack damage.
SET_BONUS_DAMAGE_PER_TIER = 1
SET_BONUS_HEALTH_PER_TIER = 3


# Max durability — how many uses the "active" unit of a gear item survives
# before it breaks (consumed from inventory; the brainstorm §7.5 keystone
# resource sink).  Generous on purpose: a sink, not an annoyance (§6.8 P5).
# Combat gear (sword/shield/…) has maxes defined now but no wear path until a
# later slice ticks durability in duels.  Items absent from this table never
# wear (safe default for unknown/legacy items).
MAX_DURABILITY: dict[str, int] = {
    "pickaxe": 60,
    "iron pickaxe": 150,
    "gold pickaxe": 220,
    "diamond pickaxe": 400,
    "torch": 40,
    "lantern": 100,
    "diamond lantern": 180,
    "lucky charm": 80,
    # Starters.
    "sword": 60,
    "shield": 90,
}

# Combat-set durability — one ladder for all six families (gear wears once
# per duel, so these are generous: a sink, not an annoyance).
_SET_DURABILITY: tuple[int, ...] = (80, 150, 200, 260, 320)
_SET_FAMILIES: tuple[str, ...] = (
    "sword",
    "shield",
    "helmet",
    "chestplate",
    "leggings",
    "boots",
)
MAX_DURABILITY.update(
    {
        f"{tier} {family}": _SET_DURABILITY[i]
        for i, tier in enumerate(TIER_ORDER)
        for family in _SET_FAMILIES
    },
)


def max_durability(item_name: str) -> int | None:
    """Uses before *item_name* breaks, or None if it does not wear."""
    return MAX_DURABILITY.get(item_name.lower())


def gear_names() -> tuple[str, ...]:
    """Every equippable item name (for fuzzy resolution / pickers)."""
    return tuple(_GEAR)


def slot_for(item_name: str) -> str | None:
    """The slot *item_name* equips into, or None if it is not equippable."""
    entry = _GEAR.get(item_name.lower())
    return entry[0] if entry else None


def is_equippable(item_name: str) -> bool:
    return slot_for(item_name) is not None


def item_stats(item_name: str) -> EffectiveStats:
    """Stat contribution of a single gear item (all-zero if unknown)."""
    entry = _GEAR.get(item_name.lower())
    return entry[1] if entry else EffectiveStats()


def gear_tier(item_name: str) -> str | None:
    """The set tier of *item_name* (``"bronze"`` … ``"diamond"``), or None.

    Only set-slot gear is tiered — the ``"{tier} {family}"`` naming convention
    is the registry (it is also the sprite-manifest convention).  Starters
    ("sword", "shield") and mining gear return None.
    """
    entry = _GEAR.get(item_name.lower())
    if entry is None or entry[0] not in SET_SLOTS:
        return None
    first = item_name.lower().split()[0]
    return first if first in TIER_ORDER else None


def tier_index(tier: str) -> int:
    """1-based strength index of *tier* (bronze=1 … diamond=5)."""
    return TIER_ORDER.index(tier) + 1


def active_set_tier(equipped: dict[str, str]) -> str | None:
    """The tier of a complete same-tier combat set, or None.

    All six :data:`SET_SLOTS` must hold gear of one tier; any empty slot,
    starter, or tier mismatch disqualifies the set.
    """
    tiers: set[str] = set()
    for slot in SET_SLOTS:
        tier = gear_tier(equipped.get(slot, ""))
        if tier is None:
            return None
        tiers.add(tier)
    return tiers.pop() if len(tiers) == 1 else None


def set_bonus(equipped: dict[str, str]) -> EffectiveStats:
    """The same-tier full-set bonus for *equipped* (all-zero without a set)."""
    tier = active_set_tier(equipped)
    if tier is None:
        return EffectiveStats()
    idx = tier_index(tier)
    return EffectiveStats(
        damage=SET_BONUS_DAMAGE_PER_TIER * idx,
        max_health=SET_BONUS_HEALTH_PER_TIER * idx,
    )


def set_progress(equipped: dict[str, str]) -> tuple[str, int] | None:
    """``(tier, pieces_equipped)`` for the player's most-advanced partial set.

    Drives the Gear panel's "Bronze set 4/6" line.  Ties break toward the
    stronger tier; returns None when no set-slot item is tiered.
    """
    counts: dict[str, int] = {}
    for slot in SET_SLOTS:
        tier = gear_tier(equipped.get(slot, ""))
        if tier is not None:
            counts[tier] = counts.get(tier, 0) + 1
    if not counts:
        return None
    best = max(counts, key=lambda t: (counts[t], tier_index(t)))
    return best, counts[best]


def compute_stats(equipped: dict[str, str]) -> EffectiveStats:
    """Sum the stats of every equipped item, plus any full-set bonus.

    *equipped* is ``{slot: name}``.
    """
    total = EffectiveStats()
    for item_name in equipped.values():
        total = total + item_stats(item_name)
    return total + set_bonus(equipped)


def describe_stats(stats: EffectiveStats) -> list[tuple[str, int]]:
    """Non-zero ``(label, value)`` pairs in display order — pure (no Discord)."""
    return [
        (STAT_LABELS[name], getattr(stats, name))
        for name in STAT_LABELS
        if getattr(stats, name)
    ]


__all__ = [
    "TOOL",
    "LIGHT",
    "CHARM",
    "WEAPON",
    "SHIELD",
    "HELMET",
    "CHESTPLATE",
    "LEGGINGS",
    "BOOTS",
    "SLOTS",
    "SET_SLOTS",
    "TIER_ORDER",
    "SET_BONUS_DAMAGE_PER_TIER",
    "SET_BONUS_HEALTH_PER_TIER",
    "EffectiveStats",
    "STAT_LABELS",
    "MAX_DURABILITY",
    "max_durability",
    "gear_names",
    "slot_for",
    "is_equippable",
    "item_stats",
    "gear_tier",
    "tier_index",
    "active_set_tier",
    "set_bonus",
    "set_progress",
    "compute_stats",
    "describe_stats",
]
