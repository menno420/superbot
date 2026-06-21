"""creature_battle render — the PvP outcome embed (pure presentation).

Builds a real :class:`PvpResult` from the engine, then asserts the embed surfaces
both rosters, the winner, and KO highlights — and marks fainted creatures.
"""

from __future__ import annotations

import random
from types import SimpleNamespace

from services.creature_battle_service import PvpResult
from utils.creatures import CREATURES, NORMALIZED_LEVEL, build_team, resolve_battle
from views.creature_battle.render import build_result_embed


def _user(name: str):
    return SimpleNamespace(display_name=name, mention=f"@{name}")


def _two_teams():
    by_el: dict[str, object] = {}
    for c in CREATURES:
        by_el.setdefault(c.element, c)
    creatures = list(by_el.values())
    mid = len(creatures) // 2
    team_a = build_team(creatures[:mid], NORMALIZED_LEVEL)
    team_b = build_team(creatures[mid:], NORMALIZED_LEVEL)
    return team_a, team_b


def _result() -> PvpResult:
    team_a, team_b = _two_teams()
    roster_a, roster_b = tuple(team_a), tuple(team_b)
    outcome = resolve_battle(team_a, team_b, rng=random.Random(3))
    return PvpResult(outcome=outcome, team_a=roster_a, team_b=roster_b)


def test_embed_lists_both_teams_and_a_winner():
    result = _result()
    embed = build_result_embed(_user("Ada"), _user("Bo"), result)
    field_names = [f.name for f in embed.fields]
    assert any("Ada" in n for n in field_names)
    assert any("Bo" in n for n in field_names)
    winner_field = next(f for f in embed.fields if f.name == "Winner")
    expected = "@Ada" if result.a_won else "@Bo"
    assert expected in winner_field.value


def test_embed_marks_fainted_creatures():
    result = _result()
    embed = build_result_embed(_user("Ada"), _user("Bo"), result)
    rosters = " ".join(f.value for f in embed.fields if f.name.endswith("team"))
    # At least one side took casualties in a resolved 6v6-ish bout.
    assert "💀" in rosters


def test_highlights_field_present():
    result = _result()
    embed = build_result_embed(_user("Ada"), _user("Bo"), result)
    assert any(f.name == "Highlights" for f in embed.fields)
