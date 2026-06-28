"""Completion-first (Q-0209) — Deathmatch PvP terminal views are never dead-ends.

Pins the headline gap from the Deathmatch completion cert (punch-list #1 + #3):
the **PvP** ``_DuelView`` / ``_ChallengeView`` used to disable their buttons and
stop on finish / timeout / decline / expire, stranding the player on a dead embed
(the bot path already swaps to a nav-bearing ``_BotDuelResultView``). They now
swap to ``_PvpDuelResultView`` (a ``HubView`` with SUBSYSTEM="deathmatch" → 📚 Help
+ ↩ Games nav + a 🔁 Rematch button).

Also pins the bugs-first root fix: the panel-initiated PvP path builds the duel
with ``ctx=None``; the leaderboard / gear-wear writes now take an explicit
``guild_id`` instead of ``ctx.guild.id`` (which crashed on resolve).
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


def _player(id_: int, name: str = "P") -> SimpleNamespace:
    return SimpleNamespace(id=id_, display_name=name, mention=f"<@{id_}>", bot=False)


def _member(id_: int, name: str = "P") -> MagicMock:
    """A discord.Member-spec'd mock — needed where the code isinstance-checks."""
    m = MagicMock(spec=discord.Member)
    m.id = id_
    m.display_name = name
    m.mention = f"<@{id_}>"
    m.bot = False
    return m


def _stub_interaction(user) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = user
    interaction.guild_id = 0
    interaction.message = AsyncMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def _result_view_cls():
    from views.games.deathmatch_panel import _PvpDuelResultView

    return _PvpDuelResultView


@pytest.mark.asyncio
async def test_pvp_duel_finish_swaps_to_result_view():
    """A finishing blow swaps the in-game view for the nav-bearing result view."""
    from cogs.deathmatch_cog import _Duel, _DuelView

    cog = MagicMock()
    cog.active_duels = {}
    cog.update_leaderboard = AsyncMock()
    p1, p2 = _player(1, "One"), _player(2, "Two")
    duel = _Duel(p1, p2)  # type: ignore[arg-type]
    duel.player2_hp = 1  # next attack from p1 finishes p2
    key = (1, 2)
    cog.active_duels[key] = duel
    view = _DuelView(cog, duel, key, MagicMock(), guild_id=42)
    interaction = _stub_interaction(p1)

    with patch(
        "cogs.deathmatch_cog._tick_duel_gear_wear",
        new_callable=AsyncMock,
        return_value=[],
    ):
        attack = next(c for c in view.children if (c.label or "").startswith("⚔️"))
        await attack.callback(interaction)  # type: ignore[union-attr]

    cog.update_leaderboard.assert_awaited_once_with(
        winner_id=p1.id,
        loser_id=p2.id,
        guild_id=42,
    )
    swapped = interaction.response.edit_message.call_args.kwargs["view"]
    assert isinstance(swapped, _result_view_cls())
    assert key not in cog.active_duels


@pytest.mark.asyncio
async def test_pvp_duel_timeout_swaps_to_result_view_and_uses_guild_id():
    """A timeout records under the explicit guild_id (panel path: ctx=None) and
    swaps to the result view — no ``ctx.guild`` AttributeError crash."""
    from cogs.deathmatch_cog import _Duel, _DuelView

    cog = MagicMock()
    cog.active_duels = {}
    cog.update_leaderboard = AsyncMock()
    p1, p2 = _player(1, "One"), _player(2, "Two")
    duel = _Duel(p1, p2)  # type: ignore[arg-type]
    key = (1, 2)
    cog.active_duels[key] = duel
    # ctx=None is the panel-initiated PvP path — used to crash on resolve.
    view = _DuelView(cog, duel, key, None, guild_id=777)  # type: ignore[arg-type]
    view.message = AsyncMock()

    with patch(
        "cogs.deathmatch_cog._tick_duel_gear_wear",
        new_callable=AsyncMock,
        return_value=[],
    ):
        await view.on_timeout()  # turn == p1 → p1 loses to p2

    cog.update_leaderboard.assert_awaited_once_with(
        winner_id=p2.id,
        loser_id=p1.id,
        guild_id=777,
    )
    swapped = view.message.edit.call_args.kwargs["view"]
    assert isinstance(swapped, _result_view_cls())


@pytest.mark.asyncio
async def test_duelview_guild_id_falls_back_to_ctx():
    """Backward-compat: with no explicit guild_id the duel still reads ctx.guild
    (the command path + existing tests)."""
    from cogs.deathmatch_cog import _Duel, _DuelView

    duel = _Duel(_player(1), _player(2))  # type: ignore[arg-type]
    ctx = MagicMock()
    ctx.guild.id = 999
    assert _DuelView(MagicMock(), duel, (1, 2), ctx).guild_id == 999
    # ctx=None with no guild_id degrades to the global bucket, never crashes.
    assert _DuelView(MagicMock(), duel, (1, 2), None).guild_id == 0  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_challenge_decline_swaps_to_result_view():
    from cogs.deathmatch_cog import _ChallengeView

    cog = MagicMock()
    cog.active_duels = {}
    challenger, opponent = _player(1, "Chal"), _player(2, "Opp")
    view = _ChallengeView(cog, challenger, opponent, (1, 2), MagicMock())
    view.message = AsyncMock()
    interaction = _stub_interaction(opponent)

    decline = next(c for c in view.children if (c.label or "").startswith("❌"))
    await decline.callback(interaction)  # type: ignore[union-attr]

    swapped = interaction.response.edit_message.call_args.kwargs["view"]
    assert isinstance(swapped, _result_view_cls())
    assert view.is_finished()


@pytest.mark.asyncio
async def test_challenge_expire_swaps_to_result_view():
    from cogs.deathmatch_cog import _ChallengeView

    cog = MagicMock()
    cog.active_duels = {}
    challenger, opponent = _player(1, "Chal"), _player(2, "Opp")
    view = _ChallengeView(cog, challenger, opponent, (1, 2), MagicMock())
    view.message = AsyncMock()

    await view.on_timeout()

    swapped = view.message.edit.call_args.kwargs["view"]
    assert isinstance(swapped, _result_view_cls())


@pytest.mark.asyncio
async def test_rematch_reissues_challenge():
    """🔁 Rematch swaps the result view for a fresh Accept/Decline challenge."""
    from cogs.deathmatch_cog import _ChallengeView

    cog = MagicMock()
    cog.active_duels = {}
    p1, p2 = _member(1, "One"), _member(2, "Two")
    view = _result_view_cls()(cog, p1, p2)
    interaction = _stub_interaction(p1)

    rematch = next(
        c
        for c in view.children
        if getattr(c, "custom_id", "") == "deathmatch_pvp_result:rematch"
    )
    await rematch.callback(interaction)  # type: ignore[union-attr]

    swapped = interaction.response.edit_message.call_args.kwargs["view"]
    assert isinstance(swapped, _ChallengeView)
    assert swapped.challenger is p1 and swapped.opponent is p2


@pytest.mark.asyncio
async def test_result_view_blocks_non_duelists():
    cog = MagicMock()
    p1, p2 = _player(1), _player(2)
    view = _result_view_cls()(cog, p1, p2)
    bystander = _stub_interaction(_player(99))

    assert await view.interaction_check(bystander) is False
    bystander.response.send_message.assert_awaited_once()

    for fighter in (p1, p2):
        assert await view.interaction_check(_stub_interaction(fighter)) is True
