"""BTD6 Paragon degree math — forward power model and reverse solver.

Pure, stdlib-only (``utils`` layer). This module replicates the public
Paragon Calculator API's power formula (validated field-by-field against the
live endpoint) so the bot can:

* compute a degree offline as a **labelled fallback** when the live API is
  unreachable, and
* solve the inverse problem the API does **not** expose — "what inputs reach
  Degree X for the least cash / least tiers / least pops, or balanced".

The HTTP wrapper, response caching, and live-vs-local reconciliation live in
``services/paragon_service.py``; this module never performs I/O.

Formula (per the API reference, confirmed against the live endpoint)::

    popsPower    = min(90000, floor((pops + income*4) / 180))
    upgradesPower= min(10000, upgrade_count * 100)            # upgrade_count cap 100
    cashPower    = min(60000, floor(cash_spent*(20000/base) + slider*(20000/(base*1.05))))
    t5Power      = min(50000, tier5_count * 6000)
    totemsPower  = geraldo_totems * 2000                      # uncapped
    total_power  = sum of the above                           # reported RAW (may exceed 200000)
    threshold(D) = floor((50*D^3 + 5025*D^2 + 168324*D + 843000) / 600), threshold(100)=200000
    degree       = max D in 1..100 with threshold(D) <= total_power

``base`` (the paragon's adjusted base price for the difficulty) is required for
the cash axis; the committed :data:`BASE_PRICES_MEDIUM` table was captured from
the live API and the other difficulties are derived with the shared BTD6
multipliers (``utils.btd6.difficulty_costs``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from enum import Enum

from utils.btd6.difficulty_costs import cost_for_difficulty

# --- power model constants ---------------------------------------------------

MAX_DEGREE = 100
TOTAL_POWER_FOR_MAX_DEGREE = 200_000

POPS_POWER_CAP = 90_000
UPGRADES_POWER_CAP = 10_000
CASH_POWER_CAP = 60_000
T5_POWER_CAP = 50_000

POPS_PER_POWER = 180
INCOME_TO_POPS = 4
POWER_PER_UPGRADE_TIER = 100
MAX_UPGRADE_TIERS = 100
POWER_PER_EXTRA_T5 = 6_000
POWER_PER_TOTEM = 2_000
CASH_POWER_NUMERATOR = 20_000  # power per $1 == CASH_POWER_NUMERATOR / base_price
SLIDER_PREMIUM = 1.05  # slider cash is 95% efficient (5% convenience fee)
SLIDER_MAX_BASE_MULTIPLE = 3.15  # in-game slider clamp

SOLO_DART_MAX_EXTRA_T5 = 1
COOP_MAX_EXTRA_T5 = 9

_DART_PARAGON_ID = "apex_plasma_master"


# --- paragon catalogue -------------------------------------------------------


@dataclass(frozen=True)
class Paragon:
    """A BTD6 paragon and its medium-difficulty adjusted base price."""

    paragon_id: str
    name: str
    tower: str
    base_price_medium: int

    @property
    def is_dart(self) -> bool:
        return self.paragon_id == _DART_PARAGON_ID


# base_price_medium values captured once from the live Paragon Calculator API
# (POST /api/paragon/calculate, difficulty="medium") and committed so the local
# fallback and reverse solver stay deterministic without a network round-trip.
PARAGONS: tuple[Paragon, ...] = (
    Paragon("apex_plasma_master", "Apex Plasma Master", "Dart Monkey", 150_000),
    Paragon("glaive_dominus", "Glaive Dominus", "Boomerang Monkey", 375_000),
    Paragon("ascended_shadow", "Ascended Shadow", "Ninja Monkey", 500_000),
    Paragon("navarch_of_the_seas", "Navarch of the Seas", "Monkey Buccaneer", 500_000),
    Paragon("nautic_siege_core", "Nautic Siege Core", "Monkey Sub", 400_000),
    Paragon("master_builder", "Master Builder", "Engineer Monkey", 650_000),
    Paragon("magus_perfectus", "Magus Perfectus", "Wizard Monkey", 800_000),
    Paragon("goliath_doomship", "Goliath Doomship", "Monkey Ace", 900_000),
    Paragon(
        "crucible_of_steel_and_flame",
        "Crucible of Steel and Flame",
        "Tack Shooter",
        200_000,
    ),
    Paragon(
        "mega_massive_munitions_factory",
        "Mega Massive Munitions Factory",
        "Spike Factory",
        750_000,
    ),
    Paragon(
        "ballistic_obliteration_missile_bunker",
        "Ballistic Obliteration Missile Bunker (B.O.M.B.)",
        "Bomb Shooter",
        600_000,
    ),
    Paragon("herald_of_everfrost", "Herald of Everfrost", "Ice Monkey", 300_000),
    Paragon("root_of_all_nature", "Root of all Nature", "Druid", 475_000),
)

BASE_PRICES_MEDIUM: dict[str, int] = {
    p.paragon_id: p.base_price_medium for p in PARAGONS
}

_BY_ID: dict[str, Paragon] = {p.paragon_id: p for p in PARAGONS}

# Player-facing shorthand → paragon id. Tower names, paragon names, and ids are
# matched automatically; this table only adds the colloquial extras.
_ALIASES: dict[str, str] = {
    "dart": "apex_plasma_master",
    "apex": "apex_plasma_master",
    "apex plasma": "apex_plasma_master",
    "boomer": "glaive_dominus",
    "boomerang": "glaive_dominus",
    "glaive": "glaive_dominus",
    "ninja": "ascended_shadow",
    "shadow": "ascended_shadow",
    "ascended": "ascended_shadow",
    "bucc": "navarch_of_the_seas",
    "buccaneer": "navarch_of_the_seas",
    "boat": "navarch_of_the_seas",
    "navarch": "navarch_of_the_seas",
    "sub": "nautic_siege_core",
    "submarine": "nautic_siege_core",
    "nautic": "nautic_siege_core",
    "nautic siege": "nautic_siege_core",
    "engi": "master_builder",
    "engineer": "master_builder",
    "builder": "master_builder",
    "wizard": "magus_perfectus",
    "magus": "magus_perfectus",
    "ace": "goliath_doomship",
    "goliath": "goliath_doomship",
    "doomship": "goliath_doomship",
    "tack": "crucible_of_steel_and_flame",
    "crucible": "crucible_of_steel_and_flame",
    "spact": "mega_massive_munitions_factory",
    "spike": "mega_massive_munitions_factory",
    "spike factory": "mega_massive_munitions_factory",
    "mmmf": "mega_massive_munitions_factory",
    "munitions": "mega_massive_munitions_factory",
    "bomb": "ballistic_obliteration_missile_bunker",
    "b.o.m.b.": "ballistic_obliteration_missile_bunker",
    "bomb shooter": "ballistic_obliteration_missile_bunker",
    "ice": "herald_of_everfrost",
    "herald": "herald_of_everfrost",
    "everfrost": "herald_of_everfrost",
    "druid": "root_of_all_nature",
    "root": "root_of_all_nature",
    "nature": "root_of_all_nature",
}


def paragon_surfaces() -> tuple[tuple[str, str], ...]:
    """Every ``(surface, paragon_id)`` the resolver matches, for text scanning.

    Paragon names, tower names, ids, and the colloquial aliases — so a
    multi-paragon comparison can find *all* mentions in a sentence the same way
    :func:`resolve_paragon` matches a single string. Surfaces are lower-cased;
    duplicates (a surface that equals its id) are returned as-is — the caller
    dedups on the resolved id, not the surface.
    """
    surfaces: list[tuple[str, str]] = []
    for paragon in PARAGONS:
        surfaces.append((paragon.name.lower(), paragon.paragon_id))
        surfaces.append((paragon.tower.lower(), paragon.paragon_id))
        surfaces.append((paragon.paragon_id, paragon.paragon_id))
    for alias, pid in _ALIASES.items():
        surfaces.append((alias, pid))
    return tuple(surfaces)


def resolve_paragon(text: str) -> Paragon | None:
    """Resolve a tower name, paragon name, paragon id, or shorthand alias.

    Case-insensitive; tolerates a trailing " paragon" (e.g. "dart paragon").
    Returns ``None`` when nothing matches.
    """
    key = " ".join(text.strip().lower().split())
    if not key:
        return None
    if key.endswith(" paragon"):
        key = key[: -len(" paragon")].strip()
    if key in _BY_ID:
        return _BY_ID[key]
    for paragon in PARAGONS:
        if key in (paragon.name.lower(), paragon.tower.lower(), paragon.paragon_id):
            return paragon
    alias = _ALIASES.get(key)
    return _BY_ID[alias] if alias else None


def base_price(paragon: Paragon, difficulty: str) -> int:
    """Adjusted base price for ``paragon`` at ``difficulty`` (mode-aware)."""
    return cost_for_difficulty(paragon.base_price_medium, difficulty)


# --- degree thresholds -------------------------------------------------------


def threshold(degree: int) -> int:
    """Minimum total power required to reach ``degree`` (1..100)."""
    if degree >= MAX_DEGREE:
        return TOTAL_POWER_FOR_MAX_DEGREE
    if degree <= 1:
        return (50 + 5025 + 168324 + 843000) // 600  # threshold(1) == 1693
    return (50 * degree**3 + 5025 * degree**2 + 168324 * degree + 843000) // 600


def degree_from_power(power: int) -> int:
    """Highest degree (1..100) reachable with ``power`` total power."""
    degree = 1
    for candidate in range(2, MAX_DEGREE + 1):
        if threshold(candidate) <= power:
            degree = candidate
        else:
            break
    return degree


def power_for_next_degree(power: int) -> int:
    """Additional power needed to reach the next degree (0 at Degree 100)."""
    degree = degree_from_power(power)
    if degree >= MAX_DEGREE:
        return 0
    return max(0, threshold(degree + 1) - power)


def next_degree(power: int) -> int:
    """The degree that more power would unlock (clamped to 100)."""
    return min(MAX_DEGREE, degree_from_power(power) + 1)


# --- game-mode / T5 limits ---------------------------------------------------


def game_mode_for(player_count: int) -> str:
    """``"solo"`` for 1 player, ``"coop"`` for 2-4."""
    return "solo" if player_count <= 1 else "coop"


def max_extra_t5_count(game_mode: str, *, is_dart: bool) -> int:
    """Max extra T5 sacrifices: solo Dart 1, solo other 0, co-op 9."""
    if game_mode == "coop":
        return COOP_MAX_EXTRA_T5
    return SOLO_DART_MAX_EXTRA_T5 if is_dart else 0


def t5_power_cap_for(game_mode: str, *, is_dart: bool) -> int:
    """Power ceiling reachable from extra T5s for the mode/paragon."""
    return min(
        T5_POWER_CAP,
        max_extra_t5_count(game_mode, is_dart=is_dart) * POWER_PER_EXTRA_T5,
    )


# --- typed models ------------------------------------------------------------


@dataclass(frozen=True)
class ParagonInputs:
    """A set of sacrifice inputs for one paragon calculation."""

    tower: str
    pops: int = 0
    income: int = 0
    cash_spent: int = 0
    slider_cash: int = 0
    tier5_count: int = 0
    upgrade_count: int = 0
    geraldo_totems: int = 0
    player_count: int = 1
    difficulty: str = "medium"

    def as_payload(self) -> dict[str, object]:
        """JSON body for the live API (``tower`` plus non-default fields)."""
        payload: dict[str, object] = {"tower": self.tower}
        for field_name in (
            "pops",
            "income",
            "cash_spent",
            "slider_cash",
            "tier5_count",
            "upgrade_count",
            "geraldo_totems",
        ):
            value = getattr(self, field_name)
            if value:
                payload[field_name] = value
        payload["player_count"] = self.player_count
        payload["difficulty"] = self.difficulty
        return payload


@dataclass(frozen=True)
class AxisBreakdown:
    """One power source's contribution."""

    key: str
    power: int
    max_power: int | None
    capped: bool
    fill_pct: float | None
    note: str = ""


