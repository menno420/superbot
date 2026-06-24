"""Deterministic paragon Elite-Boss damage-multiplier floor.

Owner-reported (2026-06-24): "elite boss multiplier for paragons" refused with
"no verified data", and the named-paragon form ("for the dart paragon") got
faithfulness-rejected. Both are now owned by a deterministic floor — the answer
is a global runtime constant (paragons deal ×2 their boss damage to Elite Bosses,
every degree), so it can be served without the model and can't refuse.

The ×2 / ×4.5 figures are pinned to ``utils.btd6.paragon_degrees`` so the reply
can't drift from the shipped constant.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_context_service  # noqa: E402
from utils.btd6 import paragon_degrees  # noqa: E402

_reply = btd6_context_service.deterministic_paragon_elite_reply


@pytest.mark.parametrize(
    "phrase",
    [
        "whats the elite boss damage multiplier for paragons",
        "what's the elite boss multiplier for the dart paragon",
        "elite boss bonus for the glaive dominus paragon",
        "how much extra damage do paragons do to elite bosses, doubled?",
    ],
)
def test_fires_on_general_and_named_paragon_elite_questions(phrase):
    reply = _reply(phrase)
    assert reply is not None
    assert "double" in reply.lower()


def test_values_match_the_shipped_constant():
    reply = _reply("elite boss damage multiplier for paragons")
    assert reply is not None
    # x2 at degree 1, x4.5 at degree 100 — from paragon_degrees, not hardcoded.
    assert f"×{paragon_degrees.elite_boss_multiplier(1):g}" in reply  # ×2
    assert f"×{paragon_degrees.elite_boss_multiplier(100):g}" in reply  # ×4.5
    assert f"×{paragon_degrees.boss_multiplier(100):g}" in reply  # ×2.25
    # The key facts the owner needed: global + runtime constant.
    assert "every degree" in reply.lower()
    assert "not per-paragon" in reply.lower()


def test_defers_without_an_elite_cue():
    # Boss multiplier (non-elite) is a different question — not ours.
    assert _reply("what's the boss multiplier for paragons") is None


def test_defers_without_paragon_context():
    # "elite boss damage" with no paragon (worded or resolvable) is not ours —
    # it belongs to the boss floors / model.
    assert _reply("how much damage does an elite boss take") is None


def test_defers_without_a_damage_or_multiplier_cue():
    # "elite lych for paragons to fight" — no multiplier/damage cue.
    assert _reply("which paragon is best against an elite lych") is None


def test_dispatcher_routes_the_elite_reply():
    reply = btd6_context_service.deterministic_btd6_list_reply(
        "whats the elite boss damage multiplier for paragons",
    )
    assert reply is not None
    assert "Elite-Boss" in reply
