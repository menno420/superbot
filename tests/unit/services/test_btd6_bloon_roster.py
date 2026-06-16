"""Tests for the deterministic BTD6 bloon-roster floor (AI §7 new family).

``btd6_context_service.deterministic_bloon_roster_reply`` fronts the committed
bloon fields ("what are all the MOAB-class bloons", "which bloons are immune to
sharp") as a pre-emptive floor before the model — the wrong-assembly class on the
bloon side of the matchup. The sibling roster floor (deterministic_roster_reply)
covers heroes/towers/paragons/maps but not bloons. These tests pin firing, the
roster content (derived from the dataset), and clean deferral.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_context_service, btd6_data_service  # noqa: E402

_reply = btd6_context_service.deterministic_bloon_roster_reply


@pytest.fixture(autouse=True)
def _reset_dataset_cache():
    btd6_data_service.reset_cache()
    yield
    btd6_data_service.reset_cache()


def _moab_class_canonicals() -> list[str]:
    return [
        b.canonical
        for b in btd6_data_service.get_dataset().bloons
        if b.category == "moab_class"
    ]


@pytest.mark.parametrize(
    "phrase",
    [
        "what are all the moab class bloons",
        "list every blimp in btd6",
        "how many moab class bloons are there",
        "name all the blimps",
    ],
)
def test_moab_class_enumeration_owns_the_blimp_tier(phrase):
    reply = _reply(phrase)
    assert reply is not None
    expected = _moab_class_canonicals()
    assert f"({len(expected)})" in reply
    for name in expected:
        assert name in reply
    # The data set's blimp tier is exactly these five — pin the count so a
    # mis-roster (dropping/adding one) fails here.
    assert len(expected) == 5


@pytest.mark.parametrize(
    ("phrase", "label", "expected"),
    [
        ("which bloons are immune to sharp", "Sharp", {"Lead Bloon", "DDT"}),
        (
            "what bloons are immune to explosion",
            "Explosion",
            {"Black Bloon", "Zebra Bloon", "DDT"},
        ),
        (
            "which bloons resist cold",
            "Cold",
            {"White Bloon", "Lead Bloon", "Zebra Bloon", "DDT"},
        ),
        ("which bloons are immune to acid", "Acid", {"Glass Bloon"}),
    ],
)
def test_immunity_roster_matches_the_committed_data(phrase, label, expected):
    reply = _reply(phrase)
    assert reply is not None
    assert f"immune to {label} damage" in reply
    for name in expected:
        assert name in reply
    # Cross-check against the dataset so the test never drifts from the source.
    derived = {
        b.canonical
        for b in btd6_data_service.get_dataset().bloons
        if b.category != "modifier" and label in (b.immune_to or ())
    }
    assert derived == expected


def test_modifier_pseudo_bloons_are_excluded():
    # "camo"/"fortified"/"regrow" are modifier rows, never listed as bloons.
    reply = _reply("what are all the moab class bloons")
    assert reply is not None
    for marker in ("Camo property", "Fortified property", "Regrow property"):
        assert marker not in reply


@pytest.mark.parametrize(
    "phrase",
    [
        "what is a moab",  # single-bloon lookup, not a roster
        "is the lead bloon immune to sharp",  # single-entity yes/no
        "how much health does a bfb have",  # stat lookup
        "which tower is best against moabs",  # strategy + tower subject
        "which towers can pop lead without upgrades",  # tower capability, not bloons
        "what is the strongest bloon",  # superlative/opinion, no enumeration
        "",
    ],
)
def test_defers_outside_the_roster_shape(phrase):
    assert _reply(phrase) is None


def test_served_through_the_dispatcher():
    assert (
        btd6_context_service.deterministic_btd6_list_reply(
            "what are all the moab class bloons",
        )
        is not None
    )