@dataclass(frozen=True)
class ParagonBreakdown:
    """Computed power breakdown and resulting degree (no I/O, no warnings)."""

    degree: int
    total_power: int
    power_for_next_degree: int
    next_degree: int
    pops: AxisBreakdown
    upgrades: AxisBreakdown
    cash: AxisBreakdown
    extra_t5s: AxisBreakdown
    totems: AxisBreakdown
    wasted_cash: int

    @property
    def axes(self) -> tuple[AxisBreakdown, ...]:
        return (self.pops, self.upgrades, self.cash, self.extra_t5s, self.totems)


@dataclass(frozen=True)
class ParagonWarning:
    """A non-fatal advisory (e.g. an input was clamped or ignored)."""

    type: str
    message: str


class SolveStrategy(str, Enum):
    """Reverse-solve objective."""

    BALANCED = "balanced"
    LEAST_CASH = "least_cash"
    LEAST_TIERS = "least_tiers"
    LEAST_POPS = "least_pops"


@dataclass(frozen=True)
class RequirementSolution:
    """A recommended build that reaches (at least) the target degree."""

    target_degree: int
    strategy: SolveStrategy
    inputs: ParagonInputs
    breakdown: ParagonBreakdown
    requires_totems: bool
    note: str = ""


# --- forward computation -----------------------------------------------------


