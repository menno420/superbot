"""BTD6 superlative / aggregate queries — rank the roster by cost or combat stat.

Answers "most / least / highest / lowest …" ranking questions across the whole
roster — most expensive paragon, highest-DPS paragon, longest-range tower — so
the AI can answer them in one call instead of looking entities up one by one.
Derived at runtime from the committed data in :mod:`services.btd6_data_service`
and :mod:`services.btd6_stats_service`. Read-only, no DB. Backs the
``btd6_superlative_lookup`` AI tool.

**DPS here is a ROUGH estimate only** — the sum over every attack of all its
projectiles' damage ÷ cooldown. It ignores targeting, pierce, AoE, and uptime,
so it is never authoritative; it exists to answer "roughly which is highest",
and the exact figures live in the per-attack breakdown from
``btd6_paragon_stats_at_degree``. Paragon combat stats are at degree 1 (base);
damage / pierce describe the main attack. Tower combat stats are base (0-0-0).
"""

from __future__ import annotations

from dataclasses import dataclass

from services import btd6_data_service, btd6_stats_service

# Cost metrics.
UPGRADE_COST = "upgrade_cost"
TOWER_COST = "tower_cost"
PARAGON_COST = "paragon_cost"
# Combat metrics (paragons at degree 1, towers at base 0-0-0).
PARAGON_DPS = "paragon_dps"
PARAGON_DAMAGE = "paragon_damage"
PARAGON_PIERCE = "paragon_pierce"
TOWER_DPS = "tower_dps"
TOWER_DAMAGE = "tower_damage"
TOWER_PIERCE = "tower_pierce"
TOWER_RANGE = "tower_range"

_COST_METRICS = (UPGRADE_COST, TOWER_COST, PARAGON_COST)
_PARAGON_COMBAT = (PARAGON_DPS, PARAGON_DAMAGE, PARAGON_PIERCE)
_TOWER_COMBAT = (TOWER_DPS, TOWER_DAMAGE, TOWER_PIERCE, TOWER_RANGE)
METRICS: tuple[str, ...] = _COST_METRICS + _PARAGON_COMBAT + _TOWER_COMBAT

_DEFAULT_LIMIT = 3


@dataclass(frozen=True)
class SuperlativeHit:
    """One ranked result: a value (with unit) and what it belongs to."""

    value: float
    unit: str  # "$", "DPS", "dmg", "pierce", "range"
    what: str  # e.g. "Glaive Dominus (Boomerang Monkey Paragon)"
    tower_id: str
    detail: str = ""  # e.g. "25 dmg / 0.04s (degree 1)"

    @property
    def cost(self) -> int:
        """Back-compat accessor for the cost metrics (value is a dollar amount)."""
        return int(self.value)


# ---------------------------------------------------------------------------
# Cost rows
# ---------------------------------------------------------------------------


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
                        value=float(cost),
                        unit="$",
                        what=f"{name} ({tower.canonical}, {path} path tier {idx})",
                        tower_id=tower.id,
                    ),
                )
    return rows


def _tower_cost_rows() -> list[SuperlativeHit]:
    return [
        SuperlativeHit(
            value=float(t.base_cost),
            unit="$",
            what=t.canonical,
            tower_id=t.id,
        )
        for t in btd6_data_service.get_dataset().towers
        if t.base_cost
    ]


def _paragon_cost_rows() -> list[SuperlativeHit]:
    rows: list[SuperlativeHit] = []
    for tower in btd6_data_service.get_dataset().towers:
        stats = btd6_stats_service.get_tower_stats(tower.id)
        if stats is not None and stats.paragon_cost:
            label = (
                f"{stats.paragon_name} ({tower.canonical} Paragon)"
                if stats.paragon_name
                else f"{tower.canonical} Paragon"
            )
            rows.append(
                SuperlativeHit(
                    value=float(stats.paragon_cost),
                    unit="$",
                    what=label,
                    tower_id=tower.id,
                ),
            )
    return rows


# ---------------------------------------------------------------------------
# Combat rows (single-target main-attack DPS / damage / pierce / range)
# ---------------------------------------------------------------------------


