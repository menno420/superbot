"""BTD6 late-game/freeplay MOAB-class health scaling.

Round-relative bloon health scaling is NOT in the BTD Mod Helper game data dump
(round files store only composition + timing; ``BloonModel`` stores base
``maxHealth`` only). BTD6 applies a runtime ramp to MOAB-class bloons: +2% of base
HP per round from round 81, piecewise-linear, so ``v(100) = 1.40`` and a BAD first
spawns on round 100 already at 28,000 HP. The curve is curated in
``bloon_scaling.json`` (sibling of ``round_xp.json``). These tests pin the loader,
the multiplier math, the per-bloon scaled health, and the deterministic
"HP of <bloon> at round N" reply against the cross-verified anchor (BAD = 28,000 @
r100, three independent sources: Late Game and Freeplay / BAD wiki / topper64).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).parents[3]
_DISBOT = _REPO / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_context_service  # noqa: E402
from services import btd6_data_service  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_cache():
    btd6_data_service.reset_cache()
    yield
    btd6_data_service.reset_cache()


# --- the runtime loader -------------------------------------------------------


def test_dataset_loads_scaling_curve():
    dataset = btd6_data_service.get_dataset()
    assert dataset.moab_health_scaling  # non-empty
    assert dataset.moab_health_start_round == 81
    assert "bloon_scaling" in dataset.sources


def test_committed_json_anchor_is_28000_at_round_100():
    # The verified cross-check that motivated this work: a BAD first appears on
    # round 100 at 28,000 HP. If the committed curve or base health drifts so this
    # no longer holds, fail here rather than in production.
    committed = json.loads(
        (_DISBOT / "data" / "btd6" / "bloon_scaling.json").read_text("utf-8"),
    )
    assert committed["moab_class_health"]["start_round"] == 81
    assert btd6_data_service.bloon_health_at_round("bad", 100) == 28000


# --- the multiplier math ------------------------------------------------------


@pytest.mark.parametrize(
    ("rnd", "expected"),
    [
        (1, 1.0),
        (80, 1.0),  # no ramp through round 80
        (81, 1.02),  # +2% of base per round kicks in
        (100, 1.40),  # the verified anchor (BAD 20k -> 28k)
        (101, 1.60),  # step up into the next bracket
        (150, 2.58),
        (151, 3.00),
    ],
)
def test_moab_class_health_multiplier(rnd: int, expected: float):
    assert btd6_data_service.moab_class_health_multiplier(rnd) == pytest.approx(
        expected
    )


# --- per-bloon scaled health --------------------------------------------------


def test_bad_scaled_health_standard_and_fortified():
    assert btd6_data_service.bloon_health_at_round("bad", 100) == 28000
    assert btd6_data_service.bloon_health_at_round("bad", 100, fortified=True) == 56000
    # Through round 80 the base is unchanged.
    assert btd6_data_service.bloon_health_at_round("bad", 80) == 20000


def test_other_moab_class_bloons_scale():
    assert btd6_data_service.bloon_health_at_round("zomg", 100) == 5600  # 4000 * 1.4
    assert btd6_data_service.bloon_health_at_round("moab", 100) == 280  # 200 * 1.4


def test_non_moab_bloon_does_not_scale():
    # Regular bloons keep their base health on every round (only MOAB-class ramp;
    # ceramics instead become superceramics, which is a swap, not a multiplier).
    red = btd6_data_service.get_bloon("red")
    assert red is not None
    assert btd6_data_service.bloon_health_at_round("red", 50) == red.health
    assert btd6_data_service.bloon_health_at_round("red", 200) == red.health


def test_unknown_bloon_returns_none():
    assert btd6_data_service.bloon_health_at_round("not_a_bloon", 100) is None


# --- the deterministic floor reply --------------------------------------------


def test_reply_owns_bad_at_round_100():
    reply = btd6_context_service.deterministic_bloon_health_reply(
        "how much health does a BAD have on round 100",
    )
    assert reply is not None
    assert "28,000" in reply
    assert "20,000" in reply  # names the base too


def test_reply_handles_fortified():
    reply = btd6_context_service.deterministic_bloon_health_reply(
        "hp of a fortified bad on r100",
    )
    assert reply is not None
    assert "56,000" in reply


def test_reply_defers_without_a_round_number():
    # The base "how much HP does a BAD have" question stays with the model (which
    # answers the 20,000 base from grounding) — the floor only owns round-specific.
    assert (
        btd6_context_service.deterministic_bloon_health_reply(
            "how much health does a BAD have",
        )
        is None
    )


def test_reply_defers_without_a_health_cue():
    assert (
        btd6_context_service.deterministic_bloon_health_reply(
            "what spawns on round 100",
        )
        is None
    )


def test_reply_states_non_moab_bloons_do_not_scale():
    reply = btd6_context_service.deterministic_bloon_health_reply(
        "how much health does a red bloon have on round 80",
    )
    assert reply is not None
    assert "every round" in reply.lower()
