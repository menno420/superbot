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

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from utils.btd6 import paragon_degrees, tier_codes

STATS_ROOT = Path(__file__).resolve().parents[1] / "data" / "btd6" / "stats"
HERO_STATS_ROOT = STATS_ROOT / "heroes"
PARAGON_STATS_ROOT = STATS_ROOT / "paragons"


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


@dataclass(frozen=True)
class ParagonAbility:
    """One named paragon ability (activated or passive), curated from the wiki."""

    name: str
    kind: str  # "activated" | "passive"
    cooldown: int | None  # seconds, for activated abilities
    description: str


@dataclass(frozen=True)
class ParagonStats:
    """All stored stats for one paragon (lazy-loaded).

    Only the degree-INDEPENDENT base node is stored; the degree-dependent table
    (pierce / damage / cooldown / boss multiplier per degree 1..100) is derived
    on demand from the wiki's formulas via :func:`degree`. All thirteen paragons
    have a file: eleven from their bloonswiki stats module, and two (Root of all
    Nature, Herald of Everfrost) transcribed from their article prose because no
    machine-readable module exists — :attr:`is_prose_sourced` flags those so the
    UI / AI can label the lower-fidelity origin.
    """

    paragon_id: str
    tower_id: str
    canonical: str
    tower_canonical: str
    game_version: str
    cost: int | None
    cost_chimps: int | None
    xp: int | None
    base: dict[str, Any]
    source: str = ""
    description: str = ""
    abilities: tuple[ParagonAbility, ...] = ()

    @property
    def has_combat_stats(self) -> bool:
        return bool(self.base.get("attacks") or self.base.get("abilities"))

    @property
    def is_prose_sourced(self) -> bool:
        """True when the base was transcribed from article prose, not a module."""
        return "prose" in self.source.lower()

    def degree(self, degree: int) -> paragon_degrees.DegreeRow:
        """Degree-dependent stats (power, boss multiplier, scaled cells)."""
        return paragon_degrees.degree_row(self.base, degree)

    def degree_groups(self) -> tuple[str, ...]:
        """Column-group headers the degree table shows (degree-independent)."""
        return paragon_degrees.degree_stat_groups(self.base)


# ---------------------------------------------------------------------------
# Cached loader
# ---------------------------------------------------------------------------

_CACHE: dict[str, TowerStats | None] = {}
_HERO_CACHE: dict[str, HeroStats | None] = {}
_PARAGON_CACHE: dict[str, ParagonStats | None] = {}
_PARAGON_BY_TOWER: dict[str, str] | None = None


def _read_blob(relpath: str) -> dict | None:
    """Read one stats blob through the active BTD6 data backend.

    Routes the per-entity stats reads through the same provider as the
    fixtures (``btd6_data_service``), so the stats tree honours
    ``BTD6_DATA_BACKEND`` (file / postgres / cloud) too. Lazy import keeps the
    module load order independent.
    """
    from services import btd6_data_service

    return btd6_data_service.read_blob(relpath)


def _load(tower_id: str) -> TowerStats | None:
    data = _read_blob(f"stats/{tower_id}.json")
    if data is None:
        return None
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
    data = _read_blob(f"stats/heroes/{hero_id}.json")
    if data is None:
        return None
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


# Paragon overviews + ability prose live in their own committed blobs
# (paragon_descriptions.json / paragon_abilities.json) so a stats re-fetch
# never clobbers them; read through the provider via ``_read_blob``.
_PARAGON_DESCRIPTIONS: dict[str, str] | None = None
_PARAGON_ABILITIES: dict[str, tuple[ParagonAbility, ...]] | None = None


def _descriptions() -> dict[str, str]:
    """Curated, original-voice paragon overviews (paraphrased; cached).

    Kept in a separate committed file so a stats re-fetch never clobbers them.
    """
    global _PARAGON_DESCRIPTIONS
    if _PARAGON_DESCRIPTIONS is None:
        data = _read_blob("paragon_descriptions.json")
        _PARAGON_DESCRIPTIONS = dict(data.get("descriptions", {})) if data else {}
    return _PARAGON_DESCRIPTIONS


