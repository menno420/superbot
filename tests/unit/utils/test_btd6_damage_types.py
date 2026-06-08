"""Tests for the BTD6 damage-type decoder (port of Template:BTD6 dt)."""

from __future__ import annotations

import pytest

from utils.btd6.damage_types import (
    decode_damage_type,
    immunities_for_bloon_properties,
)

# (immuneBloonProperties, expected name, expected cannot_pop) from Template:BTD6 dt.
CASES = [
    (0, "Normal", "Can damage any Bloon type"),
    (1, "Shatter", "Cannot damage Lead"),
    (2, "Explosion", "Cannot damage Black"),
    (4, "Glacier", "Cannot damage White"),
    (5, "Cold", "Cannot damage Lead or White"),
    (8, "Fire", "Cannot damage Purple"),
    (12, "Frigid", "Cannot damage White or Purple"),
    (17, "Sharp", "Cannot damage Lead or frozen"),
    (64, "Acid", "Cannot damage Glass"),
    (72, "Plasma", "Cannot damage Purple or Glass"),
    (73, "Energy", "Cannot damage Lead, Purple, or Glass"),
]


@pytest.mark.parametrize(("value", "name", "cannot_pop"), CASES)
def test_known_damage_types(value, name, cannot_pop):
    dt = decode_damage_type(value)
    assert dt.name == name
    assert dt.cannot_pop == cannot_pop
    assert dt.is_known


def test_bomb_shooter_signature_values():
    # Base bomb explosion (immuneBloonProperties 2) cannot pop Black...
    assert decode_damage_type(2).name == "Explosion"
    assert not decode_damage_type(2).pops_everything
    # ...but Bloon Crush (0) flips to Normal and pops everything.
    assert decode_damage_type(0).pops_everything


def test_unknown_value_is_flagged_not_guessed():
    dt = decode_damage_type(999)
    assert not dt.is_known
    assert dt.name == "Unknown"


# (bloonProperties bitflag, expected immunity set) — the dump-sourced inverse,
# pinned against the curated bloonswiki ``immune_to`` lists it reproduces.
IMMUNITY_CASES = [
    (0, set()),  # Red/Blue/... : no immunities
    (1, {"Shatter", "Cold", "Energy", "Sharp"}),  # Lead
    (2, {"Explosion"}),  # Black
    (4, {"Glacier", "Cold", "Frigid"}),  # White
    (8, {"Fire", "Energy", "Frigid", "Plasma"}),  # Purple
    (6, {"Explosion", "Glacier", "Cold", "Frigid"}),  # Zebra = Black | White
]


@pytest.mark.parametrize(("props", "expected"), IMMUNITY_CASES)
def test_immunities_for_bloon_properties_matches_curated(props, expected):
    result = immunities_for_bloon_properties(props)
    assert set(result) == expected
    # Deterministic, de-duplicated (Energy comes from masks 9 and 73), and never
    # emits Normal/Unknown.
    assert len(result) == len(set(result))
    assert "Normal" not in result and "Unknown" not in result


def test_zebra_immunity_is_the_union_of_its_property_bits():
    # The bitflag composes: Zebra (6 = 2|4) is immune to exactly Black's ∪ White's.
    black = set(immunities_for_bloon_properties(2))
    white = set(immunities_for_bloon_properties(4))
    assert set(immunities_for_bloon_properties(6)) == black | white
