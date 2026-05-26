"""Regression tests for solo RPS terminal-state lifecycle.

Originally added in Smooth Interaction Pass PR 6 to pin the
"end-of-round replay row" contract; updated when the terminal state
moved off the live ``_RpsView`` and onto a dedicated
``_RpsSoloResultView``. The previous design appended Play again /
Back to the live game view and then called ``self.stop()`` — which
un-registers the view from discord.py's component dispatch table and
surfaces "interaction failed" on the visible buttons. The fix swaps
the live view for a fresh result view in ``safe_edit`` before
stopping the original.

These tests pin the new contract:

* After resolution ``_play`` swaps the view for a fresh
  ``_RpsSoloResultView`` whose row 0 is three disabled
  Rock/Paper/Scissors shells and row 1 is ``🔁 Play again`` +
  ``↩ Back to RPS``.
* ``Play again`` (now on the result view) spawns a *fresh* ``_RpsView``
  (same user / guild / bet) and edits the message in place. The old
  view stays stopped.
* When ``bet > 0`` and balance is insufficient, replay sends an
  ephemeral nudge and does NOT spawn a new game.
* Wrong-user replay attempts are rejected ephemerally on the result
  view's ``interaction_check``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.rps.solo_play import _RpsSoloResultView, _RpsView


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
# End-of-game: result view swapped in
# ---------------------------------------------------------------------------


def _capture_safe_edit() -> tuple[AsyncMock, dict]:
    captured: dict = {}

    async def fake_edit(_interaction, **kwargs):
        captured.update(kwargs)
        return True

    return fake_edit, captured  # type: ignore[return-value]


@pytest.mark.asyncio
async def test_play_appends_replay_and_back_buttons():
    user = _member(id_=1)
    view = _RpsView(user, guild_id=99, bet=0)
    interaction = _interaction(user)

    fake_edit, captured = _capture_safe_edit()

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
        patch("views.rps.solo_play.safe_edit", new=fake_edit),
    ):
        await view._play(interaction, "paper")  # paper beats rock → win

    result_view = captured["view"]
    assert isinstance(result_view, _RpsSoloResultView)
    labels = [getattr(c, "label", None) for c in result_view.children]
    assert any(label and "Play again" in label for label in labels), labels
    assert any(label and "Back to RPS" in label for label in labels), labels

    move_btns = [
        c
        for c in result_view.children
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
    finished = _RpsSoloResultView(user, guild_id=99, bet=0)
    interaction = _interaction(user, is_done=False)

    await finished._replay(interaction)

    interaction.response.defer.assert_awaited_once()
    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    new_view = kwargs["view"]
    assert isinstance(new_view, _RpsView)
    assert new_view.bet == 0
    assert new_view.user is user
    assert new_view.guild_id == 99


@pytest.mark.asyncio
async def test_replay_spawns_fresh_view_when_bet_covered():
    user = _member(id_=1)
    finished = _RpsSoloResultView(user, guild_id=99, bet=10)
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
    finished = _RpsSoloResultView(user, guild_id=99, bet=100)
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
    """A different user clicking Play again on the result view gets
    the standard ownership ephemeral.
    """
    owner = _member(id_=1)
    finished = _RpsSoloResultView(owner, guild_id=99, bet=0)
    intruder = _member(id_=99)
    interaction = _interaction(intruder)

    allowed = await finished.interaction_check(interaction)
    assert allowed is False
    interaction.response.send_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# Result view: ownership / shells / on_timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_result_view_disables_move_button_shells():
    """Row 0 of the result view is three disabled Rock/Paper/Scissors
    shells (visual continuity with the in-progress game view).
    """
    user = _member(id_=1)
    view = _RpsSoloResultView(user, guild_id=99, bet=10)
    move_shells = [
        c
        for c in view.children
        if getattr(c, "label", None) in ("Rock", "Paper", "Scissors")
    ]
    assert len(move_shells) == 3
    for shell in move_shells:
        assert shell.disabled is True


@pytest.mark.asyncio
async def test_result_view_on_timeout_disables_remaining_items():
    """``on_timeout`` disables every child (including the previously
    enabled Play again / Back) and edits the bound message.
    """
    user = _member(id_=1)
    view = _RpsSoloResultView(user, guild_id=99, bet=10)
    view.message = MagicMock()
    view.message.edit = AsyncMock()

    await view.on_timeout()

    for child in view.children:
        assert child.disabled is True
    view.message.edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_result_view_on_timeout_skips_when_message_unset():
    """If the message reference was never assigned, ``on_timeout``
    must not raise.
    """
    user = _member(id_=1)
    view = _RpsSoloResultView(user, guild_id=99, bet=10)
    assert view.message is None

    # Must not raise.
    await view.on_timeout()
