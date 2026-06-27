"""Tests for the BTD6 absence-claim contradiction guard (Layer B first slice).

The guard fires ONLY when the grounded haystack affirms the very attribute the
reply denies — so it catches the canonical "Monkey Buccaneer does not have a
paragon" repro (the data grounds Navarch) yet never blocks a true negative.
"""

from __future__ import annotations

import pytest

from utils.btd6 import absence_guard

# A realistic grounded line: the data AFFIRMS the Buccaneer's paragon.
_BUCC_PARAGON = (
    "[btd6_paragon] Monkey Buccaneer's Paragon (tier 6) is Navarch of the Seas, "
    "costing 550000 on Medium (source: bloonswiki)"
)


@pytest.mark.parametrize(
    "reply",
    [
        "The Monkey Buccaneer does not have a paragon.",
        "The Monkey Buccaneer doesn't have a paragon.",
        "Monkey Buccaneer has no paragon.",
        "There is no paragon for the Monkey Buccaneer.",
        "The Monkey Buccaneer lacks a paragon.",
        "The Monkey Buccaneer is without a paragon.",
        "The Monkey Buccaneer's paragon does not exist.",
    ],
)
def test_flags_contradicted_paragon_absence(reply):
    """Every common phrasing of the false 'no paragon' is caught when the data
    affirms the paragon."""
    offending = absence_guard.contradicted_absence_claims(reply, _BUCC_PARAGON)
    assert offending, f"expected {reply!r} to be flagged as a contradicted absence"


def test_silent_when_grounding_does_not_affirm_the_attribute():
    """A 'no paragon' statement is a true negative when the data never affirms a
    paragon for the subject — the gate must stay silent (no false floor)."""
    haystack = "[btd6_tower] Spike Factory base cost: 1000 (source: dataset)"
    offending = absence_guard.contradicted_absence_claims(
        "The Spike Factory does not have a paragon.", haystack
    )
    assert offending == ()


def test_silent_for_a_different_tower_than_the_one_affirmed():
    """The gate matches the subject: a true 'no paragon' about a tower other than
    the one the data affirms must not be blocked."""
    offending = absence_guard.contradicted_absence_claims(
        "The Spike Factory does not have a paragon.", _BUCC_PARAGON
    )
    assert offending == ()


def test_silent_on_a_no_second_paragon_qualifier():
    """'no SECOND paragon' is a non-absence (towers have exactly one) — excluded."""
    offending = absence_guard.contradicted_absence_claims(
        "The Monkey Buccaneer has no second paragon.", _BUCC_PARAGON
    )
    assert offending == ()


def test_silent_when_the_reply_affirms_the_paragon():
    """A correct positive answer is never flagged."""
    offending = absence_guard.contradicted_absence_claims(
        "The Monkey Buccaneer's paragon is Navarch of the Seas.", _BUCC_PARAGON
    )
    assert offending == ()


def test_handles_a_curly_apostrophe_in_the_grounding():
    """A model/source may emit the curly apostrophe; the affirm match must still
    find the subject."""
    haystack = "[btd6_paragon] Monkey Buccaneer’s Paragon (tier 6) is Navarch"
    offending = absence_guard.contradicted_absence_claims(
        "The Monkey Buccaneer does not have a paragon.", haystack
    )
    assert offending


def test_returns_the_offending_sentence_only():
    """A multi-sentence reply returns just the contradicted sentence."""
    reply = (
        "The Monkey Buccaneer is a water tower. "
        "It does not have a paragon, surprisingly. "
        "Its top path ends in Trade Empire."
    )
    offending = absence_guard.contradicted_absence_claims(reply, _BUCC_PARAGON)
    # "It does not have a paragon" names no tower → not flagged on its own; the
    # subject must be in the same sentence. This documents the v1 same-sentence
    # scope (pronoun-reference is the noted follow-up).
    assert offending == ()


def test_flags_when_subject_and_denial_share_the_sentence():
    reply = (
        "The Monkey Buccaneer is a water tower. "
        "The Monkey Buccaneer does not have a paragon."
    )
    offending = absence_guard.contradicted_absence_claims(reply, _BUCC_PARAGON)
    assert offending == ("The Monkey Buccaneer does not have a paragon.",)


def test_empty_inputs_are_safe():
    assert absence_guard.contradicted_absence_claims("", _BUCC_PARAGON) == ()
    assert absence_guard.contradicted_absence_claims("no paragon", "") == ()
