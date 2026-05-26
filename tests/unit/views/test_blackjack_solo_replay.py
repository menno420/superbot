"""Regression tests for solo Blackjack terminal-state lifecycle.

Originally added in Smooth Interaction Pass PR 7 to pin the
"end-of-hand replay row" contract; updated when the terminal state
moved off the live ``BlackjackView`` and onto a dedicated
``_BlackjackSoloResultView``. The previous design appended Play
again / Back buttons to the live game view and then called
``self.stop()`` — which un-registers the view from discord.py's
component dispatch table and surfaces "interaction failed" on the
visible buttons. The fix swaps the live view for a fresh result
view in ``safe_edit`` before stopping the original.

These tests pin the new contract:

* Solo end-of-hand swaps in ``_BlackjackSoloResultView`` whose row 0
  is three disabled hit/stand/double shells and row 1 is ``🔁 Play
  again`` + ``◀ Back to Blackjack``. PvP / tournament hands keep
  the original view (no swap).
* ``Play again`` re-enters ``start_solo_blackjack`` (the canonical
  entry point) and commits the new hand via the existing
  ``commit_solo_blackjack`` helper, so ``_active`` and persistence
  stay correct.
* ``hit_btn`` defers up front and uses ``safe_edit`` (the pre-PR-7
  raw ``response.edit_message`` after I/O was flagged in the UI
  adoption audit's "partial" hotspots).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.blackjack._state import _Game
from cogs.blackjack.actions import SoloStartResult
from views.blackjack.solo_view import BlackjackView, _BlackjackSoloResultView


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
# Solo _finish swaps in result view; PvP / tournament keep the original view
# ---------------------------------------------------------------------------


def _capture_safe_edit() -> tuple[AsyncMock, dict]:
    """Return a patched ``safe_edit`` that records its kwargs."""
    captured: dict = {}

    async def fake_edit(_interaction, **kwargs):
        captured.update(kwargs)
        return True

    return fake_edit, captured  # type: ignore[return-value]


@pytest.mark.asyncio
async def test_solo_finish_appends_replay_and_back_buttons():
    game = _make_solo_game()
    view = BlackjackView(game, on_finish=None)
    interaction = _interaction()

    fake_edit, captured = _capture_safe_edit()

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
        patch("views.blackjack.solo_view.safe_edit", new=fake_edit),
    ):
        await view._finish(
            interaction,
            "🎉 You win!",
            discord.Color.green(),
            coin_delta=10,
            hand_value=20,
        )

    result_view = captured["view"]
    assert isinstance(result_view, _BlackjackSoloResultView)
    labels = [getattr(c, "label", None) for c in result_view.children]
    assert any(label and "Play again" in label for label in labels), labels
    assert any(label and "Back to Blackjack" in label for label in labels), labels


@pytest.mark.asyncio
async def test_pvp_finish_does_not_append_replay_row():
    """PvP path (on_finish callback present) keeps the original
    ``BlackjackView`` — replay is solo-only.
    """
    game = _make_solo_game()
    on_finish = AsyncMock()
    view = BlackjackView(game, on_finish=on_finish)
    interaction = _interaction()

    fake_edit, captured = _capture_safe_edit()

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
        patch("views.blackjack.solo_view.safe_edit", new=fake_edit),
    ):
        await view._finish(
            interaction,
            "🎉 You win!",
            discord.Color.green(),
            coin_delta=10,
            hand_value=20,
        )

    assert captured["view"] is view
    on_finish.assert_awaited_once()


@pytest.mark.asyncio
async def test_tournament_finish_does_not_append_replay_row():
    """Tournament path (tournament_chips != None) keeps the original
    ``BlackjackView`` — replay is solo-only.
    """
    game = _make_solo_game()
    game.tournament_chips = 100  # mark as tournament
    view = BlackjackView(game, on_finish=None)
    interaction = _interaction()

    fake_edit, captured = _capture_safe_edit()

    with (
        patch(
            "views.blackjack.solo_view._clear_solo_game",
            new_callable=AsyncMock,
        ),
        patch("views.blackjack.solo_view.safe_edit", new=fake_edit),
    ):
        await view._finish(
            interaction,
            "🎉 You win!",
            discord.Color.green(),
            coin_delta=10,
            hand_value=20,
        )

    assert captured["view"] is view


# ---------------------------------------------------------------------------
# Replay button re-enters start_solo_blackjack
# ---------------------------------------------------------------------------


def _result_view(bet: int = 10) -> _BlackjackSoloResultView:
    game = _make_solo_game(bet=bet)
    return _BlackjackSoloResultView(game.user_id, game.guild_id, game.bet, game)


@pytest.mark.asyncio
async def test_replay_calls_start_solo_blackjack_with_same_bet():
    view = _result_view(bet=25)
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
    view = _result_view(bet=1000)
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
    view = _result_view(bet=10)
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
# Result view: ownership, terminal disabled shells, on_timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_result_view_disables_move_button_shells():
    """Row 0 of the result view is three disabled hit/stand/double
    shells (visual continuity with the in-progress game view).
    """
    view = _result_view(bet=10)
    move_shells = [
        c
        for c in view.children
        if getattr(c, "label", None) in ("Hit", "Stand", "Double Down")
    ]
    assert len(move_shells) == 3
    for shell in move_shells:
        assert shell.disabled is True


@pytest.mark.asyncio
async def test_result_view_rejects_wrong_user():
    """A different user clicking any result-view button gets the
    standard ownership ephemeral.
    """
    owner_view = _result_view(bet=10)
    intruder = _interaction(user_id=owner_view.user_id + 1)

    allowed = await owner_view.interaction_check(intruder)
    assert allowed is False
    intruder.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_result_view_on_timeout_disables_remaining_items():
    """``on_timeout`` disables every child (including the previously
    enabled Play again / Back) and edits the bound message. Guards
    cleanly when ``self.message`` is unset.
    """
    view = _result_view(bet=10)
    view.message = MagicMock()
    view.message.edit = AsyncMock()

    await view.on_timeout()

    for child in view.children:
        assert child.disabled is True
    view.message.edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_result_view_on_timeout_skips_when_message_unset():
    """If the message reference was never assigned, ``on_timeout``
    must not raise (defensive against the result view being
    constructed but never published).
    """
    view = _result_view(bet=10)
    assert view.message is None

    # Must not raise.
    await view.on_timeout()


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
        # Pin a non-bust value so the test exercises the save-path,
        # not the bust → _finish branch that hits the real DB.
        patch("views.blackjack.solo_view._hand_value", return_value=15),
    ):
        await hit_callback(view, interaction, MagicMock())

    # Defer must come before save (and edit).
    assert call_order.index("defer") < call_order.index("save")
    assert call_order.index("save") < call_order.index("edit")