def _abilities() -> dict[str, tuple[ParagonAbility, ...]]:
    """Curated paragon ability names + explanations (paraphrased; cached).

    Like the overviews, kept in a separate committed file (the fetched stats
    module carries cooldowns but no prose, and a few abilities are unnamed
    there) so a stats re-fetch never clobbers it.
    """
    global _PARAGON_ABILITIES
    if _PARAGON_ABILITIES is None:
        index: dict[str, tuple[ParagonAbility, ...]] = {}
        data = _read_blob("paragon_abilities.json")
        for paragon_id, rows in ((data or {}).get("abilities") or {}).items():
            index[paragon_id] = tuple(
                ParagonAbility(
                    name=str(row.get("name", "")),
                    kind=str(row.get("kind", "activated")),
                    cooldown=row.get("cooldown"),
                    description=str(row.get("description", "")),
                )
                for row in rows
                if row.get("name")
            )
        _PARAGON_ABILITIES = index
    return _PARAGON_ABILITIES


def _load_paragon(paragon_id: str) -> ParagonStats | None:
    data = _read_blob(f"stats/paragons/{paragon_id}.json")
    if data is None:
        return None
    return ParagonStats(
        paragon_id=data.get("paragon_id", paragon_id),
        tower_id=data.get("tower_id", ""),
        canonical=data.get("canonical", ""),
        tower_canonical=data.get("tower_canonical", ""),
        game_version=str(data.get("game_version", "")),
        cost=data.get("cost"),
        cost_chimps=data.get("cost_chimps"),
        xp=data.get("xp"),
        base=data.get("base", {}),
        source=str(data.get("source", "")),
        description=_descriptions().get(data.get("paragon_id", paragon_id), ""),
        abilities=_abilities().get(data.get("paragon_id", paragon_id), ()),
    )


def get_paragon_stats(paragon_id: str) -> ParagonStats | None:
    """Return a paragon's stats by paragon id, or ``None`` if none exists."""
    if paragon_id not in _PARAGON_CACHE:
        _PARAGON_CACHE[paragon_id] = _load_paragon(paragon_id)
    return _PARAGON_CACHE[paragon_id]


_PARAGON_PREFIX = "stats/paragons/"
_JSON_SUFFIX = ".json"


def list_paragon_ids() -> tuple[str, ...]:
    """All paragon ids that have a stats blob in the active backend (sorted)."""
    from services import btd6_data_service

    names = btd6_data_service.list_blob_names(_PARAGON_PREFIX)
    ids = [
        name[len(_PARAGON_PREFIX) : -len(_JSON_SUFFIX)]
        for name in names
        if name.endswith(_JSON_SUFFIX)
    ]
    return tuple(sorted(ids))


def _paragon_index() -> dict[str, str]:
    """``tower_id -> paragon_id`` for every paragon with a stats file (cached)."""
    global _PARAGON_BY_TOWER
    if _PARAGON_BY_TOWER is None:
        index: dict[str, str] = {}
        for paragon_id in list_paragon_ids():
            stats = get_paragon_stats(paragon_id)
            if stats is not None and stats.tower_id:
                index[stats.tower_id] = paragon_id
        _PARAGON_BY_TOWER = index
    return _PARAGON_BY_TOWER


def get_paragon_stats_by_tower(tower_id: str) -> ParagonStats | None:
    """Return the paragon stats for ``tower_id`` (the tower's tier-6 paragon)."""
    paragon_id = _paragon_index().get(tower_id)
    return get_paragon_stats(paragon_id) if paragon_id else None


@dataclass(frozen=True)
class DegreeAttack:
    """One attack's per-projectile stats at a degree (the authoritative data)."""

    name: str
    cooldown: float
    projectiles: tuple[tuple[str, float, float], ...]  # (name, damage, pierce)


