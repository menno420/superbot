"""Deathmatch reads the cross-game EffectiveStats seam (combat gear).

Pins that equipped combat gear tilts a duel through ``_Duel`` — max HP from
``max_health``, attack from ``damage``, flat reduction from ``defense`` — while
a bare fighter (no stats passed) duels at exactly the historical baseline.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from cogs.deathmatch_cog import BASE_ATTACK_DAMAGE, BASE_HP, _Duel
from utils.equipment import EffectiveStats


def _player(id_: int, name: str = "P") -> SimpleNamespace:
    return SimpleNamespace(id=id_, display_name=name, mention=f"<@{id_}>", bot=False)


def test_bare_duel_matches_historical_baseline():
    # No stats passed → exactly the pre-gear 100 HP duel (backward compatible
    # with every existing caller/test).
    duel = _Duel(_player(1), _player(2))
    assert duel.player1_max_hp == BASE_HP
    assert duel.player2_max_hp == BASE_HP
    assert duel.player1_hp == BASE_HP


def test_max_health_gear_raises_starting_hp():
    duel = _Duel(_player(1), _player(2), p1_stats=EffectiveStats(max_health=20))
    assert duel.player1_max_hp == BASE_HP + 20
    assert duel.player1_hp == BASE_HP + 20
    assert duel.player2_max_hp == BASE_HP  # opponent unaffected


def test_weapon_damage_adds_to_attack():
    p1, p2 = _player(1), _player(2)
    duel = _Duel(p1, p2, p1_stats=EffectiveStats(damage=6))
    with patch("cogs.deathmatch_cog.random.random", return_value=0.5):  # no crit
        damage, critical = duel.attack(p1.id, p2.id)
    assert not critical
    assert damage == BASE_ATTACK_DAMAGE + 6
    assert duel.player2_hp == duel.player2_max_hp - (BASE_ATTACK_DAMAGE + 6)


def test_armor_defense_reduces_incoming_damage():
    p1, p2 = _player(1), _player(2)
    duel = _Duel(p1, p2, p2_stats=EffectiveStats(defense=4))
    with patch("cogs.deathmatch_cog.random.random", return_value=0.5):  # no crit
        damage, _ = duel.attack(p1.id, p2.id)
    assert damage == BASE_ATTACK_DAMAGE - 4


def test_defense_never_reduces_an_attack_below_one():
    p1, p2 = _player(1), _player(2)
    duel = _Duel(p1, p2, p2_stats=EffectiveStats(defense=999))
    with patch("cogs.deathmatch_cog.random.random", return_value=0.5):
        damage, _ = duel.attack(p1.id, p2.id)
    assert damage == 1


def test_active_defend_and_armor_stack():
    p1, p2 = _player(1), _player(2)
    duel = _Duel(p1, p2, p2_stats=EffectiveStats(defense=2))
    duel.defend(p2.id)  # p2 braces for the next hit
    with patch("cogs.deathmatch_cog.random.random", return_value=0.5):
        damage, _ = duel.attack(p1.id, p2.id)
    # base 15 → halved by the defend stance to 7 → -2 armor = 5.
    assert damage == (BASE_ATTACK_DAMAGE // 2) - 2
