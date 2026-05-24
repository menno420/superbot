"""BTD6 deterministic knowledge queries.

Thin query API over :mod:`services.btd6_data_service`. Answers the
kind of question a BTD6 cog command needs to render an embed:
"what does this tower cost", "what's on this round", "what are the
restrictions for this mode". All answers come from the validated
fixture set; nothing is invented.
"""

from __future__ import annotations

from dataclasses import dataclass

from services.btd6_data_service import (
    HeroEntry,
    MapEntry,
    ModeEntry,
    RoundEntry,
    TowerEntry,
    get_dataset,
    get_hero,
    get_map,
    get_mode,
    get_round,
    get_tower,
)


@dataclass(frozen=True)
class TowerFact:
    """A query result for a tower lookup."""

    tower: TowerEntry
    base_cost: int
    upgrade_paths: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class RoundFact:
    """A query result for a round lookup."""

    round_number: int
    summary: str
    danger: str
    common_threats: tuple[str, ...]


def tower_fact(tower_id: str) -> TowerFact | None:
    tower = get_tower(tower_id)
    if tower is None:
        return None
    return TowerFact(
        tower=tower,
        base_cost=tower.base_cost,
        upgrade_paths=dict(tower.upgrade_paths),
    )


def hero_fact(hero_id: str) -> HeroEntry | None:
    return get_hero(hero_id)


def map_fact(map_id: str) -> MapEntry | None:
    return get_map(map_id)


def mode_fact(mode_id: str) -> ModeEntry | None:
    return get_mode(mode_id)


def round_fact(round_number: int) -> RoundFact | None:
    entry = get_round(round_number)
    if entry is None:
        return None
    return RoundFact(
        round_number=entry.round_number,
        summary=entry.summary,
        danger=entry.danger,
        common_threats=entry.common_threats,
    )


def list_towers() -> tuple[TowerEntry, ...]:
    return get_dataset().towers


def list_heroes() -> tuple[HeroEntry, ...]:
    return get_dataset().heroes


def list_maps() -> tuple[MapEntry, ...]:
    return get_dataset().maps


def list_modes() -> tuple[ModeEntry, ...]:
    return get_dataset().modes


def list_rounds() -> tuple[RoundEntry, ...]:
    return get_dataset().rounds


def data_version() -> str:
    return get_dataset().data_version


def game_version() -> str:
    return get_dataset().game_version
