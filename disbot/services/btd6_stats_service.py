"""Lazy per-tower BTD6 stats (combat stats + per-upgrade cost/XP).

The lean catalog (towers.json) is loaded at boot by
:mod:`services.btd6_data_service`; the heavy per-tower stats live in
``disbot/data/btd6/stats/<id>.json`` and are loaded here only when a tower is
actually opened.

Two views over the same data, per the agreed UX:

* :func:`normal_stats` — the glanceable default (damage, type + immunities,
  pierce, cooldown, range, and a few headline specials incl. cash income);
* the full per-tier structure (``TowerStats.tier``) for the Pro view.

Pure data access — no Discord, no network (the bot never fetches at runtime;
``scripts/fetch_bloonswiki.py`` produces these files offline).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from utils.btd6 import tier_codes

STATS_ROOT = Path(__file__).resolve().parents[1] / "data" / "btd6" / "stats"
HERO_STATS_ROOT = STATS_ROOT / "heroes"


@dataclass(frozen=True)
class NormalStats:
    """The glanceable headline view of a single tier."""

    damage: int | None
    damage_type: str | None
    cannot_pop: str | None
    pierce: int | None
    cooldown: float | None
    attack_range: float | None
    can_see_camo: bool
    specials: tuple[str, ...]


@dataclass(frozen=True)
class TowerStats:
    """All stored stats for one tower (lazy-loaded)."""

    tower_id: str
    canonical: str
    game_version: str
    base_cost: int | None
    category: str | None
    paragon_cost: int | None
    paragon_name: str | None
    upgrades: tuple[dict[str, Any], ...]
    tiers: dict[str, dict[str, Any]]

    def tier(self, code: str) -> dict[str, Any] | None:
        return self.tiers.get(code)

    @property
    def has_combat_stats(self) -> bool:
        return bool(self.tiers)

    def tier_codes(self) -> tuple[str, ...]:
        """Present tiers in display order: the canonical 16, then crosspaths."""
        return tier_codes.ordered_codes(self.tiers.keys())

    def crosspaths_for(self, single_code: str) -> tuple[str, ...]:
        """Present crosspath codes built on a single-path tier.

        e.g. ``crosspaths_for("200")`` -> present crosspaths whose path-1 tier is
        2 (``201``, ``202``, ``210``, ``220`` …). Empty for the base, a crosspath
        argument, or an old 16-tier file with no crosspath data.
        """
        if not tier_codes.is_single_path(single_code):
            return ()
        path = tier_codes.primary_path(single_code)
        if path is None:
            return ()
        tier = tier_codes.digits(single_code)[path - 1]
        present = [
            code
            for code in self.tiers
            if tier_codes.is_valid_code(code)
            and tier_codes.is_crosspath(code)
            and tier_codes.digits(code)[path - 1] == tier
        ]
        return tier_codes.ordered_codes(present)


# Hero levels run 1..20. Only the ~6 heroes with a bloonswiki stats module
# have a file here; the rest are cost/ability-only (no per-level combat stats).
_HERO_LEVEL_CODES: tuple[str, ...] = tuple(str(n) for n in range(1, 21))


@dataclass(frozen=True)
class HeroStats:
    """All stored per-level stats for one hero (lazy-loaded)."""

    hero_id: str
    canonical: str
    game_version: str
    base_cost: int | None
    cost_chimps: int | None
    levels: dict[str, dict[str, Any]]

    def level(self, code: str) -> dict[str, Any] | None:
        return self.levels.get(code)

    @property
    def has_combat_stats(self) -> bool:
        return bool(self.levels)

    def level_codes(self) -> tuple[str, ...]:
        return tuple(code for code in _HERO_LEVEL_CODES if code in self.levels)


# ---------------------------------------------------------------------------
# Cached loader
# ---------------------------------------------------------------------------

_CACHE: dict[str, TowerStats | None] = {}
_HERO_CACHE: dict[str, HeroStats | None] = {}


def _load(tower_id: str) -> TowerStats | None:
    path = STATS_ROOT / f"{tower_id}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return TowerStats(
        tower_id=data.get("tower_id", tower_id),
        canonical=data.get("canonical", ""),
        game_version=str(data.get("game_version", "")),
        base_cost=data.get("base_cost"),
        category=data.get("category"),
        paragon_cost=data.get("paragon_cost"),
        paragon_name=data.get("paragon_name"),
        upgrades=tuple(data.get("upgrades", ())),
        tiers=data.get("tiers", {}),
    )


def get_tower_stats(tower_id: str) -> TowerStats | None:
    """Return a tower's stats, or ``None`` if no stats file exists."""
    if tower_id not in _CACHE:
        _CACHE[tower_id] = _load(tower_id)
    return _CACHE[tower_id]