def _fill_pct(power: int, cap: int) -> float:
    return round(power / cap * 100, 2) if cap else 0.0


def compute_breakdown(inputs: ParagonInputs, base_price_value: int) -> ParagonBreakdown:
    """Replicate the API's power math locally for ``inputs`` and ``base_price``."""
    pops_power = min(
        POPS_POWER_CAP,
        (inputs.pops + inputs.income * INCOME_TO_POPS) // POPS_PER_POWER,
    )
    up_power = min(UPGRADES_POWER_CAP, inputs.upgrade_count * POWER_PER_UPGRADE_TIER)
    raw_cash = inputs.cash_spent * (
        CASH_POWER_NUMERATOR / base_price_value
    ) + inputs.slider_cash * (
        CASH_POWER_NUMERATOR / (base_price_value * SLIDER_PREMIUM)
    )
    cash_power = min(CASH_POWER_CAP, math.floor(raw_cash))
    t5_power = min(T5_POWER_CAP, inputs.tier5_count * POWER_PER_EXTRA_T5)
    totems_power = inputs.geraldo_totems * POWER_PER_TOTEM
    total = pops_power + up_power + cash_power + t5_power + totems_power

    if raw_cash > CASH_POWER_CAP and raw_cash > 0:
        used_fraction = CASH_POWER_CAP / raw_cash
        wasted_cash = round(
            (inputs.cash_spent + inputs.slider_cash) * (1 - used_fraction),
        )
    else:
        wasted_cash = 0

    degree = degree_from_power(total)
    rate = CASH_POWER_NUMERATOR / base_price_value
    return ParagonBreakdown(
        degree=degree,
        total_power=total,
        power_for_next_degree=power_for_next_degree(total),
        next_degree=next_degree(total),
        pops=AxisBreakdown(
            "pops",
            pops_power,
            POPS_POWER_CAP,
            pops_power >= POPS_POWER_CAP,
            _fill_pct(pops_power, POPS_POWER_CAP),
            "1 power per 180 pops ($1 income = 4 pops)",
        ),
        upgrades=AxisBreakdown(
            "upgrades",
            up_power,
            UPGRADES_POWER_CAP,
            up_power >= UPGRADES_POWER_CAP,
            _fill_pct(up_power, UPGRADES_POWER_CAP),
            "100 power per upgrade tier (max 100 tiers)",
        ),
        cash=AxisBreakdown(
            "cash",
            cash_power,
            CASH_POWER_CAP,
            cash_power >= CASH_POWER_CAP,
            _fill_pct(cash_power, CASH_POWER_CAP),
            f"~{rate:.3f} power per $1 (slider has a 5% premium)",
        ),
        extra_t5s=AxisBreakdown(
            "extra_t5s",
            t5_power,
            T5_POWER_CAP,
            t5_power >= T5_POWER_CAP,
            _fill_pct(t5_power, T5_POWER_CAP),
            "6,000 power per extra T5 beyond the 3 required",
        ),
        totems=AxisBreakdown(
            "totems",
            totems_power,
            None,
            False,
            None,
            "2,000 power per Geraldo totem (uncapped)",
        ),
        wasted_cash=wasted_cash,
    )


