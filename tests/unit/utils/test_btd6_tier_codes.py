"""Unit tests for utils.btd6.tier_codes — the canonical crosspath-code logic."""

from __future__ import annotations

import pytest

from utils.btd6 import tier_codes as tc


def test_is_valid_code():
    assert tc.is_valid_code("000")
    assert tc.is_valid_code("520")
    assert not tc.is_valid_code("00")  # too short
    assert not tc.is_valid_code("0a0")  # non-digit
    assert not tc.is_valid_code("060")  # 6 is out of range
    assert not tc.is_valid_code(None)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "code",
    ["000", "500", "050", "005", "520", "250", "220", "202", "022", "140", "014"],
)
def test_legal_codes(code):
    assert tc.is_legal(code)


@pytest.mark.parametrize(
    "code", ["111", "530", "350", "055", "333", "225", "252", "115"]
)
def test_illegal_codes(code):
    # >2 nonzero paths, or a second path above tier 2 — impossible in-game.
    assert not tc.is_legal(code)


def test_classification():
    assert tc.is_base("000")
    assert tc.is_single_path("500") and not tc.is_crosspath("500")
    assert tc.is_crosspath("520") and not tc.is_single_path("520")
    assert tc.nonzero_count("202") == 2


def test_primary_path_highest_tier_then_lowest_index():
    assert tc.primary_path("000") is None
    assert tc.primary_path("050") == 2
    assert tc.primary_path("025") == 3  # tier-5 path 3 is the main
    assert tc.primary_path("520") == 1  # tier-5 path 1
    assert tc.primary_path("202") == 1  # tie at tier 2 -> lowest index (the bug fix)
    assert tc.primary_tier("025") == 5


def test_format_code():
    assert tc.format_code("202") == "2-0-2"
    assert tc.format_code("000") == "0-0-0"


def test_candidate_and_preferred_parent():
    assert set(tc.candidate_parents("220")) == {"200", "020"}
    assert set(tc.candidate_parents("025")) == {"020", "005"}
    assert tc.preferred_parent(["200", "020"]) == "200"  # tie tier -> lower path
    assert tc.preferred_parent(["005", "050"]) == "050"  # tie tier-5 -> lower path
    assert tc.preferred_parent(["500", "010"]) == "500"  # higher tier wins


def test_ordered_codes_canonical_first():
    ordered = tc.ordered_codes(["202", "000", "500", "210"])
    assert ordered[0] == "000"
    assert ordered.index("500") < ordered.index("202")  # 16 canonical before crosspaths
    assert set(ordered) == {"202", "000", "500", "210"}
