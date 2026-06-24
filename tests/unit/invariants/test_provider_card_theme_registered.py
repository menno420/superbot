"""Invariant: every ``RankProvider.card_theme`` is a registered engine skin.

A provider names its leaderboard / rank-card skin with a free string
(``card_theme``), resolved by :func:`utils.card_render.get_theme`, which falls
back to the **default** skin on an unknown key *with no error*.  That silent
fallback means a typo (``"abyss "`` / ``"emberr"``) would quietly render the
wrong skin and never go red — exactly the silent-misconfiguration class the
dead-binding self-heal and tool-pin guards exist to catch elsewhere.

This test makes a skin typo a failing build instead of a quiet visual bug
(the friction→guard reflex: #1280 / #1297 / BUG-0017).
"""

from __future__ import annotations

import pytest

from services.rank_providers import get_provider, provider_names
from utils.card_render import THEMES


@pytest.mark.parametrize("name", provider_names())
def test_every_provider_card_theme_is_registered(name: str) -> None:
    provider = get_provider(name)
    assert provider is not None  # provider_names() only yields registered keys
    assert provider.card_theme in THEMES, (
        f"RankProvider {name!r} declares card_theme={provider.card_theme!r}, which is not a key in "
        f"card_render.THEMES ({sorted(THEMES)}). get_theme() would silently fall back to the default "
        f"skin — fix the typo or register the theme."
    )


def test_guard_would_catch_an_unregistered_theme() -> None:
    # Pin that the assertion above is real: a bogus theme key is NOT in THEMES,
    # so a provider carrying it would fail the parametrized test.
    assert "definitely-not-a-real-skin" not in THEMES
