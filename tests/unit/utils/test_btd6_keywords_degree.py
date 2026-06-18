"""Pin: ``degree_in_text`` reads a paragon degree (1-100) from a query.

BUG-0015 (live miss 2026-06-16): SuperBot misread the "d67" shorthand for
"degree 67" as the upgrade path "0-6-7". The shared cue here is the parse half
of the fix (the router routes on it, the grounding leg surfaces the per-degree
stats). These pin both that it RECOGNISES the forms players use and that it
does NOT mistake a round / version / dice / temperature token for a degree.
"""

from __future__ import annotations

import pytest

from utils.btd6.keywords import degree_in_text


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("whats the damage of a d67 dart", 67),  # the bare "d67" shorthand
        ("a d67 dart praragon", 67),  # the verbatim screenshot phrasing
        ("dart paragon at degree 67", 67),  # spelled "degree N"
        ("degrees 5 ace", 5),  # plural "degrees N"
        ("ace paragon degree-80", 80),  # hyphenated "degree-80"
        ("deg 42 glaive dominus", 42),  # "deg N" abbreviation
        ("deg.42 stats", 42),  # "deg.N"
        ("d1 dart paragon", 1),  # the lower bound
        ("dart paragon at d100", 100),  # the upper bound (MAX_DEGREE)
    ],
)
def test_recognises_the_degree_forms_players_type(text, expected):
    assert degree_in_text(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "d255 dart paragon",  # above the 1-100 range
        "degree 0 dart",  # below the 1-100 range
        "how much cash on r67",  # a ROUND (r-shorthand), not a degree
        "on game version v55 the buff changed",  # a version, not a degree
        "i rolled 5d6 for damage",  # tabletop dice: the "d" is mid-token
        "please add 7 more towers",  # "add 7" — "d" is not at a word boundary
        "its 67 degrees outside",  # temperature: "degrees" AFTER the number
        "what is a paragon of virtue",  # no number at all
    ],
)
def test_rejects_non_degree_number_tokens(text):
    assert degree_in_text(text) is None


def test_empty_and_none_text_are_safe():
    assert degree_in_text("") is None
    assert degree_in_text(None) is None  # type: ignore[arg-type]


def test_first_in_range_degree_wins_when_several_appear():
    # The intermediate degree is what the player asked about; the leading match
    # in range is returned (a trailing out-of-range token doesn't shadow it).
    assert degree_in_text("compare the dart paragon at degree 67 vs d255") == 67
