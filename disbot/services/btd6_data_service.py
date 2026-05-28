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

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "btd6"


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
    wiki_url: str


@dataclass(frozen=True)
class ModeEntry:
    id: str
    canonical: str
    aliases: tuple[str, ...]
    starting_cash: int
    starting_lives: int
    description: str
    restrictions: tuple[str, ...]


@dataclass(frozen=True)
class RoundEntry:
    round_number: int
    summary: str
    danger: str
    common_threats: tuple[str, ...]


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
    "wiki_url",
)
_REQUIRED_MODE_FIELDS = (
    "id",
    "canonical",
    "aliases",
    "starting_cash",
    "starting_lives",
    "description",
    "restrictions",
)
_REQUIRED_ROUND_FIELDS = ("round", "summary", "danger", "common_threats")
_REQUIRED_HERO_ABILITY_FIELDS = ("level", "name", "summary")


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
        wiki_url=str(raw["wiki_url"]),
    )


def _parse_mode(raw: dict[str, Any]) -> ModeEntry:
    _require_keys(raw, _REQUIRED_MODE_FIELDS, where=f"mode {raw.get('id')!r}")
    return ModeEntry(
        id=str(raw["id"]),
        canonical=str(raw["canonical"]),
        aliases=tuple(_normalise_alias(a) for a in raw["aliases"]),
        starting_cash=int(raw["starting_cash"]),
        starting_lives=int(raw["starting_lives"]),
        description=str(raw["description"]),
        restrictions=tuple(str(r) for r in raw["restrictions"]),
    )


def _parse_round(raw: dict[str, Any]) -> RoundEntry:
    _require_keys(raw, _REQUIRED_ROUND_FIELDS, where=f"round {raw.get('round')!r}")
    return RoundEntry(
        round_number=int(raw["round"]),
        summary=str(raw["summary"]),
        danger=str(raw["danger"]),
        common_threats=tuple(str(t) for t in raw["common_threats"]),
    )


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _load_file(name: str) -> dict[str, Any]:
    path = DATA_ROOT / name
    if not path.exists():
        raise BTD6DataValidationError(
            f"missing fixture file: {path}",
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    _require_keys(raw, _REQUIRED_TOP_LEVEL, where=str(path))
    return raw


def _load_dataset() -> BTD6DataSet:
    towers_raw = _load_file("towers.json")
    heroes_raw = _load_file("heroes.json")
    maps_raw = _load_file("maps.json")
    modes_raw = _load_file("modes.json")
    rounds_raw = _load_file("rounds.json")

    towers = tuple(_parse_tower(t) for t in towers_raw.get("towers", []))
    heroes = tuple(_parse_hero(h) for h in heroes_raw.get("heroes", []))
    maps = tuple(_parse_map(m) for m in maps_raw.get("maps", []))
    modes = tuple(_parse_mode(m) for m in modes_raw.get("modes", []))
    rounds = tuple(_parse_round(r) for r in rounds_raw.get("rounds", []))

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

    return BTD6DataSet(
        data_version=str(towers_raw["data_version"]),
        game_version=str(towers_raw["game_version"]),
        sources={
            "towers": str(towers_raw["source"]),
            "heroes": str(heroes_raw["source"]),
            "maps": str(maps_raw["source"]),
            "modes": str(modes_raw["source"]),
            "rounds": str(rounds_raw["source"]),
        },
        towers=towers,
        heroes=heroes,
        maps=maps,
        modes=modes,
        rounds=rounds,
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


def get_round(round_number: int) -> RoundEntry | None:
    for entry in get_dataset().rounds:
        if entry.round_number == round_number:
            return entry
    return None
