"""Tests for the Project Moon (Limbus) context detector."""

from __future__ import annotations

import pytest

from utils.projmoon.keywords import has_limbus_context


@pytest.mark.parametrize(
    "text",
    [
        "what is limbus company",
        "tell me about the sinners",
        "how does an E.G.O work",
        "is Heathcliff good",
        "explain the ALEPH grade",
        "who is Ryōshū",
        "mirror dungeon tips",
    ],
)
def test_distinctive_tokens_match(text):
    assert has_limbus_context(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "",
        "i feel a lot of pride today",  # bare Sin word — deliberately not routed
        "the fire will burn",  # ambiguous status word — not routed bare
        "i am full of envy and sloth",
        "what is the weather",
    ],
)
def test_ambiguous_or_empty_does_not_match(text):
    assert has_limbus_context(text) is False


def test_word_boundary_guard():
    # "ego" is only matched as "e.g.o" / "ego grade", not inside "category".
    assert has_limbus_context("this is a category of things") is False
