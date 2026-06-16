"""Tests for the deterministic BTD6 capability-roster floor (AI §7 new family).

``btd6_context_service.deterministic_capability_roster_reply`` fronts the
authoritative ``btd6_capability_service`` rosters ("which towers pop lead / detect
camo") as a pre-emptive floor before the model — the BUG-0009 wrong-assembly class:
every tower name is grounded, so a mis-*roster* slips past the value-only
faithfulness guard. These tests pin that it fires on the roster shape, owns the
right capability, honours the base-vs-upgraded scope, and defers cleanly.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import (  # noqa: E402
    btd6_capability_service,
    btd6_context_service,
    btd6_data_service,
)

_reply = btd6_context_service.deterministic_capability_roster_reply


@pytest.fixture(autouse=True)
def _reset_dataset_cache():
    btd6_data_service.reset_cache()
    yield
    btd6_data_service.reset_cache()


@pytest.mark.parametrize(
    ("phrase", "capability", "label"),
    [
        ("which towers can pop lead without upgrades", "lead_popping", "pop Lead"),
        ("what towers detect camo", "camo_detection", "detect Camo"),
        ("which monkeys can pop purple", "purple_popping", "pop Purple"),
        ("which towers pop black at base", "black_popping", "pop Black"),
        ("what towers can pop white", "white_popping", "pop White"),
    ],
)
def test_fires_and_owns_the_right_capability(phrase, capability, label):
    reply = _reply(phrase)
    assert reply is not None
    assert label in reply
    # The roster IS the service's answer — same count, same names (it owns it).
    hits = btd6_capability_service.towers_with_capability(capability, unupgraded=True)
    assert f"({len(hits)})" in reply
    for hit in hits:
        assert hit.canonical in reply


def test_base_scope_is_the_default_and_labelled():
    reply = _reply("which towers detect camo")
    assert reply is not None
    assert "without upgrades (base tier)" in reply


def test_with_upgrades_signal_flips_to_the_full_roster():
    base = btd6_capability_service.towers_with_capability("lead_popping", unupgraded=True)
    upgraded = btd6_capability_service.towers_with_capability(
        "lead_popping",
        unupgraded=False,
    )
    reply = _reply("which towers can pop lead with upgrades")
    assert reply is not None
    assert "any tier, earliest shown" in reply
    # The upgraded roster is a superset (more towers gain lead via an upgrade).
    assert len(upgraded) > len(base)
    assert f"({len(upgraded)})" in reply


def test_paragon_camo_roster_splits_yes_no():
    reply = _reply("which paragons detect camo")
    assert reply is not None
    assert "paragons and Camo detection" in reply
    assert "Detect Camo innately" in reply
    assert "Need external Camo support" in reply
    # Glaive Dominus detects camo innately; Herald of Everfrost does not (curated).
    assert "Glaive Dominus" in reply


def test_paragon_non_camo_capability_defers():
    # Only camo is verified per-paragon; a paragon lead-popping question is not a
    # roster the service can answer authoritatively, so the floor defers.
    assert _reply("which paragons can pop lead") is None


@pytest.mark.parametrize(
    "phrase",
    [
        "does the dartling gunner detect camo",  # single-entity yes/no, not a roster
        "which tower is best at popping lead",  # strategy/opinion
        "what is the navarch of the seas paragon",  # paragon lookup, no capability cue
        "how much does a 0-4-1 desperado cost on impoppable",  # cost lookup
        "the white monkey skin looks cool",  # colour word without a pop verb
        "which map has the most water",  # roster shape, but no capability cue
        "",
    ],
)
def test_defers_outside_the_roster_shape(phrase):
    assert _reply(phrase) is None


def test_served_through_the_dispatcher():
    # The floor rides the shared _BTD6_LIST_BUILDERS seam (no integration change).
    assert (
        btd6_context_service.deterministic_btd6_list_reply(
            "which towers can pop lead without upgrades",
        )
        is not None
    )