def validate_inputs(inputs: ParagonInputs) -> list[ParagonWarning]:
    """Local mirror of the API's advisory rules (clamps / ignored fields).

    Returns warnings; it never raises. Unknown towers are reported as a
    ``unknown_tower`` warning so callers can decide whether to hard-error.
    """
    warnings: list[ParagonWarning] = []
    paragon = resolve_paragon(inputs.tower)
    if paragon is None:
        warnings.append(
            ParagonWarning(
                "unknown_tower",
                f"Unknown tower/paragon: {inputs.tower!r}.",
            ),
        )
        return warnings

    mode = game_mode_for(inputs.player_count)
    if inputs.player_count < 1 or inputs.player_count > 4:
        warnings.append(
            ParagonWarning(
                "player_count",
                "player_count must be 1-4; treating out-of-range as nearest.",
            ),
        )
    if inputs.tier5_count > 0:
        if mode == "solo" and not paragon.is_dart:
            warnings.append(
                ParagonWarning(
                    "extra_t5_ignored",
                    "Extra T5s are ignored in solo for any paragon other than Dart Monkey.",
                ),
            )
        else:
            limit = max_extra_t5_count(mode, is_dart=paragon.is_dart)
            if inputs.tier5_count > limit:
                warnings.append(
                    ParagonWarning(
                        "extra_t5_clamped",
                        f"Extra T5s clamped to {limit} for this mode/paragon.",
                    ),
                )
    if inputs.upgrade_count > MAX_UPGRADE_TIERS:
        warnings.append(
            ParagonWarning(
                "upgrades_capped",
                f"upgrade_count above {MAX_UPGRADE_TIERS} adds no power (10,000 cap).",
            ),
        )
    slider_cap = int(SLIDER_MAX_BASE_MULTIPLE * base_price(paragon, inputs.difficulty))
    if inputs.slider_cash > slider_cap:
        warnings.append(
            ParagonWarning(
                "slider_clamped",
                f"slider_cash above ${slider_cap:,} (3.15x base) is clamped in-game.",
            ),
        )
    return warnings


