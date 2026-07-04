"""PvP bet selector in the Blackjack panel — completion-cert punch-list #2.

Before this, the panel's "Challenge Player" flow hardcoded ``bet = 0``
(``_BlackjackOpponentSelect.callback``) — PvP stakes were reachable only
via the ``!bj @player <bet>`` command. The opponent select now routes
into a ``_BlackjackChallengeBetView`` stake picker (Free + presets +
Custom) before the challenge is built, mirroring the Solo Bet UX.

These tests pin:
* picking an opponent opens the bet picker (not an immediate bet-0 game);
* a self/bot target is rejected *before* the picker is shown;
* a preset/custom bet flows through to ``build_blackjack_challenge_view``
  with the chosen stake (not 0).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.games import blackjack_panel
from views.games.blackjack_panel import (
    _BlackjackChallengeBetButton,
    _BlackjackChallengeBetView,
    _BlackjackChallengeSelectView,
    _BlackjackOpponentSelect,
)


def _member(id_: int, *, bot: bool = False) -> MagicMock:
    m = MagicMock(spec=discord.Member)
    m.id = id_
    m.bot = bot
    m.mention = f"<@{id_}>"
    return m


def _interaction(user: MagicMock, guild_id: int = 7) -> MagicMock:
    inter = MagicMock(spec=discord.Interaction)
    inter.user = user
    inter.guild_id = guild_id
    inter.message = MagicMock()
    inter.response = MagicMock()
    inter.response.edit_message = AsyncMock()
    inter.response.send_message = AsyncMock()
    return inter


def _opponent_select(
    challenger: MagicMock, opponent: MagicMock
) -> _BlackjackOpponentSelect:
    view = _BlackjackChallengeSelectView(challenger)
    select = next(c for c in view.children if isinstance(c, _BlackjackOpponentSelect))
    # discord.py populates ``.values`` from the payload; stub it directly.
    type(select).values = property(lambda self: [opponent])
    return select


@pytest.mark.asyncio
async def test_selecting_opponent_opens_bet_picker():
    challenger = _member(1)
    opponent = _member(2)
    select = _opponent_select(challenger, opponent)
    inter = _interaction(challenger)

    try:
        await select.callback(inter)
    finally:
        del type(select).values

    inter.response.edit_message.assert_awaited_once()
    new_view = inter.response.edit_message.await_args.kwargs["view"]
    assert isinstance(new_view, _BlackjackChallengeBetView)
    # The picker offers Free play + the four presets + Custom.
    bet_buttons = [
        c for c in new_view.children if isinstance(c, _BlackjackChallengeBetButton)
    ]
    assert {b._bet for b in bet_buttons} == {0, 10, 25, 50, 100}


@pytest.mark.asyncio
async def test_selecting_self_is_rejected_before_picker():
    challenger = _member(1)
    select = _opponent_select(challenger, challenger)
    inter = _interaction(challenger)

    try:
        await select.callback(inter)
    finally:
        del type(select).values

    inter.response.send_message.assert_awaited_once()
    assert "yourself" in inter.response.send_message.await_args.args[0].lower()
    inter.response.edit_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_selecting_bot_is_rejected_before_picker():
    challenger = _member(1)
    bot_opponent = _member(2, bot=True)
    select = _opponent_select(challenger, bot_opponent)
    inter = _interaction(challenger)

    try:
        await select.callback(inter)
    finally:
        del type(select).values

    inter.response.send_message.assert_awaited_once()
    assert "bot" in inter.response.send_message.await_args.args[0].lower()
    inter.response.edit_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_preset_bet_builds_challenge_with_chosen_stake():
    challenger = _member(1)
    opponent = _member(2)
    view = _BlackjackChallengeBetView(challenger, opponent)
    button = next(
        c
        for c in view.children
        if isinstance(c, _BlackjackChallengeBetButton) and c._bet == 50
    )
    inter = _interaction(challenger)

    fake_view = MagicMock()
    with patch.object(
        blackjack_panel,
        "build_blackjack_challenge_view",
        return_value=(MagicMock(), fake_view, None),
    ) as build:
        await button.callback(inter)

    build.assert_called_once()
    # bet (4th positional arg) is the chosen 50, not 0.
    assert build.call_args.args[3] == 50
    assert build.call_args.args[0] is challenger
    assert build.call_args.args[1] is opponent
    inter.response.edit_message.assert_awaited_once()
    assert fake_view.message is inter.message


@pytest.mark.asyncio
async def test_challenge_build_error_is_surfaced_ephemerally():
    challenger = _member(1)
    opponent = _member(2)
    view = _BlackjackChallengeBetView(challenger, opponent)
    button = next(
        c
        for c in view.children
        if isinstance(c, _BlackjackChallengeBetButton) and c._bet == 10
    )
    inter = _interaction(challenger)

    with patch.object(
        blackjack_panel,
        "build_blackjack_challenge_view",
        return_value=(
            MagicMock(),
            None,
            "There's already a PvP game between these players.",
        ),
    ):
        await button.callback(inter)

    inter.response.send_message.assert_awaited_once()
    assert inter.response.send_message.await_args.kwargs.get("ephemeral") is True
    inter.response.edit_message.assert_not_awaited()
