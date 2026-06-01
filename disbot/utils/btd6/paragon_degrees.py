"""BTD6 Paragon degree-dependent stat scaling.

A paragon's *degree-independent* stats (range, projectile count, speed, radius,
damage type, …) are stored once in its cleaned stats node. The *degree-dependent*
stats — attack cooldown, pierce, damage, damage modifiers, plus the boss-damage
multiplier and the power threshold — change with the paragon's degree (1..100).

This module reproduces those, ported field-for-field from the wiki's own
renderer ``Module:BTD6 stats`` ``parse_paragon_table`` (``{{#invoke:BTD6 stats|
paragon|…}}``), so the bot shows the exact same numbers as the paragon page::

    cooldown(d)   = rate / (1 + 0.01 * sqrt(50 * (d-1)))
    damage(d)     = base * (1 + 0.01*(d-1)) + floor((d-1)/10)       # d < 100
    pierce(d)     = floor(base * (1 + 0.01*(d-1))) + (d-1)/10        # d < 100
    damage_mod(d) = base * (1 + 0.01*(d-1))                         # d < 100
    <all three above at d == 100> = base * 2 + 10
    boss_mult(d)  = 1.0/1.25/1.5/1.75/2.0 stepping every 20 degrees, 2.25 at 100
    power(d)      = paragon_math.threshold(d)  (0 at degree 1)

Pure, stdlib-only (``utils`` layer): no I/O, no Discord, no services. The
:func:`degree_row` traversal walks the *cleaned* node shape produced by
``scripts/parse_bloonswiki._clean_node`` (``attacks``/``abilities`` are lists of
named dicts, projectiles carry nested ``effects``) — the same shape stored in
``disbot/data/btd6/stats/paragons/<id>.json`` and consumed by
``services.btd6_stats_service``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from utils.btd6 import paragon_math

MAX_DEGREE = paragon_math.MAX_DEGREE  # 100

# Damage-modifier field -> column label, in the wiki's emission order. Both the
# projectile and effect parsers check exactly this set, in this order.
_DAMAGE_MODIFIERS: tuple[tuple[str, str], ...] = (
    ("damageModifierForBoss", "Damage to bosses"),
    ("damageModifierForMoabs", "Damage to MOAB-Class"),
    ("damageModifierForCeramic", "Damage to Ceramic"),
    ("damageModifierForCamo", "Damage to Camo"),
    ("damageModifierForStunned", "Damage to stunned"),
    ("damageModifierForStickied", "Damage to stickied"),
)

# A "rate" at or above this is the wiki's "no real cooldown" sentinel; such
# attacks are omitted from the cooldown column.
_RATE_SENTINEL = 9999
# Pierce at or above this is effectively infinite and omitted from the table.
_PIERCE_SENTINEL = 99999


# ---------------------------------------------------------------------------
# Scalar scaling (verbatim ports)
# ---------------------------------------------------------------------------


def power_for_degree(degree: int) -> int:
    """Cumulative power required to reach ``degree`` (the table's Power column).

    Reproduces the wiki's ``degree_requirements`` table exactly: the same cubic
    the Paragon Calculator uses, but **rounded** (the displayed table rounds to
    the nearest whole power, whereas :func:`paragon_math.threshold` *floors* it
    for the calculator's "minimum power to reach" comparison — an off-by-one for
    ~half the degrees). Degree 1 is pinned to 0 (you start at degree 1 with no
    accumulated power) and degree 100 to the published 200,000 cap.
    """
    if degree <= 1:
        return 0
    if degree >= MAX_DEGREE:
        return paragon_math.TOTAL_POWER_FOR_MAX_DEGREE
    return round((50 * degree**3 + 5025 * degree**2 + 168324 * degree + 843000) / 600)


def boss_multiplier(degree: int) -> float:
    """Boss-damage multiplier for ``degree`` (steps every 20 degrees)."""
    if degree < 20:
        return 1.0
    if degree < 40:
        return 1.25
    if degree < 60:
        return 1.5
    if degree < 80:
        return 1.75
    if degree != MAX_DEGREE:
        return 2.0
    return 2.25


def scale_cooldown(rate: float, degree: int) -> float:
    """Attack/ability cooldown at ``degree`` (decreases with degree)."""
    return rate / (1 + 0.01 * math.sqrt((degree - 1) * 50))


def scale_damage(amount: float, degree: int) -> float:
    """Projectile/effect damage at ``degree``."""
    if degree == MAX_DEGREE:
        return amount * 2 + 10
    return amount * (1 + (degree - 1) * 0.01) + math.floor((degree - 1) / 10)


def scale_pierce(amount: float, degree: int) -> float:
    """Projectile pierce at ``degree``.

    Note the asymmetry with :func:`scale_damage`: the integer part is floored
    *before* the per-ten bonus is added as an un-floored tenth — faithful to the
    wiki's ``mfloor(amt*(1+(d-1)*0.01)) + (d-1)/10``.
    """
    if degree == MAX_DEGREE:
        return amount * 2 + 10
    return math.floor(amount * (1 + (degree - 1) * 0.01)) + (degree - 1) / 10


def scale_damage_modifier(amount: float, degree: int) -> float:
    """A bonus-damage modifier (vs bosses / ceramic / …) at ``degree``."""
    if degree == MAX_DEGREE:
        return amount * 2 + 10
    return amount * (1 + (degree - 1) * 0.01)


def format_value(value: float) -> str:
    """Render a scaled value like the wiki (``%.4g`` — 4 significant figures)."""
    return f"{value:.4g}"


# ---------------------------------------------------------------------------
# Per-degree row (faithful traversal of the cleaned node)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DegreeStat:
    """One degree-dependent cell: a stat under a named attack/projectile group."""

    group: str  # column-group header (attack / projectile / effect / ability name)
    label: str  # stat label ("Cooldown", "Pierce", "Damage", "Damage to bosses", …)
    value: float
    is_modifier: bool = False  # render with a leading "+"
    is_cooldown: bool = False  # render with a trailing "s"


@dataclass(frozen=True)
class DegreeRow:
    """A paragon's full degree-dependent stat line for one degree."""

    degree: int
    power: int
    boss_multiplier: float
    stats: tuple[DegreeStat, ...]


def _projectile_stats(proj: dict[str, Any], degree: int) -> list[DegreeStat]:
    group = str(proj.get("name", "Projectile"))
    out: list[DegreeStat] = []
    pierce = proj.get("pierce")
    if (
        isinstance(pierce, (int, float))
        and (proj.get("maxPierce") or 0) < 1
        and pierce < _PIERCE_SENTINEL
    ):
        out.append(DegreeStat(group, "Pierce", scale_pierce(pierce, degree)))
    damage = proj.get("damage")
    if isinstance(damage, (int, float)) and damage > 0:
        out.append(DegreeStat(group, "Damage", scale_damage(damage, degree)))
    for field, label in _DAMAGE_MODIFIERS:
        amount = proj.get(field)
        if isinstance(amount, (int, float)):
            out.append(
                DegreeStat(
                    group,
                    label,
                    scale_damage_modifier(amount, degree),
                    is_modifier=True,
                ),
            )
    for effect in proj.get("effects", []) or []:
        out.extend(_effect_stats(effect, degree))
    return out


def _effect_stats(effect: dict[str, Any], degree: int) -> list[DegreeStat]:
    group = str(effect.get("name", "Effect"))
    out: list[DegreeStat] = []
    damage = effect.get("damage")
    if isinstance(damage, (int, float)):
        out.append(DegreeStat(group, "Damage", scale_damage(damage, degree)))
    for field, label in _DAMAGE_MODIFIERS:
        amount = effect.get(field)
        if isinstance(amount, (int, float)):
            out.append(
                DegreeStat(
                    group,
                    label,
                    scale_damage_modifier(amount, degree),
                    is_modifier=True,
                ),
            )
    return out


def _attack_stats(attack: dict[str, Any], degree: int) -> list[DegreeStat]:
    group = str(attack.get("name", "Attack"))
    out: list[DegreeStat] = []
    rate = attack.get("rate")
    if (
        isinstance(rate, (int, float))
        and rate < _RATE_SENTINEL
        and "rateMin" not in attack
    ):
        out.append(
            DegreeStat(
                group,
                "Cooldown",
                scale_cooldown(rate, degree),
                is_cooldown=True,
            ),
        )
    for proj in attack.get("projectiles", []) or []:
        out.extend(_projectile_stats(proj, degree))
    return out


def _ability_stats(ability: dict[str, Any], degree: int) -> list[DegreeStat]:
    group = str(ability.get("name", "Ability"))
    out: list[DegreeStat] = []
    cooldown = ability.get("cooldown")
    if isinstance(cooldown, (int, float)):
        out.append(
            DegreeStat(
                group,
                "Cooldown",
                scale_cooldown(cooldown, degree),
                is_cooldown=True,
            ),
        )
    for proj in ability.get("projectiles", []) or []:
        out.extend(_projectile_stats(proj, degree))
    for attack in ability.get("attacks", []) or []:
        out.extend(_attack_stats(attack, degree))
    return out


def degree_row(base: dict[str, Any], degree: int) -> DegreeRow:
    """Compute the full degree-dependent stat row for a paragon ``base`` node.

    ``degree`` is clamped to 1..100. The traversal order (top-level
    ``projectiles`` as attacks, then ``attacks``, then ``abilities``, then
    ``zones`` effects) and every field gate mirror the wiki's
    ``parse_paragon_table`` exactly, so the resulting cells line up with the
    paragon page's "Degree-dependent stats" table.
    """
    d = max(1, min(MAX_DEGREE, degree))
    stats: list[DegreeStat] = []
    for attack in base.get("projectiles", []) or []:
        stats.extend(_attack_stats(attack, d))
    for attack in base.get("attacks", []) or []:
        stats.extend(_attack_stats(attack, d))
    for ability in base.get("abilities", []) or []:
        stats.extend(_ability_stats(ability, d))
    for effect in base.get("zones", []) or []:
        stats.extend(_effect_stats(effect, d))
    return DegreeRow(
        degree=d,
        power=power_for_degree(d),
        boss_multiplier=boss_multiplier(d),
        stats=tuple(stats),
    )


def degree_stat_groups(base: dict[str, Any]) -> tuple[str, ...]:
    """Distinct column-group headers a paragon's degree table would show.

    Degree-independent (the groups are the same at every degree), so callers can
    build a header once. Uses degree 1 since the gates don't depend on degree.
    """
    seen: list[str] = []
    for stat in degree_row(base, 1).stats:
        if stat.group not in seen:
            seen.append(stat.group)
    return tuple(seen)


__all__ = [
    "MAX_DEGREE",
    "DegreeRow",
    "DegreeStat",
    "boss_multiplier",
    "degree_row",
    "degree_stat_groups",
    "format_value",
    "power_for_degree",
    "scale_cooldown",
    "scale_damage",
    "scale_damage_modifier",
    "scale_pierce",
    "format_value",
]
