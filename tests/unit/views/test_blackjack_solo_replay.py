"""Regression tests for solo Blackjack instant-replay (Smooth Interaction Pass PR 7).

Before this PR ``BlackjackView._finish`` disabled every child after
the hand resolved and stopped the view — leaving the user with no
way to play again without retyping ``!blackjack`` or re-opening the
panel.

These tests pin the new contract:

* Solo end-of-hand appends two new buttons on row 1: ``🔁 Play
  again`` and ``◀ Back to Blackjack``. PvP / tournament hands are
  unchanged (no replay row).
* ``Play again`` re-enters ``start_solo_blackjack`` (the canonical
  entry point) and commits the new hand via the existing
  ``commit_solo_blackjack`` helper, so ``_active`` and persistence
  stay correct.
* ``hit_btn`` now defers up front and uses ``safe_edit`` (the
  pre-PR-7 raw ``response.edit_message`` after I/O was flagged in
  the UI adoption audit's "partial" hotspots).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.blackjack._state import _Game
from cogs.blackjack.actions import SoloStartResult
from views.blackjack.solo_view import BlackjackView


def _make_solo_game(user_id: int = 1, guild_id: int = 99, bet: int = 10) -> _Game:
    return _Game(user_id, guild_id, bet, channel_id=42)


def _interaction(user_id: int = 1, *, is_done: bool = False) -> MagicMock:
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = user_id
    interaction.guild = MagicMock()
    interaction.guild.id = 99
    interaction.guild_id = 99
    interaction.channel = MagicMock()
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
# Solo _finish appends the replay+back row; PvP does not
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_solo_finish_appends_replay_and_back_buttons():
    game = _make_solo_game()
    view = BlackjackView(game, on_finish=None)
    interaction = _interaction()

    # Stub balance + economy calls — solo settle path runs inside _finish.
    with (
        patch(
            "views.blackjack.solo_view.economy_service.credit",
            new_callable=AsyncMock,
            return_value=500,
        ),
        patch(
            "views.blackjack.solo_view.db.get_coins",
            new_callable=AsyncMock,
            return_value=500,
        ),
        patch(
            "views.blackjack.solo_view._clear_solo_game",
            new_callable=AsyncMock,
        ),
    ):
        await view._finish(
            interaction,
            "🎉 You win!",
            discord.Color.green(),
            coin_delta=10,
            hand_value=20,
        )

    labels = [getattr(c, "label", None) for c in view.children]
    assert any(label and "Play again" in label for label in labels), labels
    assert any(label and "Back to Blackjack" in label for label in labels), labels


@pytest.mark.asyncio
async def test_pvp_finish_does_not_append_replay_row():
    """PvP path (on_finish callback present) must NOT gain replay
    buttons — replay is solo-only.
    """
    game = _make_solo_game()
    on_finish = AsyncMock()
    view = BlackjackView(game, on_finish=on_finish)
    interaction = _interaction()

    with (
        patch(
            "views.blackjack.solo_view.economy_service.credit",
            new_callable=AsyncMock,
            return_value=500,
        ),
        patch(
            "views.blackjack.solo_view.db.get_coins",
            new_callable=AsyncMock,
            return_value=500,
        ),
        patch(
            "views.blackjack.solo_view._clear_solo_game",
            new_callable=AsyncMock,
        ),
    ):
        await view._finish(
            interaction,
            "🎉 You win!",
            discord.Color.green(),
            coin_delta=10,
            hand_value=20,
        )

    labels = [getattr(c, "label", None) for c in view.children]
    assert not any(label and "Play again" in label for label in labels), labels
    assert not any(label and "Back to Blackjack" in label for label in labels), labels
    on_finish.assert_awaited_once()


@pytest.mark.asyncio
async def test_tournament_finish_does_not_append_replay_row():
    """Tournament path (tournament_chips != None) must NOT gain
    replay buttons either.
    """
    game = _make_solo_game()
    game.tournament_chips = 100  # mark as tournament
    view = BlackjackView(game, on_finish=None)
    interaction = _interaction()

    with patch(
        "views.blackjack.solo_view._clear_solo_game",
        new_callable=AsyncMock,
    ):
        await view._finish(
            interaction,
            "🎉 You win!",
            discord.Color.green(),
            coin_delta=10,
            hand_value=20,
        )

    labels = [getattr(c, "label", None) for c in view.children]
    assert not any(label and "Play again" in label for label in labels), labels


# ---------------------------------------------------------------------------
# Replay button re-enters start_solo_blackjack
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_replay_calls_start_solo_blackjack_with_same_bet():
    game = _make_solo_game(bet=25)
    view = BlackjackView(game, on_finish=None)
    interaction = _interaction()

    new_game = _make_solo_game(bet=25)
    new_view = BlackjackView(new_game, on_finish=None)
    fake_result = SoloStartResult(
        embed=discord.Embed(title="new hand"),
        view=new_view,
        game=new_game,
    )

    with (
        patch(
            "cogs.blackjack.actions.start_solo_blackjack",
            new_callable=AsyncMock,
            return_value=fake_result,
        ) as start_mock,
        patch(
            "cogs.blackjack.actions.commit_solo_blackjack",
            new_callable=AsyncMock,
        ) as commit_mock,
    ):
        await view._replay(interaction)

    start_mock.assert_awaited_once()
    args, kwargs = start_mock.await_args
    # Positional: user, guild, channel, bet
    assert args[3] == 25  # bet
    commit_mock.assert_awaited_once_with(new_view, interaction.message)


@pytest.mark.asyncio
async def test_replay_surfaces_short_circuit_message_ephemerally():
    """When start_solo_blackjack returns an ephemeral message
    (e.g. "You already have a game running!", "❌ You only have N 🪙."),
    the replay handler must surface it as an ephemeral followup and
    NOT edit the message.
    """
    game = _make_solo_game(bet=1000)
    view = BlackjackView(game, on_finish=None)
    interaction = _interaction()

    fake_result = SoloStartResult(
        embed=None,
        view=None,
        game=None,
        ephemeral_message="❌ You only have 5 🪙.",
    )

    with patch(
        "cogs.blackjack.actions.start_solo_blackjack",
        new_callable=AsyncMock,
        return_value=fake_result,
    ):
        await view._replay(interaction)

    # Some path must have sent the ephemeral — followup.send (post-defer).
    sent = (
        interaction.response.send_message.await_count
        + interaction.followup.send.await_count
    )
    assert sent == 1
    # Message was NOT edited to a new game state.
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_replay_handles_natural_blackjack_auto_payout():
    """If the new deal is a natural blackjack, start_solo_blackjack
    returns ``view=None`` with the payout embed; the replay handler
    must render that embed without trying to commit a non-existent
    view.
    """
    game = _make_solo_game(bet=10)
    view = BlackjackView(game, on_finish=None)
    interaction = _interaction()

    auto_embed = discord.Embed(title="natural-blackjack")
    fake_result = SoloStartResult(embed=auto_embed, view=None, game=None)

    with (
        patch(
            "cogs.blackjack.actions.start_solo_blackjack",
            new_callable=AsyncMock,
            return_value=fake_result,
        ),
        patch(
            "cogs.blackjack.actions.commit_solo_blackjack",
            new_callable=AsyncMock,
        ) as commit_mock,
    ):
        await view._replay(interaction)

    commit_mock.assert_not_called()


# ---------------------------------------------------------------------------
# hit_btn now defers up front
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hit_btn_defers_before_save_game_state():
    """Pre-PR-7, hit_btn called _save_game_state (DB I/O) and then
    raw response.edit_message — risking 3 s token expiry. The fix
    defers up front; this test pins the defer happens before the
    persistence call.
    """
    game = _make_solo_game()
    view = BlackjackView(game, on_finish=None)
    interaction = _interaction()

    call_order: list[str] = []

    async def fake_defer(_i, **_kw):
        call_order.append("defer")
        return True

    async def fake_save(_game):
        call_order.append("save")

    async def fake_edit(_i, **_kw):
        call_order.append("edit")
        return True

    # @discord.ui.button stores the original async function on the class
    # as the descriptor; reach the raw coroutine and call it with
    # self=view explicitly.
    hit_callback = type(view).hit_btn

    with (
        patch(
            "views.blackjack.solo_view.safe_defer",
            new=fake_defer,
        ),
        patch(
            "views.blackjack.solo_view._save_game_state",
            new=fake_save,
        ),
        patch(
            "views.blackjack.solo_view.safe_edit",
            new=fake_edit,
        ),
    ):
        await hit_callback(view, interaction, MagicMock())

    # Defer must come before save (and edit).
    assert call_order.index("defer") < call_order.index("save")
    assert call_order.index("save") < call_order.index("edit")