# --- reverse solver ----------------------------------------------------------


def _alloc_to_inputs(
    paragon: Paragon,
    alloc: dict[str, int],
    *,
    player_count: int,
    difficulty: str,
    base_price_value: int,
    max_t5: int,
) -> ParagonInputs:
    """Convert a per-axis power allocation to concrete inputs (rounding up)."""
    return ParagonInputs(
        tower=paragon.paragon_id,
        pops=alloc["pops"] * POPS_PER_POWER,
        cash_spent=math.ceil(alloc["cash"] * base_price_value / CASH_POWER_NUMERATOR),
        tier5_count=(
            min(max_t5, math.ceil(alloc["t5"] / POWER_PER_EXTRA_T5))
            if alloc["t5"]
            else 0
        ),
        upgrade_count=math.ceil(alloc["upgrades"] / POWER_PER_UPGRADE_TIER),
        geraldo_totems=(
            math.ceil(alloc["totems"] / POWER_PER_TOTEM) if alloc["totems"] else 0
        ),
        player_count=player_count,
        difficulty=difficulty,
    )


def solve_requirements(
    paragon: Paragon,
    target_degree: int,
    strategy: SolveStrategy,
    *,
    player_count: int = 1,
    difficulty: str = "medium",
) -> RequirementSolution:
    """Find a build reaching ``target_degree`` under the chosen ``strategy``.

    Works in power space, then converts to integer inputs (rounded up, so the
    result always reaches at least the target). Geraldo totems fill **only** the
    remainder that the capped axes cannot supply at their collective maximum —
    they never displace a capped axis (so "least cash/tiers/pops" stays a real
    minimum instead of collapsing to zero via unlimited totems).
    """
    target = max(1, min(MAX_DEGREE, target_degree))
    need = threshold(target)
    mode = game_mode_for(player_count)
    is_dart = paragon.is_dart
    bp = base_price(paragon, difficulty)
    max_t5 = max_extra_t5_count(mode, is_dart=is_dart)
    t5_cap = t5_power_cap_for(mode, is_dart=is_dart)

    caps: dict[str, int] = {
        "pops": POPS_POWER_CAP,
        "upgrades": UPGRADES_POWER_CAP,
        "cash": CASH_POWER_CAP,
        "t5": t5_cap,
    }
    capped_total = sum(caps.values())
    alloc: dict[str, int] = {"pops": 0, "upgrades": 0, "cash": 0, "t5": 0, "totems": 0}

    if strategy is SolveStrategy.BALANCED:
        three_cap = POPS_POWER_CAP + UPGRADES_POWER_CAP + CASH_POWER_CAP
        fraction = min(1.0, need / three_cap)
        alloc["pops"] = math.ceil(fraction * POPS_POWER_CAP)
        alloc["upgrades"] = math.ceil(fraction * UPGRADES_POWER_CAP)
        alloc["cash"] = math.ceil(fraction * CASH_POWER_CAP)
        covered = alloc["pops"] + alloc["upgrades"] + alloc["cash"]
        if need > covered:
            alloc["t5"] = min(t5_cap, need - covered)
            covered += alloc["t5"]
        if need > covered:
            alloc["totems"] = need - covered
    else:
        axis = {
            SolveStrategy.LEAST_CASH: "cash",
            SolveStrategy.LEAST_TIERS: "upgrades",
            SolveStrategy.LEAST_POPS: "pops",
        }[strategy]
        if need > capped_total:
            for key in ("pops", "upgrades", "cash", "t5"):
                alloc[key] = caps[key]
            alloc["totems"] = need - capped_total
        else:
            min_axis_power = max(0, need - (capped_total - caps[axis]))
            alloc[axis] = min_axis_power
            remaining = need - min_axis_power
            for key in ("pops", "upgrades", "t5", "cash"):
                if key == axis or remaining <= 0:
                    continue
                take = min(caps[key], remaining)
                alloc[key] = take
                remaining -= take

    inputs = _alloc_to_inputs(
        paragon,
        alloc,
        player_count=player_count,
        difficulty=difficulty,
        base_price_value=bp,
        max_t5=max_t5,
    )
    breakdown = compute_breakdown(inputs, bp)
    # Belt-and-suspenders: integer rounding only overshoots, but guarantee the
    # target is met before returning.
    guard = 0
    while breakdown.degree < target and guard < 64:
        inputs = replace(inputs, pops=inputs.pops + POPS_PER_POWER)
        breakdown = compute_breakdown(inputs, bp)
        guard += 1

    return RequirementSolution(
        target_degree=target,
        strategy=strategy,
        inputs=inputs,
        breakdown=breakdown,
        requires_totems=inputs.geraldo_totems > 0,
    )


__all__ = [
    "BASE_PRICES_MEDIUM",
    "PARAGONS",
    "AxisBreakdown",
    "Paragon",
    "ParagonBreakdown",
    "ParagonInputs",
    "ParagonWarning",
    "RequirementSolution",
    "SolveStrategy",
    "base_price",
    "compute_breakdown",
    "degree_from_power",
    "game_mode_for",
    "max_extra_t5_count",
    "next_degree",
    "paragon_surfaces",
    "power_for_next_degree",
    "resolve_paragon",
    "solve_requirements",
    "t5_power_cap_for",
    "threshold",
    "validate_inputs",
]
