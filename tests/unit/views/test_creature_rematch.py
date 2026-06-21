"""creature_battle rematch view — two-participant interaction gating.

The rematch button is interactable by *either* fighter and no one else (a
specialized two-participant lifecycle, unlike a standard single-author BaseView).
These pins keep that gate honest without needing a live Discord.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from views.creature_battle.rematch import CreatureRematchView


def _member(uid: int):
    return SimpleNamespace(id=uid, mention=f"<@{uid}>", display_name=f"U{uid}")


def _interaction(user_id: int):
    return SimpleNamespace(
        user=SimpleNamespace(id=user_id),
        response=SimpleNamespace(send_message=AsyncMock()),
    )


def test_view_has_a_single_rematch_button():
    view = CreatureRematchView(_member(1), _member(2), 99)
    labels = [getattr(c, "label", None) for c in view.children]
    assert "Rematch" in labels


@pytest.mark.asyncio
async def test_either_fighter_passes_the_interaction_check():
    view = CreatureRematchView(_member(1), _member(2), 99)
    for uid in (1, 2):
        interaction = _interaction(uid)
        assert await view.interaction_check(interaction) is True
        interaction.response.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_third_party_is_rejected_with_an_ephemeral_nudge():
    view = CreatureRematchView(_member(1), _member(2), 99)
    interaction = _interaction(3)
    assert await view.interaction_check(interaction) is False
    interaction.response.send_message.assert_awaited_once()
    _, kwargs = interaction.response.send_message.await_args
    assert kwargs.get("ephemeral") is True
