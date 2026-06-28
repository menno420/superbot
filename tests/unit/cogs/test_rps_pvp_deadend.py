"""Completion-first (Q-0209) — RPS PvP result is never a dead-end + help-text guard.

Pins the remaining offline gaps from the RPS completion cert:
- punch-list #2 — the PvP match result used to post a bare channel embed with no
  controls; it now carries a ◀ Back to RPS affordance (`_RpsPvpResultView`).
- punch-list #4 — a `!rpshelp` output guard so the command-name drift fixed in the
  prior PR (underscored `!rps_*` names + a nonexistent leaderboard) can't silently
  return.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


def _player(id_: int) -> SimpleNamespace:
    return SimpleNamespace(id=id_, mention=f"<@{id_}>")


def _stub_interaction(user) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = user
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def test_pvp_result_view_carries_back_to_rps():
    from views.rps.pvp_play import _RpsPvpResultView

    view = _RpsPvpResultView(_player(1), _player(2))
    labels = [getattr(c, "label", "") for c in view.children]
    assert any("Back to RPS" in (lbl or "") for lbl in labels), labels


@pytest.mark.asyncio
async def test_pvp_result_view_blocks_non_participants():
    from views.rps.pvp_play import _RpsPvpResultView

    p1, p2 = _player(1), _player(2)
    view = _RpsPvpResultView(p1, p2)
    assert await view.interaction_check(_stub_interaction(_player(99))) is False
    for fighter in (p1, p2):
        assert await view.interaction_check(_stub_interaction(fighter)) is True


@pytest.mark.asyncio
async def test_resolve_posts_result_with_back_affordance():
    """A resolved (free) PvP match posts its result with the nav-bearing view —
    not a bare embed."""
    from views.rps.pvp_play import _RpsPvpPlayView, _RpsPvpResultView

    p1, p2 = _player(1), _player(2)
    channel = MagicMock()
    channel.id = 5
    channel.send = AsyncMock(return_value=AsyncMock())
    view = _RpsPvpPlayView(p1, p2, guild_id=7, bet=0, channel=channel)
    view.message = AsyncMock()
    view.choices = {p1.id: "rock", p2.id: "scissors"}  # p1 wins

    with patch(
        "views.rps.pvp_play.game_state_service.clear",
        new_callable=AsyncMock,
    ):
        await view._resolve()

    channel.send.assert_awaited_once()
    posted_view = channel.send.await_args.kwargs["view"]
    assert isinstance(posted_view, _RpsPvpResultView)


@pytest.mark.asyncio
async def test_rpshelp_lists_only_real_command_names():
    """Guard against the punch-list #1 drift recurring: the help text must use the
    real no-underscore commands and never advertise a leaderboard that doesn't
    exist."""
    from cogs.rps_tournament_cog import RockPaperScissorsCog

    ctx = SimpleNamespace(send=AsyncMock())
    await RockPaperScissorsCog.rps_help.callback(MagicMock(), ctx)  # type: ignore[attr-defined]
    text = ctx.send.await_args.args[0]

    for real in ("!rps", "!rpsregister", "!rpsstart", "!rpsbot", "!rpssettings", "!rpshelp"):
        assert real in text, f"{real} missing from rpshelp"
    for bogus in ("!rps_register", "!rps_start", "!rps_bot", "!rps_settings", "!rps_help"):
        assert bogus not in text, f"stale underscored command {bogus} in rpshelp"
    assert "leaderboard" not in text.lower(), "rpshelp advertises a nonexistent leaderboard"