@dataclass(frozen=True)
class ParagonDegreeStats:
    """A paragon's exact per-attack stats at one degree.

    ``attacks`` is the authoritative breakdown (every attack, every projectile,
    scaled by the wiki's non-linear degree formulas). ``rough_dps`` is a single
    headline ESTIMATE only — it sums all projectile damage / cooldown across
    every attack, which ignores targeting, pierce, AoE, and uptime, so it is not
    a precise figure; quote the breakdown for anything exact.
    """

    paragon_id: str
    canonical: str
    tower_canonical: str
    degree: int
    attacks: tuple[DegreeAttack, ...]
    rough_dps: float
    boss_multiplier: float
    power: int


def attack_breakdown(
    attacks: list,
    degree: int | None = None,
) -> tuple[DegreeAttack, ...]:
    """Per-attack, per-projectile stats — scaled by ``degree`` for paragons.

    Without ``degree`` the base values are used (towers). Each projectile keeps
    its own name / damage / pierce; nothing is collapsed, so callers see the real
    components (e.g. a bomb's direct hit AND its explosion) instead of one number.
    """
    out: list[DegreeAttack] = []
    for attack in attacks or []:
        rate = attack.get("rate")
        if not isinstance(rate, (int, float)) or rate <= 0:
            continue
        cooldown = (
            paragon_degrees.scale_cooldown(float(rate), degree)
            if degree is not None
            else float(rate)
        )
        projectiles: list[tuple[str, float, float]] = []
        for proj in attack.get("projectiles") or []:
            damage = proj.get("damage")
            if not isinstance(damage, (int, float)) or damage <= 0:
                continue
            pierce = proj.get("pierce")
            pierce_val = float(pierce) if isinstance(pierce, (int, float)) else 0.0
            if degree is not None:
                damage = paragon_degrees.scale_damage(float(damage), degree)
                pierce_val = paragon_degrees.scale_pierce(pierce_val, degree)
            projectiles.append(
                (
                    str(proj.get("name") or "Projectile"),
                    round(float(damage), 1),
                    round(pierce_val, 1),
                ),
            )
        if projectiles:
            out.append(
                DegreeAttack(
                    name=str(attack.get("name") or "Attack"),
                    cooldown=round(cooldown, 4),
                    projectiles=tuple(projectiles),
                ),
            )
    return tuple(out)


def rough_attack_dps(attacks: list, degree: int | None = None) -> float | None:
    """Rough total DPS ESTIMATE — sum of all projectile damage / cooldown.

    Deliberately approximate (ignores targeting / pierce / AoE / uptime); use it
    only as a labelled estimate, never as an authoritative number. None if no
    damaging attack.
    """
    breakdown = attack_breakdown(attacks, degree)
    if not breakdown:
        return None
    total = sum(
        sum(p[1] for p in atk.projectiles) / atk.cooldown
        for atk in breakdown
        if atk.cooldown
    )
    return round(total, 1)


def main_projectile_stats(
    attacks: list,
    degree: int | None = None,
) -> tuple[float, float] | None:
    """``(damage, pierce)`` of the first attack's highest-damage projectile."""
    breakdown = attack_breakdown(attacks, degree)
    if not breakdown:
        return None
    top = max(breakdown[0].projectiles, key=lambda p: p[1], default=None)
    return (top[1], top[2]) if top is not None else None


