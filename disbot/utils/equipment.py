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
rows.  Combat slots (weapon/armor) and their damage/defense stats are reserved
in :class:`EffectiveStats` but unused until combat gear exists.
"""

from __future__ import annotations

from dataclasses import dataclass

# Equipment slots — each holds at most one item.  Mining slots (tool/light/
# charm) feed the mining stats; combat slots (weapon/armor) feed the deathmatch
# stats.  One equip/unequip path serves every slot.
TOOL = "tool"
LIGHT = "light"
CHARM = "charm"
WEAPON = "weapon"
ARMOR = "armor"
SLOTS: tuple[str, ...] = (TOOL, LIGHT, CHARM, WEAPON, ARMOR)


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
_GEAR: dict[str, tuple[str, EffectiveStats]] = {
    # Mining gear → mining stats.
    "pickaxe": (TOOL, EffectiveStats(mining_power=2)),
    "iron pickaxe": (TOOL, EffectiveStats(mining_power=4)),
    "torch": (LIGHT, EffectiveStats(light_radius=1, depth_access=1)),
    "lantern": (LIGHT, EffectiveStats(light_radius=2, depth_access=2)),
    "lucky charm": (CHARM, EffectiveStats(luck=1, loot_bonus=1)),
    # Combat gear → deathmatch stats.  Deliberately a SMALL, fair edge over the
    # base 100 HP / 15-damage duel — gear tilts a fight, it does not decide it
    # (a bare fighter still wins on crits + good defends).  Tune here.
    "sword": (WEAPON, EffectiveStats(damage=3)),
    "iron sword": (WEAPON, EffectiveStats(damage=6)),
    "shield": (ARMOR, EffectiveStats(defense=2, max_health=10)),
    "armor": (ARMOR, EffectiveStats(defense=4, max_health=20)),
}


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


def compute_stats(equipped: dict[str, str]) -> EffectiveStats:
    """Sum the stats of every equipped item.  *equipped* is ``{slot: name}``."""
    total = EffectiveStats()
    for item_name in equipped.values():
        total = total + item_stats(item_name)
    return total


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
    "SLOTS",
    "EffectiveStats",
    "STAT_LABELS",
    "slot_for",
    "is_equippable",
    "item_stats",
    "compute_stats",
    "describe_stats",
]
