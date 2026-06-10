"""Render a mode's game-sourced ``rules`` block as short human clauses.

The modes cutover (``parse_gamedata.py --modes``) attaches a structured
``rules`` dict to each mapped mode — starting cash/lives, start/end rounds,
cost/speed/income multipliers, MOAB-health multiplier, locked towers/classes,
and the no-continue/no-sell/no-MK/no-income flags — parsed from the dump's
``Mods/<mode>.json`` ``mutatorMods[]``. This module is the one formatter both
surfaces share (the AI ``btd6_mode_lookup`` payload stays the raw dict; the
menu's modes embed shows these clauses), so the wording can't drift per-panel.

Pure / stdlib-only, so services, cogs, and views can all use it without
crossing a layer boundary.
"""

from __future__ import annotations

import re
from typing import Any

# Internal tower ids in ``locked_towers`` are CamelCase game codes
# ("BananaFarm"); split them into the display name rather than carrying a
# hand-maintained id->name table for the one id the data uses today.
_CAMEL_SPLIT = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _tower_label(internal_id: str) -> str:
    return _CAMEL_SPLIT.sub(" ", internal_id)


def _fmt_num(value: Any) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return f"{value:,}" if isinstance(value, int) else f"{value:g}"
    return str(value)


def _fmt_mult(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"×{value:g}" if isinstance(value, (int, float)) else f"×{value}"


def summarize_mode_rules(rules: dict[str, Any]) -> list[str]:
    """The rules dict -> ordered, embed-ready clauses (empty list when none).

    Every key the modes cutover can emit is handled; an unknown future key is
    rendered as ``key=value`` rather than silently dropped, so new dump data
    is visible (if unpolished) instead of dark.
    """
    if not rules:
        return []
    clauses: list[str] = []
    handled: set[str] = set()

    def take(key: str) -> Any:
        handled.add(key)
        return rules.get(key)

    cash = take("starting_cash")
    if cash is not None:
        clauses.append(f"${_fmt_num(cash)} starting cash")
    lives = take("starting_lives")
    if lives is not None:
        clauses.append(f"{_fmt_num(lives)} {'life' if lives == 1 else 'lives'}")
    start, end = take("start_round"), take("end_round")
    if start is not None and end is not None:
        clauses.append(f"rounds {start}–{end}")
    elif start is not None:
        clauses.append(f"starts at round {start}")
    elif end is not None:
        clauses.append(f"ends at round {end}")
    if take("round_set") == "AlternateRoundSet":
        clauses.append("Alternate Bloons Rounds")
    if take("reverse"):
        clauses.append("reversed track")
    cost = take("cost_multiplier")
    if cost is not None:
        clauses.append(f"prices {_fmt_mult(cost)}")
    speed = take("speed_multiplier")
    if speed is not None:
        clauses.append(f"bloon speed {_fmt_mult(speed)}")
    moab = take("moabs_health_multiplier")
    if moab is not None:
        clauses.append(f"MOAB-class health {_fmt_mult(moab)}")
    income = take("income_multiplier")
    if take("no_income"):
        clauses.append("no income from pops")
    elif income is not None:
        clauses.append(f"income {_fmt_mult(income)}")
    locked_classes = take("locked_tower_classes") or []
    if locked_classes:
        clauses.append(f"{'/'.join(locked_classes)} towers locked")
    locked = take("locked_towers") or []
    if locked:
        clauses.append(
            ", ".join(_tower_label(t) for t in locked)
            + (" locked" if len(locked) == 1 else " towers locked"),
        )
    if take("no_continues"):
        clauses.append("no continues")
    if take("no_selling"):
        clauses.append("no selling")
    if take("no_monkey_knowledge"):
        clauses.append("no Monkey Knowledge")
    for key in sorted(rules.keys() - handled):
        clauses.append(f"{key}={rules[key]}")
    return clauses
