"""BTD6 deterministic knowledge queries.

Thin query API over :mod:`services.btd6_data_service`. Answers the
kind of question a BTD6 cog command needs to render an embed:
"what does this tower cost", "what's on this round", "what are the
restrictions for this mode". All answers come from the validated
fixture set; nothing is invented.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

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
    round_base_xp,
)
from services.btd6_source_registry import FreshnessBucket, bucket_freshness


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
    # Per-round economy stats (None when the data is unavailable). rbe / cash /
    # cumulative_cash come straight off RoundEntry; base_xp is the bloonswiki-
    # sourced round XP (see round_xp.json). Surfaced as the round embed's
    # "Economy" field.
    rbe: int | None = None
    cash: float | None = None
    cumulative_cash: float | None = None
    base_xp: int | None = None


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
        rbe=entry.rbe,
        cash=entry.cash,
        cumulative_cash=entry.cumulative_cash,
        base_xp=round_base_xp(entry.round_number),
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


# ---------------------------------------------------------------------------
# Live fact summary (entity_kind aggregates over ``btd6_facts``)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FactKindSummary:
    """One row per entity_kind in ``btd6_facts``.

    ``last_fetched_at`` is the newest ``fetched_at`` across all rows of
    that kind. ``bucket`` is the centrally-defined freshness bucket so
    the UI doesn't reinvent thresholds.
    """

    entity_kind: str
    fact_count: int
    last_fetched_at: datetime | None
    bucket: FreshnessBucket


async def fact_summary_by_kind() -> tuple[FactKindSummary, ...]:
    """Aggregate ``btd6_facts`` by entity_kind for the status panel.

    DB layer returns rows sorted by entity_kind (stable for tests);
    UI consumers re-sort by useful-first.
    """
    from utils.db.btd6_sources import aggregate_facts_by_entity_kind

    rows = await aggregate_facts_by_entity_kind()
    return tuple(
        FactKindSummary(
            entity_kind=row["entity_kind"],
            fact_count=int(row["fact_count"]),
            last_fetched_at=row.get("last_fetched_at"),
            bucket=bucket_freshness(row.get("last_fetched_at")),
        )
        for row in rows
    )


# ---------------------------------------------------------------------------
# Price aggregates (superlatives — "most/least expensive")
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UpgradePrice:
    """One purchasable upgrade (or Paragon) and its Medium cost."""

    tower: str  # canonical tower name
    path: str  # top / mid / bot / paragon
    tier: int  # 1..5; 6 for Paragon
    name: str
    cost: int


def all_upgrade_prices() -> tuple[UpgradePrice, ...]:
    """Every purchasable upgrade across all towers, incl. Paragons.

    Paragon costs come from the per-tower stats files; per-tier costs from the
    catalog. Used to answer superlative ("most/least expensive") questions.
    """
    from services import btd6_stats_service

    out: list[UpgradePrice] = []
    for tower in list_towers():
        for path, names in tower.upgrade_paths.items():
            costs = tower.upgrade_costs.get(path, ())
            for index, name in enumerate(names):
                cost = costs[index] if index < len(costs) else 0
                if name and cost > 0:
                    out.append(
                        UpgradePrice(tower.canonical, path, index + 1, name, cost),
                    )
        stats = btd6_stats_service.get_tower_stats(tower.id)
        if stats is not None and stats.paragon_cost:
            out.append(
                UpgradePrice(
                    tower.canonical,
                    "paragon",
                    6,
                    f"{tower.canonical} Paragon",
                    stats.paragon_cost,
                ),
            )
    return tuple(out)


def upgrades_by_price(
    *,
    highest: bool,
    limit: int = 3,
    kind: str = "all",
) -> tuple[UpgradePrice, ...]:
    """Top ``limit`` most-/least-expensive upgrades.

    ``kind`` filters the pool so callers can keep the three "most expensive"
    questions distinct:
      * ``"regular"`` — tier 1-5 upgrades only (excludes Paragons);
      * ``"paragon"`` — Paragons only;
      * ``"all"`` — both (Paragons dominate the top).
    """
    prices = all_upgrade_prices()
    if kind == "regular":
        prices = tuple(u for u in prices if u.path != "paragon")
    elif kind == "paragon":
        prices = tuple(u for u in prices if u.path == "paragon")
    ordered = sorted(prices, key=lambda u: u.cost, reverse=highest)
    return tuple(ordered[:limit])
