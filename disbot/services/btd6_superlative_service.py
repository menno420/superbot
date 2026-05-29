"""BTD6 superlative / aggregate queries — "most / least expensive …".

Answers ranking questions across the whole roster (most expensive tier-4
upgrade, cheapest tower, priciest paragon) from the committed cost data in
:mod:`services.btd6_data_service` and :mod:`services.btd6_stats_service`.
Derived at runtime — no separate index — read-only, no DB. Backs the
``btd6_superlative_lookup`` AI tool.
"""

from __future__ import annotations

from dataclasses import dataclass

from services import btd6_data_service, btd6_stats_service

UPGRADE_COST = "upgrade_cost"
TOWER_COST = "tower_cost"
PARAGON_COST = "paragon_cost"
METRICS: tuple[str, ...] = (UPGRADE_COST, TOWER_COST, PARAGON_COST)

_DEFAULT_LIMIT = 3


@dataclass(frozen=True)
class SuperlativeHit:
    """One ranked result: a cost and what it belongs to."""

    cost: int
    what: str  # e.g. "Sun Temple (Super Monkey, top path tier 4)"
    tower_id: str


def _upgrade_rows(tier: int | None) -> list[SuperlativeHit]:
    rows: list[SuperlativeHit] = []
    for tower in btd6_data_service.get_dataset().towers:
        for path, costs in tower.upgrade_costs.items():
            for idx, cost in enumerate(costs, start=1):
                if not cost or (tier is not None and idx != tier):
                    continue
                names = tower.upgrade_paths.get(path, ())
                name = names[idx - 1] if idx - 1 < len(names) else f"tier {idx}"
                rows.append(
                    SuperlativeHit(
                        cost=int(cost),
                        what=f"{name} ({tower.canonical}, {path} path tier {idx})",
                        tower_id=tower.id,
                    ),
                )
    return rows


def _tower_rows() -> list[SuperlativeHit]:
    return [
        SuperlativeHit(cost=int(t.base_cost), what=t.canonical, tower_id=t.id)
        for t in btd6_data_service.get_dataset().towers
        if t.base_cost
    ]


def _paragon_rows() -> list[SuperlativeHit]:
    rows: list[SuperlativeHit] = []
    for tower in btd6_data_service.get_dataset().towers:
        stats = btd6_stats_service.get_tower_stats(tower.id)
        if stats is not None and stats.paragon_cost:
            rows.append(
                SuperlativeHit(
                    cost=int(stats.paragon_cost),
                    what=f"{tower.canonical} Paragon",
                    tower_id=tower.id,
                ),
            )
    return rows


def rank(
    metric: str,
    *,
    tier: int | None = None,
    cheapest: bool = False,
    limit: int = _DEFAULT_LIMIT,
) -> list[SuperlativeHit]:
    """Rank towers/upgrades by a cost ``metric``.

    ``upgrade_cost`` optionally scoped to ``tier`` (1-5); ``tower_cost`` ranks
    base placement cost; ``paragon_cost`` ranks the tier-6 paragons. Highest
    first, or lowest when ``cheapest``. Empty list for an unknown metric.
    """
    if metric == UPGRADE_COST:
        rows = _upgrade_rows(tier)
    elif metric == TOWER_COST:
        rows = _tower_rows()
    elif metric == PARAGON_COST:
        rows = _paragon_rows()
    else:
        return []
    rows.sort(key=lambda h: h.cost, reverse=not cheapest)
    return rows[: max(1, limit)]


__all__ = [
    "METRICS",
    "PARAGON_COST",
    "TOWER_COST",
    "UPGRADE_COST",
    "SuperlativeHit",
    "rank",
]