def _load_hero(hero_id: str) -> HeroStats | None:
    path = HERO_STATS_ROOT / f"{hero_id}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return HeroStats(
        hero_id=data.get("hero_id", hero_id),
        canonical=data.get("canonical", ""),
        game_version=str(data.get("game_version", "")),
        base_cost=data.get("base_cost"),
        cost_chimps=data.get("cost_chimps"),
        levels=data.get("levels", {}),
    )


def get_hero_stats(hero_id: str) -> HeroStats | None:
    """Return a hero's per-level stats, or ``None`` if no stats file exists.

    Only heroes with a bloonswiki stats module (~6 of the roster) have a file;
    the rest are prose-only and return ``None`` here.
    """
    if hero_id not in _HERO_CACHE:
        _HERO_CACHE[hero_id] = _load_hero(hero_id)
    return _HERO_CACHE[hero_id]


def reset_cache() -> None:
    """Test seam: drop the loaded-stats caches."""
    _CACHE.clear()
    _HERO_CACHE.clear()


# ---------------------------------------------------------------------------
# Normal-view derivation
# ---------------------------------------------------------------------------


def _iter_dicts(node: Any) -> Any:
    """Yield every dict in a nested stats structure."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _iter_dicts(value)
    elif isinstance(node, list):
        for value in node:
            yield from _iter_dicts(value)


def _main_projectile(tier: dict[str, Any]) -> dict[str, Any] | None:
    """The highest-damage projectile across all of the tier's attacks."""
    best: dict[str, Any] | None = None
    for attack in tier.get("attacks", []):
        for proj in attack.get("projectiles", []):
            if (proj.get("damage") or 0) > (best.get("damage", 0) if best else 0):
                best = proj
    return best


def _money(value: Any) -> str:
    return f"${int(value):,}" if isinstance(value, (int, float)) else str(value)


def _collect_specials(
    tier: dict[str, Any],
    main: dict[str, Any] | None,
) -> tuple[str, ...]:
    specials: list[str] = []
    seen: set[str] = set()

    def add(text: str) -> None:
        if text not in seen:
            seen.add(text)
            specials.append(text)

    if main and main.get("damageModifierForMoabs"):
        add(f"+{main['damageModifierForMoabs']} vs MOAB-Class")

    for node in _iter_dicts(tier):
        name = str(node.get("name", ""))
        if "Stun" in name and node.get("lifespan"):
            add(f"Stun {node['lifespan']}s")
        if node.get("cashPerRound"):
            add(f"Income {_money(node['cashPerRound'])}/round")
        if node.get("cashMinimum"):
            add(f"Cash crate {_money(node['cashMinimum'])}")
        if node.get("damageToBad"):
            add(f"Ability: {_money(node['damageToBad'])} to BADs/Bosses")
        elif "cooldown" in node and node.get("cooldown"):
            add(f"Ability ({node['cooldown']}s cooldown)")
        if node.get("pushAmount"):
            add("Knockback")
    return tuple(specials)


def normal_stats(tier: dict[str, Any]) -> NormalStats:
    """Distil a tier's full stats into the glanceable normal view."""
    main = _main_projectile(tier)
    attacks = tier.get("attacks", [])
    # The attack's cooldown is stored under its raw field name ``rate`` (seconds).
    cooldown = attacks[0].get("rate") if attacks else None
    # ``filterInvisible`` on the attack/projectile means it cannot target Camo.
    can_see_camo = not any(node.get("filterInvisible") for node in _iter_dicts(tier))
    return NormalStats(
        damage=main.get("damage") if main else None,
        damage_type=main.get("damage_type") if main else None,
        cannot_pop=main.get("cannot_pop") if main else None,
        pierce=main.get("pierce") if main else None,
        cooldown=cooldown,
        attack_range=tier.get("range"),
        can_see_camo=can_see_camo,
        specials=_collect_specials(tier, main),
    )


__all__ = [
    "HeroStats",
    "NormalStats",
    "TowerStats",
    "get_hero_stats",
    "get_tower_stats",
    "normal_stats",
    "reset_cache",
]
