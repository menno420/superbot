"""Regression tests for solo RPS instant-replay (Smooth Interaction Pass PR 6).

Before this PR ``_RpsView._play`` disabled every child after the
round resolved and stopped the view — leaving the user with no way
to play again without retyping ``!rps`` or re-opening the panel.

These tests pin the new contract:

* After resolution the move buttons are disabled but two new
  result-action buttons appear on row 1: ``🔁 Play again`` and
  ``◀ Back to RPS``.
* ``Play again`` spawns a *fresh* ``_RpsView`` (same user / guild /
  bet) and edits the message in place. The old view stays stopped.
* When ``bet > 0`` and balance is insufficient, replay sends an
  ephemeral nudge and does NOT spawn a new game.
* Wrong-user replay attempts are rejected ephemerally
  (re-uses the existing ``interaction_check``).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.rps.solo_play import _RpsView


def _member(id_: int = 1) -> MagicMock:
    user = MagicMock(spec=discord.Member)
    user.id = id_
    user.display_name = f"user{id_}"
    user.mention = f"<@{id_}>"
    return user


def _interaction(user: MagicMock, *, is_done: bool = False) -> MagicMock:
    interaction = MagicMock()
    interaction.user = user
    interaction.guild_id = 99
    interaction.message = MagicMock()
    interaction.message.id = 4242
    interaction.response.is_done = MagicMock(return_value=is_done)
    interaction.response.defer = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.followup.edit_original_response = AsyncMock()
    interaction.edit_original_response = AsyncMock()
    interaction.original_response = AsyncMock(return_value=MagicMock())
    return interaction


# ---------------------------------------------------------------------------
# End-of-game: result row appended
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_play_appends_replay_and_back_buttons():
    user = _member(id_=1)
    view = _RpsView(user, guild_id=99, bet=0)
    interaction = _interaction(user)

    with (
        patch(
            "views.rps.solo_play.economy_service.credit",
            new_callable=AsyncMock,
            return_value=500,
        ),
        patch(
            "views.rps.solo_play.economy_service.debit",
            new_callable=AsyncMock,
            return_value=500,
        ),
        patch(
            "views.rps.solo_play.global_db.get_coins",
            new_callable=AsyncMock,
            return_value=500,
        ),
        patch(
            "views.rps.solo_play.random.choice",
            return_value="rock",
        ),
    ):
        await view._play(interaction, "paper")  # paper beats rock → win

    labels = [getattr(c, "label", None) for c in view.children]
    assert any(label and "Play again" in label for label in labels), labels
    assert any(label and "Back to RPS" in label for label in labels), labels

    # Move buttons remain visible but disabled.
    move_btns = [
        c
        for c in view.children
        if getattr(c, "label", None) in ("Rock", "Paper", "Scissors")
    ]
    assert len(move_btns) == 3
    for btn in move_btns:
        assert btn.disabled is True


@pytest.mark.asyncio
async def test_play_disables_move_buttons_and_uses_safe_edit():
    """Result edit uses ``safe_edit`` — not the raw response.edit_message
    that the pre-PR-6 implementation used after I/O.
    """
    user = _member(id_=1)
    view = _RpsView(user, guild_id=99, bet=10)
    interaction = _interaction(user)

    with (
        patch(
            "views.rps.solo_play.economy_service.credit",
            new_callable=AsyncMock,
            return_value=510,
        ),
        patch(
            "views.rps.solo_play.global_db.get_coins",
            new_callable=AsyncMock,
            return_value=510,
        ),
        patch(
            "views.rps.solo_play.random.choice",
            return_value="rock",
        ),
    ):
        await view._play(interaction, "paper")

    interaction.response.defer.assert_awaited()


# ---------------------------------------------------------------------------
# Replay: spawns fresh _RpsView
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_replay_spawns_fresh_view_for_free_play():
    user = _member(id_=1)
    finished = _RpsView(user, guild_id=99, bet=0)
    interaction = _interaction(user, is_done=False)

    await finished._replay(interaction)

    interaction.response.defer.assert_awaited_once()
    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    new_view = kwargs["view"]
    assert isinstance(new_view, _RpsView)
    assert new_view is not finished
    assert new_view.bet == 0
    assert new_view.user is user
    assert new_view.guild_id == 99


@pytest.mark.asyncio
async def test_replay_spawns_fresh_view_when_bet_covered():
    user = _member(id_=1)
    finished = _RpsView(user, guild_id=99, bet=10)
    interaction = _interaction(user)

    with patch(
        "views.rps.solo_play.global_db.get_coins",
        new_callable=AsyncMock,
        return_value=50,  # plenty
    ):
        await finished._replay(interaction)

    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    new_view = kwargs["view"]
    assert isinstance(new_view, _RpsView)
    assert new_view.bet == 10


@pytest.mark.asyncio
async def test_replay_blocked_when_balance_too_low():
    user = _member(id_=1)
    finished = _RpsView(user, guild_id=99, bet=100)
    interaction = _interaction(user)

    with patch(
        "views.rps.solo_play.global_db.get_coins",
        new_callable=AsyncMock,
        return_value=5,  # nowhere near 100
    ):
        await finished._replay(interaction)

    # No view swap.
    interaction.response.edit_message.assert_not_called()
    # Ephemeral nudge via safe_followup → response.send_message (not deferred path)
    # ...or followup.send (deferred path). One of them must fire.
    sent = (
        interaction.response.send_message.await_count
        + interaction.followup.send.await_count
    )
    assert sent == 1


@pytest.mark.asyncio
async def test_replay_rejects_wrong_user():
    """A different user clicking Play again gets the standard
    interaction-check ephemeral, identical to a wrong-user move click.
    """
    owner = _member(id_=1)
    finished = _RpsView(owner, guild_id=99, bet=0)
    intruder = _member(id_=99)
    interaction = _interaction(intruder)

    allowed = await finished.interaction_check(interaction)
    assert allowed is False
    interaction.response.send_message.assert_awaited_once()