def paragon_stats_at_degree(paragon_id: str, degree: int) -> ParagonDegreeStats | None:
    """Exact per-attack stats for a paragon at ``degree`` (1-100).

    Applies the wiki's non-linear degree formulas (:mod:`utils.btd6.paragon_degrees`)
    rather than interpolating: cooldown is a square-root curve, damage/pierce rise
    ~1%/degree then jump to ~2x base at degree 100. The per-attack breakdown is
    exact; ``rough_dps`` is an estimate only. None if no computable attack.
    """
    pstats = get_paragon_stats(paragon_id)
    if pstats is None:
        return None
    deg = max(1, min(paragon_degrees.MAX_DEGREE, int(degree)))
    attacks = pstats.base.get("attacks") or []
    breakdown = attack_breakdown(attacks, deg)
    if not breakdown:
        return None
    return ParagonDegreeStats(
        paragon_id=pstats.paragon_id,
        canonical=pstats.canonical,
        tower_canonical=pstats.tower_canonical,
        degree=deg,
        attacks=breakdown,
        rough_dps=rough_attack_dps(attacks, deg) or 0.0,
        boss_multiplier=paragon_degrees.boss_multiplier(deg),
        power=paragon_degrees.power_for_degree(deg),
    )


def resolve_paragon(query: str) -> str | None:
    """Resolve free-form ``query`` (a paragon name, or its tower) to a paragon id."""
    text = (query or "").lower()
    if not text.strip():
        return None
    for paragon_id in list_paragon_ids():
        pstats = get_paragon_stats(paragon_id)
        if pstats and pstats.canonical and pstats.canonical.lower() in text:
            return paragon_id
    # Fall back to tower resolution ('ace', 'Monkey Ace', aliases) -> its paragon.
    from services import btd6_resolver_service

    intent = btd6_resolver_service.resolve(query)
    for tower in getattr(intent, "towers", ()) or ():
        paragon_id = _paragon_index().get(getattr(tower, "id", ""))
        if paragon_id:
            return paragon_id
    return None


def reset_cache() -> None:
    """Test seam: drop the loaded-stats caches."""
    global _PARAGON_BY_TOWER, _PARAGON_DESCRIPTIONS, _PARAGON_ABILITIES
    _CACHE.clear()
    _HERO_CACHE.clear()
    _PARAGON_CACHE.clear()
    _PARAGON_BY_TOWER = None
    _PARAGON_DESCRIPTIONS = None
    _PARAGON_ABILITIES = None


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


# Prince of Darkness fires projectiles literally named "MOAB" / "BFB" — popped
# blimps reanimated as allies, and the only bloon-class-named projectiles in the
# dataset. Their stored "damage" is the reanimated minion's, not the tower's own
# hit, so counting BFB's 100 as Prince of Darkness's headline damage misleads.
# The headline skips them; the full reanimation breakdown lives in
# btd6_upgrade_detail_service. (Druid's 9,999,999 Vine sentinel is intentional —
# it renders as "∞" for the instant-kill — and is deliberately left untouched.)
_REANIMATED_MINION_NAMES = frozenset({"moab", "bfb", "zomg", "ddt", "bad"})


def _is_own_attack_damage(proj: dict[str, Any]) -> bool:
    """False for reanimated MOAB-class minions (Prince of Darkness only)."""
    return str(proj.get("name", "")).lower() not in _REANIMATED_MINION_NAMES


def _main_projectile(tier: dict[str, Any]) -> dict[str, Any] | None:
    """The highest-damage projectile representing the tower's own attack.

    Skips reanimated MOAB-class minions (see :data:`_REANIMATED_MINION_NAMES`)
    so a reanimated blimp's damage can't masquerade as the tower's headline hit.
    """
    best: dict[str, Any] | None = None
    for attack in tier.get("attacks", []):
        for proj in attack.get("projectiles", []):
            if not _is_own_attack_damage(proj):
                continue
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
    "DegreeAttack",
    "HeroStats",
    "NormalStats",
    "ParagonAbility",
    "ParagonDegreeStats",
    "ParagonStats",
    "TowerStats",
    "attack_breakdown",
    "get_hero_stats",
    "get_paragon_stats",
    "get_paragon_stats_by_tower",
    "get_tower_stats",
    "list_paragon_ids",
    "main_projectile_stats",
    "normal_stats",
    "paragon_stats_at_degree",
    "reset_cache",
    "resolve_paragon",
    "rough_attack_dps",
]
