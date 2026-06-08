"""BTD6 deterministic data loader and query API.

Loads representative game-data fixtures from ``disbot/data/btd6/``
and exposes typed read accessors. The service is the source of
truth for every deterministic BTD6 fact (towers, heroes, maps,
modes, rounds). Higher layers (resolver, knowledge, response
builder) consume this module — they do not parse JSON themselves.

Boundary: loading is synchronous, lazy, and cached. The first call
to any accessor runs validation; subsequent calls return cached
results. Tests can call :func:`reset_cache` to force a reload.

Validation guarantees:

* Each fixture carries ``data_version``, ``game_version``, ``source``.
* Canonical names are unique within a category.
* Alias lists are deduplicated; no alias collides with another
  canonical name OR another alias within the same category.
* Required fields per entry kind are present (see ``_VALIDATORS``).
* Cross-category alias collisions raise ``BTD6DataValidationError``
  with the colliding entries listed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from services.btd6_data_provider import (
    DATA_ROOT,
    BTD6RawProvider,
    CloudRawProvider,
    FileRawProvider,
    PostgresRawProvider,
)


class BTD6DataValidationError(ValueError):
    """Raised when a fixture file fails validation."""


# ---------------------------------------------------------------------------
# Typed view of one fixture entry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TowerEntry:
    id: str
    canonical: str
    aliases: tuple[str, ...]
    category: str
    base_cost: int
    description: str
    upgrade_paths: dict[str, tuple[str, ...]]
    wiki_url: str
    # Per-upgrade costs (medium difficulty); 0 means not yet populated.
    # Parallel structure to upgrade_paths: same keys, same length tuples.
    upgrade_costs: dict[str, tuple[int, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class HeroAbility:
    level: int
    name: str
    summary: str


@dataclass(frozen=True)
class HeroEntry:
    id: str
    canonical: str
    aliases: tuple[str, ...]
    base_cost: int
    description: str
    abilities: tuple[HeroAbility, ...]
    wiki_url: str


@dataclass(frozen=True)
class MapEntry:
    id: str
    canonical: str
    aliases: tuple[str, ...]
    difficulty: str
    description: str
    lines_of_sight_notes: str
    # Whether the map has water tiles (naval-tower placement) — from game data.
    has_water: bool = False
    # Per-map removable obstacles (bloonswiki-curated prose). NOT in the dump —
    # a blank "" means "no data on this map", never "this map has none".
    removables: str = ""
    # Attribution only; never surfaced. Blank rather than the deprecated
    # Fandom pages — populate from bloonswiki if a verified link is wanted.
    wiki_url: str = ""


@dataclass(frozen=True)
class ModeEntry:
    id: str
    canonical: str
    aliases: tuple[str, ...]
    description: str
    restrictions: tuple[str, ...]
    # None for modifiers (relative effect, no fixed value); set for
    # difficulties and modes.
    starting_cash: int | None = None
    starting_lives: int | None = None
    # BTD6 separates *difficulty* (Easy/Medium/Hard — sets lives/speed/prices),
    # *mode* (Standard + the rule variants), and *modifier* (Double Cash, Fast
    # Track — opt-in cash/round changes). ``kind`` tags which this row is.
    kind: str = "mode"
    # For a mode: which difficulties it is offered in (Standard/Sandbox span all,
    # the specials are single-difficulty). Empty for difficulties/modifiers.
    difficulties: tuple[str, ...] = ()
    # Structured, game-sourced rule values parsed from the dump's Mods/<mode>.json
    # (cash/lives/round bounds, cost/speed/income multipliers, restriction flags).
    # Grounds the prose ``restrictions``; empty for Standard + modifiers (no Mods
    # file) and unmapped rows. See ``modes.json:mode_rules_source``.
    rules: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RoundEntry:
    round_number: int
    summary: str
    danger: str
    common_threats: tuple[str, ...]
    # Extended composition (Module:BTD6_rounds): total RBE (children-inclusive),
    # the ordered spawn groups ({bloon_id, count, start, duration, modifiers}),
    # and which round set this is ("default"; ABR is a later addition).
    rbe: int | None = None
    # Standard/Medium per-round cash (pop cash + end-of-round bonus) and the
    # running total. Float because income decay (rounds 51+) yields fractional
    # values. Derived from this round's composition for all 140 rounds and pinned
    # to it by tests/unit/services/test_btd6_round_cash.py. See
    # ``rounds.json:cash_source``.
    cash: float | None = None
    cumulative_cash: float | None = None
    roundset: str = "default"
    groups: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class BloonEntry:
    id: str
    canonical: str
    aliases: tuple[str, ...]
    category: str
    description: str
    # Optional grounding extras. ``immune_to`` lists damage-type names
    # (matching utils.btd6.damage_types) the bloon resists; ``properties``
    # lists trait tags (camo / lead / fortified / moab-class / …).
    properties: tuple[str, ...] = ()
    immune_to: tuple[str, ...] = ()
    popped_by: str = ""
    children: str = ""
    health: int | None = None
    # Extended bloonswiki facts (btd6_bloons Cargo): RBE (children-inclusive),
    # fortified variants, speed, layer count, and structured children
    # (bloon_id + count + modifiers — the canonical form; ``children`` is the
    # legacy display string). ``rbe`` is recomputed from health + children text
    # by tests/unit/services/test_btd6_rbe.py, so a typo in either field fails CI.
    rbe: int | None = None
    rbe_fortified: int | None = None
    health_fortified: int | None = None
    speed: float | None = None
    layers: int | None = None
    children_list: tuple[dict[str, Any], ...] = ()
    # Attribution only (bloonswiki); never surfaced in grounding. Left blank
    # rather than reusing the discredited bloons.fandom.com pages.
    wiki_url: str = ""


@dataclass(frozen=True)
class RelicEntry:
    """One Contested Territory relic and its effect.

    ``api_name`` is the exact CamelCase token Ninja Kiwi stores on a
    ``btd6_ct_tile`` fact (``relic_name``), so live tile rows can be
    mapped back to this catalog entry without guessing. ``abbrev`` is
    the optional community shorthand (e.g. ``SMS`` for Super Monkey
    Storm) surfaced alongside the canonical name in display.
    """

    id: str
    canonical: str
    api_name: str
    aliases: tuple[str, ...]
    category: str
    effect: str
    abbrev: str = ""


@dataclass(frozen=True)
class PowerEntry:
    """One consumable Power (Monkey Boost, Cash Drop, Road Spikes, …).

    Game-native: ``canonical``/``description`` are the game-authored strings,
    ``monkey_money_cost`` is the in-store MM price, ``quantity`` how many a
    single purchase grants, ``between_rounds`` whether it can be used between
    rounds. ``power_id`` is the dump's internal id.
    """

    id: str
    canonical: str
    power_id: str
    description: str
    monkey_money_cost: int
    quantity: int
    between_rounds: bool
    is_power_pro: bool = False
    # Structured headline effect factor(s) decoded from the dump (e.g. Monkey
    # Boost ``{"rate_scale": 0.5, "duration_seconds": 15}``). ``{}`` when the
    # power's effect isn't cleanly decodable. The foundation for a future
    # "apply this power to a tower stat" computation tool.
    effect: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MonkeyKnowledgeEntry:
    """One Monkey Knowledge point. ``category`` is the in-game tab
    (Primary/Military/Magic/Support/Heroes/Powers), ``investment_required`` the
    points that must already be spent in that tab to unlock it,
    ``monkey_money_cost`` its MM price, ``prerequisites`` the ids it requires.
    """

    id: str
    canonical: str
    category: str
    description: str
    monkey_money_cost: int
    investment_required: int
    prerequisites: tuple[str, ...] = ()
    # Structured, dump-native effect decoded from the knowledge's
    # ``mod.mutatorMods[]`` — ``{"factors": [{"kind": ..., <numbers>}, ...]}``
    # (More Cash ``starting_cash addition 200``, Bonus Monkey
    # ``free_tower base_tower_id DartMonkey``, …). ``{}`` for the purely
    # behavioural ones (nested projectile/ability sub-model — Cold Front, Tiny
    # Tornadoes, …) which stay description-only.
    effect: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GeraldoItemEntry:
    """One Geraldo shop item (Blade Trap, Genie Bottle, Paragon Power Totem, …).

    Game-native: ``canonical``/``description`` are the game-authored strings,
    ``cost`` the in-game cash price (not Monkey Money), ``unlock_level`` the
    Geraldo hero level it unlocks at, ``starting_quantity``/``max_quantity`` the
    stock a fresh Geraldo carries and can hold, and ``rounds_to_replenish`` /
    ``amount_to_replenish`` the restock cadence.
    """

    id: str
    canonical: str
    description: str
    cost: int
    unlock_level: int
    starting_quantity: int
    max_quantity: int
    rounds_to_replenish: int
    amount_to_replenish: int
    between_rounds: bool = False
    # Structured headline effect decoded from the item's behaviour model (e.g.
    # Sharpening Stone ``{"pierce_increase": 1, "rounds": 10}``). ``{}`` for items
    # whose effect is a spawned projectile / tower summon / non-numeric — those
    # stay description-only.
    effect: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BossEntry:
    """One Boss Bloon (Bloonarius, Lych, Vortex, Dreadbloon, Blastapopoulos,
    Phayze, Diamondback). Game-native: ``canonical`` and the mechanic
    ``description`` are the game-authored strings; ``immune_to`` is the derived
    damage-type immunity set (e.g. Dreadbloon = Lead, Blastapopoulos = Purple);
    ``tiers`` carries the five boss tiers' ``{tier, health, speed}`` (both scale
    up per tier — co-op multiplies health further at runtime). ``tagline`` is the
    flavour line shown on the boss-select panel.
    """

    id: str
    canonical: str
    description: str
    tiers: tuple[dict[str, Any], ...] = ()
    tagline: str = ""
    immune_to: tuple[str, ...] = ()


@dataclass(frozen=True)
class BTD6DataSet:
    data_version: str
    game_version: str
    sources: dict[str, str] = field(default_factory=dict)
    towers: tuple[TowerEntry, ...] = ()
    heroes: tuple[HeroEntry, ...] = ()
    maps: tuple[MapEntry, ...] = ()
    modes: tuple[ModeEntry, ...] = ()
    rounds: tuple[RoundEntry, ...] = ()
    bloons: tuple[BloonEntry, ...] = ()
    ct_relics: tuple[RelicEntry, ...] = ()
    powers: tuple[PowerEntry, ...] = ()
    monkey_knowledge: tuple[MonkeyKnowledgeEntry, ...] = ()
    geraldo_items: tuple[GeraldoItemEntry, ...] = ()
    bosses: tuple[BossEntry, ...] = ()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


_REQUIRED_TOP_LEVEL = ("data_version", "game_version", "source")
_REQUIRED_TOWER_FIELDS = (
    "id",
    "canonical",
    "aliases",
    "category",
    "base_cost",
    "description",
    "upgrade_paths",
    "wiki_url",
)
_TOWER_CATEGORIES = frozenset({"primary", "military", "magic", "support"})
_TOWER_UPGRADE_PATHS = ("top", "mid", "bot")
_TOWER_UPGRADE_TIERS_PER_PATH = 5
_REQUIRED_HERO_FIELDS = (
    "id",
    "canonical",
    "aliases",
    "base_cost",
    "description",
    "abilities",
    "wiki_url",
)
_REQUIRED_MAP_FIELDS = (
    "id",
    "canonical",
    "aliases",
    "difficulty",
    "description",
    "lines_of_sight_notes",
)
# starting_cash / starting_lives are optional: modifiers (Double Cash, Fast
# Track) have no fixed value — their effect is relative (×2 cash, start ¼ into
# the rounds), so those rows omit them.
_REQUIRED_MODE_FIELDS = (
    "id",
    "canonical",
    "aliases",
    "description",
    "restrictions",
)
_REQUIRED_ROUND_FIELDS = ("round", "summary", "danger", "common_threats")
_REQUIRED_HERO_ABILITY_FIELDS = ("level", "name", "summary")
_REQUIRED_BLOON_FIELDS = (
    "id",
    "canonical",
    "aliases",
    "category",
    "description",
)
_BLOON_CATEGORIES = frozenset({"basic", "special", "moab_class", "modifier"})
_REQUIRED_RELIC_FIELDS = (
    "id",
    "canonical",
    "api_name",
    "aliases",
    "category",
    "effect",
)
_RELIC_CATEGORIES = frozenset({"offense", "economy", "lives", "powerup", "utility"})
_REQUIRED_POWER_FIELDS = ("id", "canonical", "power_id", "monkey_money_cost")
_REQUIRED_KNOWLEDGE_FIELDS = (
    "id",
    "canonical",
    "category",
    "monkey_money_cost",
    "investment_required",
)
_MK_CATEGORIES = frozenset(
    {"Primary", "Military", "Magic", "Support", "Heroes", "Powers"},
)
_REQUIRED_GERALDO_FIELDS = ("id", "canonical", "cost", "unlock_level")
_REQUIRED_BOSS_FIELDS = ("id", "canonical")


def _require_keys(entry: dict[str, Any], keys: tuple[str, ...], where: str) -> None:
    missing = [k for k in keys if k not in entry]
    if missing:
        raise BTD6DataValidationError(
            f"{where}: missing required fields {missing!r}",
        )


def _check_unique(items: list, where: str) -> None:
    seen: set = set()
    dupes: set = set()
    for item in items:
        if item in seen:
            dupes.add(item)
        seen.add(item)
    if dupes:
        raise BTD6DataValidationError(
            f"{where}: duplicate values {sorted(dupes)!r}",
        )


# ---------------------------------------------------------------------------
# Parsers — one per fixture
# ---------------------------------------------------------------------------


def _normalise_alias(value: str) -> str:
    return value.strip().lower()


def _parse_tower(raw: dict[str, Any]) -> TowerEntry:
    _require_keys(raw, _REQUIRED_TOWER_FIELDS, where=f"tower {raw.get('id')!r}")
    category = str(raw["category"])
    if category not in _TOWER_CATEGORIES:
        raise BTD6DataValidationError(
            f"tower {raw['id']!r}: category {category!r} not one of "
            f"{sorted(_TOWER_CATEGORIES)}",
        )
    base_cost = int(raw["base_cost"])
    if base_cost <= 0:
        raise BTD6DataValidationError(
            f"tower {raw['id']!r}: base_cost must be > 0, got {base_cost}",
        )
    upgrade_paths_raw = raw["upgrade_paths"]
    if not isinstance(upgrade_paths_raw, dict):
        raise BTD6DataValidationError(
            f"tower {raw['id']!r}: upgrade_paths must be a dict",
        )
    missing_paths = [p for p in _TOWER_UPGRADE_PATHS if p not in upgrade_paths_raw]
    if missing_paths:
        raise BTD6DataValidationError(
            f"tower {raw['id']!r}: upgrade_paths missing keys {missing_paths!r}",
        )
    extra_paths = [p for p in upgrade_paths_raw if p not in _TOWER_UPGRADE_PATHS]
    if extra_paths:
        raise BTD6DataValidationError(
            f"tower {raw['id']!r}: upgrade_paths has unexpected keys "
            f"{extra_paths!r}; only {list(_TOWER_UPGRADE_PATHS)} allowed",
        )
    upgrade_paths: dict[str, tuple[str, ...]] = {}
    for path_key, tiers in upgrade_paths_raw.items():
        if not isinstance(tiers, list):
            raise BTD6DataValidationError(
                f"tower {raw['id']!r}: upgrade_paths.{path_key} must be a list",
            )
        if len(tiers) != _TOWER_UPGRADE_TIERS_PER_PATH:
            raise BTD6DataValidationError(
                f"tower {raw['id']!r}: upgrade_paths.{path_key} must have "
                f"exactly {_TOWER_UPGRADE_TIERS_PER_PATH} tiers, got {len(tiers)}",
            )
        tier_tuple: list[str] = []
        for index, tier in enumerate(tiers, start=1):
            tier_name = str(tier).strip()
            if not tier_name:
                raise BTD6DataValidationError(
                    f"tower {raw['id']!r}: upgrade_paths.{path_key} tier "
                    f"{index} is empty",
                )
            tier_tuple.append(tier_name)
        upgrade_paths[path_key] = tuple(tier_tuple)

    # upgrade_costs is optional; absent or all-zero means "not yet populated".
    upgrade_costs: dict[str, tuple[int, ...]] = {}
    costs_raw = raw.get("upgrade_costs")
    if isinstance(costs_raw, dict):
        for path_key in _TOWER_UPGRADE_PATHS:
            raw_list = costs_raw.get(path_key, [])
            if (
                isinstance(raw_list, list)
                and len(raw_list) == _TOWER_UPGRADE_TIERS_PER_PATH
            ):
                upgrade_costs[path_key] = tuple(int(c) for c in raw_list)

    aliases = tuple(_normalise_alias(a) for a in raw["aliases"])
    return TowerEntry(
        id=str(raw["id"]),
        canonical=str(raw["canonical"]),
        aliases=aliases,
        category=category,
        base_cost=base_cost,
        description=str(raw["description"]),
        upgrade_paths=upgrade_paths,
        upgrade_costs=upgrade_costs,
        wiki_url=str(raw["wiki_url"]),
    )


def _parse_hero(raw: dict[str, Any]) -> HeroEntry:
    _require_keys(raw, _REQUIRED_HERO_FIELDS, where=f"hero {raw.get('id')!r}")
    base_cost = int(raw["base_cost"])
    if base_cost <= 0:
        raise BTD6DataValidationError(
            f"hero {raw['id']!r}: base_cost must be > 0, got {base_cost}",
        )
    abilities_raw = raw["abilities"]
    if not isinstance(abilities_raw, list):
        raise BTD6DataValidationError(
            f"hero {raw['id']!r}: abilities must be a list",
        )
    abilities: list[HeroAbility] = []
    for ability in abilities_raw:
        _require_keys(
            ability,
            _REQUIRED_HERO_ABILITY_FIELDS,
            where=f"hero {raw['id']!r} ability",
        )
        abilities.append(
            HeroAbility(
                level=int(ability["level"]),
                name=str(ability["name"]),
                summary=str(ability["summary"]),
            ),
        )
    return HeroEntry(
        id=str(raw["id"]),
        canonical=str(raw["canonical"]),
        aliases=tuple(_normalise_alias(a) for a in raw["aliases"]),
        base_cost=base_cost,
        description=str(raw["description"]),
        abilities=tuple(abilities),
        wiki_url=str(raw["wiki_url"]),
    )


def _parse_map(raw: dict[str, Any]) -> MapEntry:
    _require_keys(raw, _REQUIRED_MAP_FIELDS, where=f"map {raw.get('id')!r}")
    return MapEntry(
        id=str(raw["id"]),
        canonical=str(raw["canonical"]),
        aliases=tuple(_normalise_alias(a) for a in raw["aliases"]),
        difficulty=str(raw["difficulty"]),
        description=str(raw["description"]),
        lines_of_sight_notes=str(raw["lines_of_sight_notes"]),
        has_water=bool(raw.get("has_water", False)),
        removables=str(raw.get("removables", "")),
        wiki_url=str(raw.get("wiki_url", "")),
    )


def _parse_mode(raw: dict[str, Any]) -> ModeEntry:
    _require_keys(raw, _REQUIRED_MODE_FIELDS, where=f"mode {raw.get('id')!r}")
    return ModeEntry(
        id=str(raw["id"]),
        canonical=str(raw["canonical"]),
        aliases=tuple(_normalise_alias(a) for a in raw["aliases"]),
        description=str(raw["description"]),
        restrictions=tuple(str(r) for r in raw["restrictions"]),
        kind=str(raw.get("kind", "mode")),
        difficulties=tuple(str(d) for d in raw.get("difficulties", [])),
        starting_cash=(
            int(raw["starting_cash"]) if raw.get("starting_cash") is not None else None
        ),
        starting_lives=(
            int(raw["starting_lives"])
            if raw.get("starting_lives") is not None
            else None
        ),
        rules=dict(raw.get("rules") or {}),
    )


def _parse_round(raw: dict[str, Any]) -> RoundEntry:
    _require_keys(raw, _REQUIRED_ROUND_FIELDS, where=f"round {raw.get('round')!r}")
    rbe_raw = raw.get("rbe")
    rbe = int(rbe_raw) if isinstance(rbe_raw, (int, float)) else None
    if rbe is not None and rbe < 0:
        raise BTD6DataValidationError(
            f"round {raw['round']!r}: rbe must be >= 0 when present, got {rbe}",
        )
    cash_raw = raw.get("cash")
    cash = float(cash_raw) if isinstance(cash_raw, (int, float)) else None
    cumul_raw = raw.get("cumulative_cash")
    cumulative_cash = float(cumul_raw) if isinstance(cumul_raw, (int, float)) else None
    groups = tuple(dict(g) for g in raw.get("groups", ()) if isinstance(g, dict))
    return RoundEntry(
        round_number=int(raw["round"]),
        summary=str(raw["summary"]),
        danger=str(raw["danger"]),
        common_threats=tuple(str(t) for t in raw["common_threats"]),
        rbe=rbe,
        cash=cash,
        cumulative_cash=cumulative_cash,
        roundset=str(raw.get("roundset", "default")),
        groups=groups,
    )


def _parse_bloon(raw: dict[str, Any]) -> BloonEntry:
    _require_keys(raw, _REQUIRED_BLOON_FIELDS, where=f"bloon {raw.get('id')!r}")
    category = str(raw["category"])
    if category not in _BLOON_CATEGORIES:
        raise BTD6DataValidationError(
            f"bloon {raw['id']!r}: category {category!r} not one of "
            f"{sorted(_BLOON_CATEGORIES)}",
        )

    def _opt_pos_int(key: str) -> int | None:
        value = raw.get(key)
        if not isinstance(value, (int, float)):
            return None
        as_int = int(value)
        if as_int <= 0:
            raise BTD6DataValidationError(
                f"bloon {raw['id']!r}: {key} must be > 0 when present, got {as_int}",
            )
        return as_int

    health = _opt_pos_int("health")
    rbe = _opt_pos_int("rbe")
    rbe_fortified = _opt_pos_int("rbe_fortified")
    health_fortified = _opt_pos_int("health_fortified")
    layers = _opt_pos_int("layers")
    speed_raw = raw.get("speed")
    speed = float(speed_raw) if isinstance(speed_raw, (int, float)) else None
    if speed is not None and speed <= 0:
        raise BTD6DataValidationError(
            f"bloon {raw['id']!r}: speed must be > 0 when present, got {speed}",
        )
    children_list = tuple(
        dict(c) for c in raw.get("children_list", ()) if isinstance(c, dict)
    )
    return BloonEntry(
        id=str(raw["id"]),
        canonical=str(raw["canonical"]),
        aliases=tuple(_normalise_alias(a) for a in raw["aliases"]),
        category=category,
        description=str(raw["description"]),
        wiki_url=str(raw.get("wiki_url", "")),
        properties=tuple(str(p) for p in raw.get("properties", ())),
        immune_to=tuple(str(d) for d in raw.get("immune_to", ())),
        popped_by=str(raw.get("popped_by", "")),
        children=str(raw.get("children", "")),
        health=health,
        rbe=rbe,
        rbe_fortified=rbe_fortified,
        health_fortified=health_fortified,
        speed=speed,
        layers=layers,
        children_list=children_list,
    )


def _parse_relic(raw: dict[str, Any]) -> RelicEntry:
    _require_keys(raw, _REQUIRED_RELIC_FIELDS, where=f"relic {raw.get('id')!r}")
    category = str(raw["category"])
    if category not in _RELIC_CATEGORIES:
        raise BTD6DataValidationError(
            f"relic {raw['id']!r}: category {category!r} not one of "
            f"{sorted(_RELIC_CATEGORIES)}",
        )
    effect = str(raw["effect"]).strip()
    if not effect:
        raise BTD6DataValidationError(
            f"relic {raw['id']!r}: effect must be a non-empty string",
        )
    api_name = str(raw["api_name"]).strip()
    if not api_name:
        raise BTD6DataValidationError(
            f"relic {raw['id']!r}: api_name must be a non-empty string",
        )
    return RelicEntry(
        id=str(raw["id"]),
        canonical=str(raw["canonical"]),
        api_name=api_name,
        aliases=tuple(_normalise_alias(a) for a in raw["aliases"]),
        category=category,
        effect=effect,
        abbrev=str(raw.get("abbrev", "")),
    )


def _parse_power(raw: dict[str, Any]) -> PowerEntry:
    _require_keys(raw, _REQUIRED_POWER_FIELDS, where=f"power {raw.get('id')!r}")
    effect = raw.get("effect", {})
    return PowerEntry(
        id=str(raw["id"]),
        canonical=str(raw["canonical"]),
        power_id=str(raw["power_id"]),
        description=str(raw.get("description", "")).strip(),
        monkey_money_cost=int(raw["monkey_money_cost"]),
        quantity=int(raw.get("quantity", 1)),
        between_rounds=bool(raw.get("between_rounds", False)),
        is_power_pro=bool(raw.get("is_power_pro", False)),
        effect=dict(effect) if isinstance(effect, dict) else {},
    )


def _parse_knowledge(raw: dict[str, Any]) -> MonkeyKnowledgeEntry:
    _require_keys(
        raw,
        _REQUIRED_KNOWLEDGE_FIELDS,
        where=f"knowledge {raw.get('id')!r}",
    )
    category = str(raw["category"])
    if category not in _MK_CATEGORIES:
        raise BTD6DataValidationError(
            f"knowledge {raw['id']!r}: category {category!r} not one of "
            f"{sorted(_MK_CATEGORIES)}",
        )
    effect = raw.get("effect", {})
    return MonkeyKnowledgeEntry(
        id=str(raw["id"]),
        canonical=str(raw["canonical"]),
        category=category,
        description=str(raw.get("description", "")).strip(),
        monkey_money_cost=int(raw["monkey_money_cost"]),
        investment_required=int(raw["investment_required"]),
        prerequisites=tuple(str(p) for p in raw.get("prerequisites", []) or ()),
        effect=dict(effect) if isinstance(effect, dict) else {},
    )


def _parse_boss(raw: dict[str, Any]) -> BossEntry:
    _require_keys(raw, _REQUIRED_BOSS_FIELDS, where=f"boss {raw.get('id')!r}")
    tiers = tuple(
        {
            "tier": int(t["tier"]),
            "health": int(t["health"]),
            "speed": float(t["speed"]),
        }
        for t in raw.get("tiers", []) or ()
        if "tier" in t and "health" in t
    )
    return BossEntry(
        id=str(raw["id"]),
        canonical=str(raw["canonical"]),
        description=str(raw.get("description", "")).strip(),
        tiers=tiers,
        tagline=str(raw.get("tagline", "")).strip(),
        immune_to=tuple(str(x) for x in raw.get("immune_to", []) or ()),
    )


def _parse_geraldo_item(raw: dict[str, Any]) -> GeraldoItemEntry:
    _require_keys(raw, _REQUIRED_GERALDO_FIELDS, where=f"geraldo {raw.get('id')!r}")
    effect = raw.get("effect", {})
    return GeraldoItemEntry(
        id=str(raw["id"]),
        canonical=str(raw["canonical"]),
        description=str(raw.get("description", "")).strip(),
        cost=int(raw["cost"]),
        unlock_level=int(raw["unlock_level"]),
        starting_quantity=int(raw.get("starting_quantity", 0)),
        max_quantity=int(raw.get("max_quantity", 0)),
        rounds_to_replenish=int(raw.get("rounds_to_replenish", 0)),
        amount_to_replenish=int(raw.get("amount_to_replenish", 0)),
        between_rounds=bool(raw.get("between_rounds", False)),
        effect=dict(effect) if isinstance(effect, dict) else {},
    )


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


# Raw-bytes seam: the dataset's validation + caching layer reads fixtures
# through a swappable provider. Defaults to the committed local files; setting
# ``BTD6_DATA_BASE_URL`` swaps in the network-backed CloudRawProvider (warmed
# at startup) with no change to the dataset consumers.
_REQUIRED_FIXTURES = (
    "towers.json",
    "heroes.json",
    "maps.json",
    "modes.json",
    "rounds.json",
)
_OPTIONAL_FIXTURES = (
    "bloons.json",
    "ct_relics.json",
    "powers.json",
    "monkey_knowledge.json",
    "geraldo_items.json",
    "bosses.json",
)


def _default_cache_dir() -> Path:
    import tempfile

    return Path(tempfile.gettempdir()) / "superbot_btd6_data"


def _select_provider() -> BTD6RawProvider:
    """Pick the raw-fixture backend from config (no network/DB I/O at import).

    ``BTD6_DATA_BACKEND`` selects explicitly:

    * ``postgres`` → :class:`PostgresRawProvider` (the ``btd6_data_blobs``
      table; recommended for a deployment that already runs Postgres);
    * ``cloud`` → :class:`CloudRawProvider` (a public-read object store at
      ``BTD6_DATA_BASE_URL``);
    * ``file`` / unset → the committed local files via ``FileRawProvider``.

    Back-compat: ``BTD6_DATA_BASE_URL`` set with no explicit backend still
    implies ``cloud``. Provider *selection* is cheap; the actual fetch happens
    later in :func:`warm_provider`, so import stays side-effect-free.
    """
    try:
        from config import (
            BTD6_DATA_BACKEND,
            BTD6_DATA_BASE_URL,
            BTD6_DATA_CACHE_DIR,
        )
    except Exception:  # noqa: BLE001 - config always importable in the app
        return FileRawProvider()
    backend = (BTD6_DATA_BACKEND or "").strip().lower()
    base_url = (BTD6_DATA_BASE_URL or "").strip()

    if backend == "postgres":
        return PostgresRawProvider()
    if backend == "cloud" or (not backend and base_url):
        if base_url:
            cache_dir = (BTD6_DATA_CACHE_DIR or "").strip() or _default_cache_dir()
            return CloudRawProvider(base_url, cache_dir)
    return FileRawProvider()


_PROVIDER: BTD6RawProvider = _select_provider()


def set_provider(provider: BTD6RawProvider) -> None:
    """Swap the raw-fixture provider (cloud migration + test seam).

    Callers that change the provider should also call :func:`reset_cache`
    so the next :func:`get_dataset` reloads through the new backend.
    """
    global _PROVIDER
    _PROVIDER = provider


def get_provider() -> BTD6RawProvider:
    """Return the active raw-fixture provider."""
    return _PROVIDER


def read_blob(name: str) -> dict[str, Any] | None:
    """Read one raw blob through the active provider, or ``None`` if absent.

    ``name`` is relative to the BTD6 data root (e.g. ``"stats/dart_monkey.json"``
    or ``"paragon_abilities.json"``). Lets ``btd6_stats_service`` read the
    per-entity stats tree through the same backend as the fixtures so it honours
    ``BTD6_DATA_BACKEND`` too.
    """
    return _PROVIDER.load(name)


def list_blob_names(prefix: str = "") -> tuple[str, ...]:
    """Available blob names under ``prefix`` (the provider-aware glob seam)."""
    lister = getattr(_PROVIDER, "list_names", None)
    return lister(prefix) if lister is not None else ()


async def warm_provider() -> bool:
    """Populate the active provider's cache if it supports warming (cloud).

    Returns ``True`` when the required fixtures are available (always ``True``
    for the local file provider). Safe no-op when ``BTD6_DATA_BASE_URL`` is
    unset. Drops the dataset cache so the next :func:`get_dataset` reads the
    freshly warmed copy.
    """
    warm = getattr(_PROVIDER, "warm_cache", None)
    if warm is None:
        return True
    ok = await warm(required=_REQUIRED_FIXTURES, optional=_OPTIONAL_FIXTURES)
    reset_cache()
    return bool(ok)


def data_available() -> bool:
    """Whether BTD6 deterministic data can be loaded right now.

    The file provider is always available (the fixtures ship in the repo); the
    cloud provider reports availability after :func:`warm_provider` runs.
    """
    is_available = getattr(_PROVIDER, "is_available", None)
    return is_available() if is_available is not None else True


def data_source_label() -> str:
    """Human-readable description of the active data source (for status)."""
    label = getattr(_PROVIDER, "source_label", None)
    if label is not None:
        return label()
    return f"local:{DATA_ROOT}"


async def seed_postgres_from_files(root: Path | None = None) -> int:
    """Upsert every bundled BTD6 data file into ``btd6_data_blobs`` (idempotent).

    Reads the committed files via a ``FileRawProvider`` (independent of whichever
    backend is *active*) and writes each through ``utils.db.btd6_data``. Returns
    the number of blobs seeded. Requires the DB pool to be initialised — it is,
    once the bot is running, so this powers the ``!btd6ops seed-data`` command as
    well as ``scripts/seed_btd6_data.py``.
    """
    import hashlib
    import json

    from utils.db import btd6_data

    src = FileRawProvider(root) if root is not None else FileRawProvider()
    seeded = 0
    for name in src.list_names():
        if name == "manifest.json":  # bucket artifact, not a fixture
            continue
        body = src.load(name)
        if body is None:
            continue
        sha = hashlib.sha256(
            json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8"),
        ).hexdigest()
        await btd6_data.upsert_blob(name, body, sha)
        seeded += 1
    return seeded


def _load_file(name: str) -> dict[str, Any]:
    raw = _PROVIDER.load(name)
    if raw is None:
        raise BTD6DataValidationError(
            f"missing fixture file: {DATA_ROOT / name}",
        )
    _require_keys(raw, _REQUIRED_TOP_LEVEL, where=str(DATA_ROOT / name))
    return raw


def _load_file_optional(name: str) -> dict[str, Any] | None:
    """Like :func:`_load_file` but returns ``None`` when the file is absent.

    Used for fixtures that were added after the original five (towers /
    heroes / maps / modes / rounds). A missing optional fixture degrades to
    an empty category instead of aborting the whole dataset load — and keeps
    the staged-fixture tests, which copy only the original five, green.
    """
    raw = _PROVIDER.load(name)
    if raw is None:
        return None
    _require_keys(raw, _REQUIRED_TOP_LEVEL, where=str(DATA_ROOT / name))
    return raw


def _load_dataset() -> BTD6DataSet:
    towers_raw = _load_file("towers.json")
    heroes_raw = _load_file("heroes.json")
    maps_raw = _load_file("maps.json")
    modes_raw = _load_file("modes.json")
    rounds_raw = _load_file("rounds.json")

    # bloons.json is an optional fixture (added after the original five);
    # absent → empty category, so older staged-fixture sets still load.
    bloons_raw = _load_file_optional("bloons.json")
    # ct_relics.json is likewise optional (added in the CT feature); a missing
    # file degrades to an empty catalog rather than aborting the dataset.
    ct_relics_raw = _load_file_optional("ct_relics.json")
    # powers.json / monkey_knowledge.json are game-native optional fixtures.
    powers_raw = _load_file_optional("powers.json")
    knowledge_raw = _load_file_optional("monkey_knowledge.json")
    geraldo_raw = _load_file_optional("geraldo_items.json")
    bosses_raw = _load_file_optional("bosses.json")

    towers = tuple(_parse_tower(t) for t in towers_raw.get("towers", []))
    heroes = tuple(_parse_hero(h) for h in heroes_raw.get("heroes", []))
    maps = tuple(_parse_map(m) for m in maps_raw.get("maps", []))
    modes = tuple(_parse_mode(m) for m in modes_raw.get("modes", []))
    rounds = tuple(_parse_round(r) for r in rounds_raw.get("rounds", []))
    bloons = (
        tuple(_parse_bloon(b) for b in bloons_raw.get("bloons", []))
        if bloons_raw is not None
        else ()
    )
    ct_relics = (
        tuple(_parse_relic(r) for r in ct_relics_raw.get("relics", []))
        if ct_relics_raw is not None
        else ()
    )
    powers = (
        tuple(_parse_power(p) for p in powers_raw.get("powers", []))
        if powers_raw is not None
        else ()
    )
    monkey_knowledge = (
        tuple(_parse_knowledge(k) for k in knowledge_raw.get("knowledge", []))
        if knowledge_raw is not None
        else ()
    )
    geraldo_items = (
        tuple(_parse_geraldo_item(g) for g in geraldo_raw.get("geraldo_items", []))
        if geraldo_raw is not None
        else ()
    )
    bosses = (
        tuple(_parse_boss(b) for b in bosses_raw.get("bosses", []))
        if bosses_raw is not None
        else ()
    )

    # Per-category canonical uniqueness.
    _check_unique([t.id for t in towers], where="towers.id")
    _check_unique([t.canonical for t in towers], where="towers.canonical")
    _check_unique([h.id for h in heroes], where="heroes.id")
    _check_unique([h.canonical for h in heroes], where="heroes.canonical")
    _check_unique([m.id for m in maps], where="maps.id")
    _check_unique([m.canonical for m in maps], where="maps.canonical")
    _check_unique([m.id for m in modes], where="modes.id")
    _check_unique([m.canonical for m in modes], where="modes.canonical")
    _check_unique([r.round_number for r in rounds], where="rounds.round")
    _check_unique([b.id for b in bloons], where="bloons.id")
    _check_unique([b.canonical for b in bloons], where="bloons.canonical")
    _check_unique([r.id for r in ct_relics], where="ct_relics.id")
    _check_unique([r.canonical for r in ct_relics], where="ct_relics.canonical")
    _check_unique([r.api_name for r in ct_relics], where="ct_relics.api_name")
    _check_unique([p.id for p in powers], where="powers.id")
    _check_unique([p.canonical for p in powers], where="powers.canonical")
    _check_unique([k.id for k in monkey_knowledge], where="monkey_knowledge.id")
    _check_unique(
        [k.canonical for k in monkey_knowledge],
        where="monkey_knowledge.canonical",
    )
    _check_unique([g.id for g in geraldo_items], where="geraldo_items.id")
    _check_unique([g.canonical for g in geraldo_items], where="geraldo_items.canonical")
    _check_unique([b.id for b in bosses], where="bosses.id")
    _check_unique([b.canonical for b in bosses], where="bosses.canonical")

    # Alias collision check across every category — the resolver depends
    # on aliases being globally unique.
    alias_owners: dict[str, str] = {}
    for tower in towers:
        for alias in (*tower.aliases, _normalise_alias(tower.canonical)):
            owner = f"tower:{tower.id}"
            if alias in alias_owners and alias_owners[alias] != owner:
                raise BTD6DataValidationError(
                    f"alias collision: {alias!r} owned by both "
                    f"{alias_owners[alias]} and {owner}",
                )
            alias_owners[alias] = owner
    for hero in heroes:
        for alias in (*hero.aliases, _normalise_alias(hero.canonical)):
            owner = f"hero:{hero.id}"
            if alias in alias_owners and alias_owners[alias] != owner:
                raise BTD6DataValidationError(
                    f"alias collision: {alias!r} owned by both "
                    f"{alias_owners[alias]} and {owner}",
                )
            alias_owners[alias] = owner
    for game_map in maps:
        for alias in (*game_map.aliases, _normalise_alias(game_map.canonical)):
            owner = f"map:{game_map.id}"
            if alias in alias_owners and alias_owners[alias] != owner:
                raise BTD6DataValidationError(
                    f"alias collision: {alias!r} owned by both "
                    f"{alias_owners[alias]} and {owner}",
                )
            alias_owners[alias] = owner
    for mode in modes:
        for alias in (*mode.aliases, _normalise_alias(mode.canonical)):
            owner = f"mode:{mode.id}"
            if alias in alias_owners and alias_owners[alias] != owner:
                raise BTD6DataValidationError(
                    f"alias collision: {alias!r} owned by both "
                    f"{alias_owners[alias]} and {owner}",
                )
            alias_owners[alias] = owner
    for bloon in bloons:
        for alias in (*bloon.aliases, _normalise_alias(bloon.canonical)):
            owner = f"bloon:{bloon.id}"
            if alias in alias_owners and alias_owners[alias] != owner:
                raise BTD6DataValidationError(
                    f"alias collision: {alias!r} owned by both "
                    f"{alias_owners[alias]} and {owner}",
                )
            alias_owners[alias] = owner
    for relic in ct_relics:
        relic_terms = [*relic.aliases, _normalise_alias(relic.canonical)]
        if relic.abbrev:
            relic_terms.append(_normalise_alias(relic.abbrev))
        for alias in relic_terms:
            owner = f"ct_relic:{relic.id}"
            if alias in alias_owners and alias_owners[alias] != owner:
                raise BTD6DataValidationError(
                    f"alias collision: {alias!r} owned by both "
                    f"{alias_owners[alias]} and {owner}",
                )
            alias_owners[alias] = owner

    sources = {
        "towers": str(towers_raw["source"]),
        "heroes": str(heroes_raw["source"]),
        "maps": str(maps_raw["source"]),
        "modes": str(modes_raw["source"]),
        "rounds": str(rounds_raw["source"]),
    }
    if bloons_raw is not None:
        sources["bloons"] = str(bloons_raw["source"])
    if ct_relics_raw is not None:
        sources["ct_relics"] = str(ct_relics_raw["source"])

    return BTD6DataSet(
        data_version=str(towers_raw["data_version"]),
        game_version=str(towers_raw["game_version"]),
        sources=sources,
        towers=towers,
        heroes=heroes,
        maps=maps,
        modes=modes,
        rounds=rounds,
        bloons=bloons,
        ct_relics=ct_relics,
        powers=powers,
        monkey_knowledge=monkey_knowledge,
        geraldo_items=geraldo_items,
        bosses=bosses,
    )


_DATASET: BTD6DataSet | None = None


def get_dataset() -> BTD6DataSet:
    """Return the validated dataset (cached after first call)."""
    global _DATASET
    if _DATASET is None:
        _DATASET = _load_dataset()
    return _DATASET


def reset_cache() -> None:
    """Test seam — drop the cached dataset so a fresh load runs."""
    global _DATASET
    _DATASET = None


# ---------------------------------------------------------------------------
# Convenience accessors
# ---------------------------------------------------------------------------


def get_tower(tower_id: str) -> TowerEntry | None:
    for tower in get_dataset().towers:
        if tower.id == tower_id:
            return tower
    return None


def get_hero(hero_id: str) -> HeroEntry | None:
    for hero in get_dataset().heroes:
        if hero.id == hero_id:
            return hero
    return None


def get_map(map_id: str) -> MapEntry | None:
    for game_map in get_dataset().maps:
        if game_map.id == map_id:
            return game_map
    return None


def get_mode(mode_id: str) -> ModeEntry | None:
    for mode in get_dataset().modes:
        if mode.id == mode_id:
            return mode
    return None


def get_power(power_id: str) -> PowerEntry | None:
    """A Power by catalog id or its game-native ``power_id`` (case-insensitive)."""
    needle = power_id.strip().lower()
    for power in get_dataset().powers:
        if power.id == needle or power.power_id.lower() == needle:
            return power
    return None


def find_power(name: str) -> PowerEntry | None:
    """Resolve a Power by id / game-native id / canonical name / unique partial.

    The fuzzy counterpart to :func:`get_power` (which is id-only): an exact id or
    canonical match wins; otherwise a single case-insensitive substring of a
    canonical name is accepted, and an ambiguous substring returns ``None``.
    Shared by the ``btd6_power_lookup`` and ``btd6_power_effect`` tools so name
    resolution has one home.
    """
    direct = get_power(name)
    if direct is not None:
        return direct
    needle = (name or "").strip().lower()
    if not needle:
        return None
    powers = get_dataset().powers
    exact = [p for p in powers if p.canonical.lower() == needle]
    if exact:
        return exact[0]
    partial = [p for p in powers if needle in p.canonical.lower()]
    return partial[0] if len(partial) == 1 else None


def get_geraldo_item(item_id: str) -> GeraldoItemEntry | None:
    """A Geraldo item by catalog id (case-insensitive)."""
    needle = item_id.strip().lower()
    for item in get_dataset().geraldo_items:
        if item.id == needle:
            return item
    return None


def find_geraldo_item(name: str) -> GeraldoItemEntry | None:
    """Resolve a Geraldo item by id / canonical name / unique partial.

    The fuzzy counterpart to :func:`get_geraldo_item`: an exact id or canonical
    match wins; otherwise a single case-insensitive substring of a canonical name
    is accepted, and an ambiguous substring returns ``None``.
    """
    direct = get_geraldo_item(name)
    if direct is not None:
        return direct
    needle = (name or "").strip().lower()
    if not needle:
        return None
    items = get_dataset().geraldo_items
    exact = [g for g in items if g.canonical.lower() == needle]
    if exact:
        return exact[0]
    partial = [g for g in items if needle in g.canonical.lower()]
    return partial[0] if len(partial) == 1 else None


def get_boss(boss_id: str) -> BossEntry | None:
    """A Boss Bloon by catalog id (case-insensitive)."""
    needle = boss_id.strip().lower()
    for boss in get_dataset().bosses:
        if boss.id == needle:
            return boss
    return None


def find_boss(name: str) -> BossEntry | None:
    """Resolve a Boss Bloon by id / canonical name / unique partial.

    Exact id or canonical match wins; otherwise a single case-insensitive
    substring of a canonical name is accepted, and an ambiguous one returns
    ``None`` (the same fuzzy contract as :func:`find_geraldo_item`).
    """
    direct = get_boss(name)
    if direct is not None:
        return direct
    needle = (name or "").strip().lower()
    if not needle:
        return None
    bosses = get_dataset().bosses
    exact = [b for b in bosses if b.canonical.lower() == needle]
    if exact:
        return exact[0]
    partial = [b for b in bosses if needle in b.canonical.lower()]
    return partial[0] if len(partial) == 1 else None


def get_monkey_knowledge(knowledge_id: str) -> MonkeyKnowledgeEntry | None:
    for entry in get_dataset().monkey_knowledge:
        if entry.id == knowledge_id:
            return entry
    return None


def get_round(round_number: int) -> RoundEntry | None:
    for entry in get_dataset().rounds:
        if entry.round_number == round_number:
            return entry
    return None


def get_bloon(bloon_id: str) -> BloonEntry | None:
    for bloon in get_dataset().bloons:
        if bloon.id == bloon_id:
            return bloon
    return None


def resolve_bloon_id(name: str) -> str | None:
    """Map a bloon name / alias / plural to its id (``"purples"`` -> ``"purple"``).

    Matches id, canonical, or any committed alias; falls back to stripping a
    trailing plural ``s`` so unlisted plurals still resolve. ``None`` if no match.
    """
    key = (name or "").strip().lower()
    if not key:
        return None
    for bloon in get_dataset().bloons:
        surfaces = {
            bloon.id,
            bloon.canonical.lower(),
            *(a.lower() for a in bloon.aliases),
        }
        if key in surfaces or (key.endswith("s") and key[:-1] in surfaces):
            return bloon.id
    return None


# Natural words the model is likely to pass -> the committed ``properties`` tag,
# so "moab" / "regrowth" resolve to the canonical trait. Tags already spelled
# exactly (e.g. "camo", "lead") pass through the ``.get(..., default)`` below.
_BLOON_PROPERTY_SYNONYMS: dict[str, str] = {
    "moab": "moab-class",
    "moab class": "moab-class",
    "moab-class": "moab-class",
    "regrowth": "regrow",
}


def filter_bloons(
    *,
    bloon_property: str | None = None,
    category: str | None = None,
    immune: str | None = None,
) -> tuple[BloonEntry, ...]:
    """Bloons matching ALL supplied filters, in catalog order (empty if none).

    ``bloon_property`` matches a committed trait tag (``camo`` / ``lead`` /
    ``fortified`` / ``regrow`` / ``moab-class`` …), accepting a natural word via
    :data:`_BLOON_PROPERTY_SYNONYMS`; ``category`` matches the bloon class
    (``basic`` / ``special`` / ``moab_class`` / ``modifier``); ``immune`` matches
    a resisted damage-type name (``Explosion`` / ``Sharp`` / ``Cold`` …). Note
    that ``camo`` / ``fortified`` / ``regrow`` are also ``modifier``-class
    pseudo-entries — callers should surface those distinctly so an answer does
    not imply only the inherently-tagged bloons can ever carry the trait.
    """
    out = list(get_dataset().bloons)
    if bloon_property:
        needle = bloon_property.strip().lower()
        tag = _BLOON_PROPERTY_SYNONYMS.get(needle, needle)
        out = [b for b in out if tag in b.properties]
    if category:
        cat = category.strip().lower()
        out = [b for b in out if b.category == cat]
    if immune:
        dmg = immune.strip().lower()
        out = [b for b in out if any(i.lower() == dmg for i in b.immune_to)]
    return tuple(out)


# Cap the per-round detail a round-composition query returns so a wide range
# (e.g. "moabs in rounds 1-140") can't blow the grounding token budget.
_ROUND_DETAIL_CAP = 40

# How many "heaviest" rounds the tool ranks for the model. The tool ranks them
# itself (so the model never re-sorts the per-round list — it did, badly) and
# ranks from the FULL range, before _ROUND_DETAIL_CAP truncates the detail, so a
# wide range can't hide a heavy late round out of the ranking.
_HEAVIEST_CAP = 8


def round_composition(
    round_start: int,
    round_end: int | None = None,
    bloon: str | None = None,
) -> dict[str, Any]:
    """Bloon composition for a round or inclusive round range (standard rounds).

    With ``bloon``: the total count of that bloon across the range plus the
    per-round counts (only rounds where it appears). Without: each round's
    spawn groups + RBE. Lists are capped at :data:`_ROUND_DETAIL_CAP`.
    """
    lo = round_start
    hi = round_start if round_end is None else round_end
    if lo > hi:
        lo, hi = hi, lo
    rounds = [r for r in get_dataset().rounds if lo <= r.round_number <= hi]
    if not rounds:
        return {
            "found": False,
            "note": f"no standard rounds in {lo}-{hi} (valid 1-140)",
        }

    out: dict[str, Any] = {
        "found": True,
        "round_start": lo,
        "round_end": hi,
        "roundset": "default",
        "rounds_in_range": len(rounds),
    }
    if bloon:
        bid = resolve_bloon_id(bloon)
        if bid is None:
            return {"found": False, "note": f"unknown bloon: {bloon!r}"}
        per_round: list[dict[str, int]] = []
        total = 0
        for entry in rounds:
            count = sum(
                int(g.get("count", 0)) for g in entry.groups if g.get("bloon_id") == bid
            )
            if count:
                per_round.append({"round": entry.round_number, "count": count})
                total += count
        record = get_bloon(bid)
        # Rank the heaviest rounds here (count desc, ties by round asc) from the
        # FULL list — before the detail cap — so the model never has to sort and
        # a wide range can't truncate a heavy late round out of the ranking.
        heaviest = sorted(per_round, key=lambda d: (-d["count"], d["round"]))
        out.update(
            {
                "bloon": record.canonical if record else bid,
                "bloon_id": bid,
                "total": total,
                "rounds_with_bloon": len(per_round),
                "heaviest": heaviest[:_HEAVIEST_CAP],
                "per_round": per_round[:_ROUND_DETAIL_CAP],
                "truncated": len(per_round) > _ROUND_DETAIL_CAP,
            },
        )
    else:
        detail = []
        for entry in rounds[:_ROUND_DETAIL_CAP]:
            detail.append(
                {
                    "round": entry.round_number,
                    "rbe": entry.rbe,
                    "danger": entry.danger,
                    "groups": [
                        {"bloon": g.get("bloon_id"), "count": int(g.get("count", 0))}
                        for g in entry.groups
                    ],
                },
            )
        # Heaviest rounds by total RBE (children-inclusive), ranked over the full
        # range so the cap on ``rounds`` can't hide a heavy late round either.
        heaviest = sorted(
            ({"round": r.round_number, "rbe": r.rbe or 0} for r in rounds),
            key=lambda d: (-d["rbe"], d["round"]),
        )
        out.update(
            {
                "total_rbe": sum(r.rbe or 0 for r in rounds),
                "heaviest_by_rbe": heaviest[:_HEAVIEST_CAP],
                "rounds": detail,
                "truncated": len(rounds) > _ROUND_DETAIL_CAP,
            },
        )
    return out


def _find_by_surface(entries: tuple, name: str):
    """First entry whose id / canonical / alias matches ``name`` (case-insensitive)."""
    key = (name or "").strip().lower()
    if not key:
        return None
    for entry in entries:
        surfaces = {
            entry.id,
            entry.canonical.lower(),
            *(a.lower() for a in entry.aliases),
        }
        if key in surfaces:
            return entry
    return None


def find_map(name: str) -> MapEntry | None:
    """Resolve a map by name / alias / id (``"logs"`` -> the Logs entry)."""
    return _find_by_surface(get_dataset().maps, name)


def find_mode(name: str) -> ModeEntry | None:
    """Resolve a game mode by name / alias / id (``"chimps"`` -> CHIMPS)."""
    return _find_by_surface(get_dataset().modes, name)


def find_tower(name: str) -> TowerEntry | None:
    """Resolve a tower by name / alias / id (``"dart"`` -> Dart Monkey)."""
    return _find_by_surface(get_dataset().towers, name)


def cumulative_upgrade_costs(
    tower: str,
    *,
    difficulty: str = "medium",
    path: str | None = None,
) -> dict[str, Any]:
    """Cumulative cost to REACH each upgrade tier on ``tower``: the tower base
    plus every earlier tier on that path, already summed, per path.

    Difficulty pricing scales and rounds **each purchase** to $5 *before*
    summing, so a sum-then-scale total is wrong (e.g. Tack Shooter top path to
    Inferno Ring on Easy is $42,760, not ``round5($50,310 x 0.85)`` = $42,765).
    This returns the correct per-item running totals so the answer is a grounded
    tool output, not a number the model has to derive. Medium by default.
    """
    from utils.btd6 import difficulty_costs

    entry = _find_by_surface(get_dataset().towers, tower)
    if entry is None:
        return {"found": False, "note": f"unknown tower: {tower!r}"}
    try:
        diff = difficulty_costs.normalize_difficulty(difficulty)
    except ValueError:
        return {"found": False, "note": f"unknown difficulty: {difficulty!r}"}
    paths = entry.upgrade_paths or {}
    costs = entry.upgrade_costs or {}
    wanted = path.strip().lower() if path else None
    if wanted is not None and wanted not in paths:
        return {"found": False, "note": f"unknown path: {path!r} (top/mid/bot)"}

    base = difficulty_costs.cost_for_difficulty(entry.base_cost, diff)
    out_paths: dict[str, list[dict[str, Any]]] = {}
    for pkey, names in paths.items():
        if wanted is not None and pkey != wanted:
            continue
        path_costs = costs.get(pkey, ())
        running = base
        tiers: list[dict[str, Any]] = []
        for i, name in enumerate(names):
            med = path_costs[i] if i < len(path_costs) else 0
            step = difficulty_costs.cost_for_difficulty(med, diff) if med else 0
            running += step
            tiers.append(
                {
                    "tier": i + 1,
                    "name": name,
                    "upgrade_cost": step,
                    "cumulative_cost": running,
                },
            )
        out_paths[pkey] = tiers
    return {
        "found": True,
        "tower": entry.canonical,
        "difficulty": diff,
        "base_cost": base,
        "paths": out_paths,
        "note": (
            "cumulative_cost = tower base + all earlier tiers on that path at "
            f"{diff} pricing (each purchase rounded to $5, then summed)."
        ),
    }


def list_ct_relics() -> tuple[RelicEntry, ...]:
    """Every Contested Territory relic in the catalog (possibly empty)."""
    return get_dataset().ct_relics


def get_ct_relic(relic_id: str) -> RelicEntry | None:
    """Look up a relic by its catalog ``id``."""
    for relic in get_dataset().ct_relics:
        if relic.id == relic_id:
            return relic
    return None


def get_ct_relic_by_api_name(api_name: str) -> RelicEntry | None:
    """Resolve a Ninja Kiwi ``relic_name`` (e.g. ``SuperMonkeyStorm``).

    Match is case-insensitive so minor casing drift in the fetched
    fact does not orphan a tile from its catalog entry.
    """
    needle = api_name.strip().lower()
    if not needle:
        return None
    for relic in get_dataset().ct_relics:
        if relic.api_name.lower() == needle:
            return relic
    return None


def resolve_relic(term: str) -> RelicEntry | None:
    """Best-effort relic lookup by id, API name, canonical, abbrev or alias.

    Case-insensitive. Used by the live-tile query and the resolver so a
    relic can be addressed however the caller has it (catalog id from the
    resolver, ``relic_name`` from a fact, or a free-text canonical/alias).
    """
    needle = term.strip().lower()
    if not needle:
        return None
    for relic in get_dataset().ct_relics:
        candidates = {
            relic.id.lower(),
            relic.api_name.lower(),
            relic.canonical.lower(),
            *(a.lower() for a in relic.aliases),
        }
        if relic.abbrev:
            candidates.add(relic.abbrev.lower())
        if needle in candidates:
            return relic
    return None