def _combat_hit(
    metric: str,
    *,
    dps: float | None,
    damage: float | None,
    pierce: float | None,
    attack_range: float | None,
    what: str,
    tower_id: str,
    context: str,
) -> SuperlativeHit | None:
    """Build a ranked hit for a combat ``metric``, or None if the field is absent.

    DPS is a labelled ROUGH estimate (sums all projectile damage / cooldown);
    damage / pierce describe the main attack; range is the tier's range.
    """
    if metric in (PARAGON_DPS, TOWER_DPS):
        if not dps:
            return None
        return SuperlativeHit(
            value=round(dps, 1),
            unit="DPS (rough)",
            what=what,
            tower_id=tower_id,
            detail=(
                f"ROUGH estimate, sums all attacks ({context}); ignores "
                "targeting/pierce/AoE — quote the per-attack breakdown for exact"
            ),
        )
    if metric in (PARAGON_DAMAGE, TOWER_DAMAGE) and damage:
        return SuperlativeHit(damage, "dmg", what, tower_id, f"main attack ({context})")
    if metric in (PARAGON_PIERCE, TOWER_PIERCE) and pierce:
        return SuperlativeHit(
            pierce,
            "pierce",
            what,
            tower_id,
            f"main attack ({context})",
        )
    if metric == TOWER_RANGE and attack_range:
        return SuperlativeHit(float(attack_range), "range", what, tower_id, context)
    return None


def _paragon_combat_rows(metric: str) -> list[SuperlativeHit]:
    rows: list[SuperlativeHit] = []
    for tower in btd6_data_service.get_dataset().towers:
        pstats = btd6_stats_service.get_paragon_stats_by_tower(tower.id)
        if pstats is None:
            continue
        # Degree 1 (base): damage/pierce describe the main attack; the rough DPS
        # estimate sums every attack so multi-attack paragons aren't understated.
        attacks = pstats.base.get("attacks") or []
        main = btd6_stats_service.main_projectile_stats(attacks, 1)
        m_damage, m_pierce = main if main is not None else (None, None)
        hit = _combat_hit(
            metric,
            dps=btd6_stats_service.rough_attack_dps(attacks, 1),
            damage=m_damage,
            pierce=m_pierce,
            attack_range=None,
            what=f"{pstats.canonical} ({tower.canonical} Paragon)",
            tower_id=tower.id,
            context="degree 1",
        )
        if hit is not None:
            rows.append(hit)
    return rows


def _tower_combat_rows(metric: str) -> list[SuperlativeHit]:
    rows: list[SuperlativeHit] = []
    for tower in btd6_data_service.get_dataset().towers:
        stats = btd6_stats_service.get_tower_stats(tower.id)
        if stats is None:
            continue
        tier = stats.tier("000")
        if tier is None:
            continue
        normal = btd6_stats_service.normal_stats(tier)
        hit = _combat_hit(
            metric,
            dps=btd6_stats_service.rough_attack_dps(tier.get("attacks") or [], None),
            damage=float(normal.damage) if normal.damage else None,
            pierce=float(normal.pierce) if normal.pierce else None,
            attack_range=normal.attack_range,
            what=tower.canonical,
            tower_id=tower.id,
            context="base 0-0-0",
        )
        if hit is not None:
            rows.append(hit)
    return rows


def rank(
    metric: str,
    *,
    tier: int | None = None,
    cheapest: bool = False,
    limit: int = _DEFAULT_LIMIT,
) -> list[SuperlativeHit]:
    """Rank the roster by ``metric``, highest first (or lowest when ``cheapest``).

    Cost: ``upgrade_cost`` (optionally scoped to ``tier`` 1-5), ``tower_cost``
    (base placement), ``paragon_cost``. Combat: ``paragon_dps`` /
    ``paragon_damage`` / ``paragon_pierce`` (degree 1), and ``tower_dps`` /
    ``tower_damage`` / ``tower_pierce`` / ``tower_range`` (base 0-0-0). Empty list
    for an unknown metric.
    """
    if metric == UPGRADE_COST:
        rows = _upgrade_rows(tier)
    elif metric == TOWER_COST:
        rows = _tower_cost_rows()
    elif metric == PARAGON_COST:
        rows = _paragon_cost_rows()
    elif metric in _PARAGON_COMBAT:
        rows = _paragon_combat_rows(metric)
    elif metric in _TOWER_COMBAT:
        rows = _tower_combat_rows(metric)
    else:
        return []
    rows.sort(key=lambda h: h.value, reverse=not cheapest)
    return rows[: max(1, limit)]


__all__ = [
    "METRICS",
    "PARAGON_COST",
    "PARAGON_DAMAGE",
    "PARAGON_DPS",
    "PARAGON_PIERCE",
    "TOWER_COST",
    "TOWER_DAMAGE",
    "TOWER_DPS",
    "TOWER_PIERCE",
    "TOWER_RANGE",
    "UPGRADE_COST",
    "SuperlativeHit",
    "rank",
]
