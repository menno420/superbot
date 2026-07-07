"""Settle-once retrofits for the three unguarded money/stat settlement paths.

Pins the FINAL-REVIEW §6.3 fixes (2026-07-07):

1. **deathmatch `_DuelView`** — the Gate-V Arm-D live-confirmed double-write:
   a finishing-blow re-entry (double-click, or a timeout racing the final
   move) used to run ``update_leaderboard`` + gear wear twice. Now
   ``SettleOnceMixin``-guarded, mirroring the bot-duel sibling.
2. **blackjack `_check_tourn_done`** — every player's ``_finish_round`` (and
   ``on_timeout``) awaits between recording its result and the all-finished
   check, so two concurrent finishers both reached the payout; the paid path
   is row-consumption idempotent but the FREE-reward leg has no escrow rows,
   so the claim is its only double-pay guard.
3. **rps `check_tournament_progress`** — the same shape via ``register_move``'s
   two ``not self.matches`` branches; per-tournament claim re-armed at start
   (`rearm_settlement`, the new mixin seam for long-lived cog-held state).
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


def _stub_interaction(user) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = user
    interaction.guild_id = 0
    interaction.message = AsyncMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# 1. deathmatch _DuelView
# ---------------------------------------------------------------------------


def _duel_view(cog, p1, p2):
    from cogs.deathmatch_cog import _Duel, _DuelView

    duel = _Duel(p1, p2)  # type: ignore[arg-type]
    key = (p1.id, p2.id)
    cog.active_duels[key] = duel
    return duel, _DuelView(cog, duel, key, MagicMock(), guild_id=42)


@pytest.mark.asyncio
async def test_duel_finishing_resolve_settles_once():
    """A second finishing `_resolve` short-circuits: one W/L + one gear tick."""
    cog = MagicMock()
    cog.active_duels = {}
    cog.update_leaderboard = AsyncMock()
    p1, p2 = _player(1, "One"), _player(2, "Two")
    duel, view = _duel_view(cog, p1, p2)
    duel.player2_hp = 0  # already-lethal state: any resolve finishes

    with patch(
        "cogs.deathmatch_cog._tick_duel_gear_wear",
        new_callable=AsyncMock,
        return_value=[],
    ) as wear:
        await view._resolve(_stub_interaction(p1), "hit")
        await view._resolve(_stub_interaction(p2), "hit")

    cog.update_leaderboard.assert_awaited_once()
    wear.assert_awaited_once()
    assert view.is_settled


@pytest.mark.asyncio
async def test_duel_timeout_then_finish_settles_once():
    """The Arm-D race: timeout fires, then the queued finishing move runs."""
    cog = MagicMock()
    cog.active_duels = {}
    cog.update_leaderboard = AsyncMock()
    p1, p2 = _player(1, "One"), _player(2, "Two")
    duel, view = _duel_view(cog, p1, p2)
    view.message = AsyncMock()

    with patch(
        "cogs.deathmatch_cog._tick_duel_gear_wear",
        new_callable=AsyncMock,
        return_value=[],
    ):
        await view.on_timeout()
        duel.player2_hp = 0
        await view._resolve(_stub_interaction(p1), "hit")

    cog.update_leaderboard.assert_awaited_once()


@pytest.mark.asyncio
async def test_duel_finish_then_timeout_settles_once():
    cog = MagicMock()
    cog.active_duels = {}
    cog.update_leaderboard = AsyncMock()
    p1, p2 = _player(1, "One"), _player(2, "Two")
    duel, view = _duel_view(cog, p1, p2)
    view.message = AsyncMock()
    duel.player2_hp = 0

    with patch(
        "cogs.deathmatch_cog._tick_duel_gear_wear",
        new_callable=AsyncMock,
        return_value=[],
    ):
        await view._resolve(_stub_interaction(p1), "hit")
        await view.on_timeout()

    cog.update_leaderboard.assert_awaited_once()


@pytest.mark.asyncio
async def test_duel_non_finishing_move_does_not_consume_the_claim():
    """A regular turn must leave the claim intact for the real finish."""
    cog = MagicMock()
    cog.active_duels = {}
    cog.update_leaderboard = AsyncMock()
    p1, p2 = _player(1, "One"), _player(2, "Two")
    duel, view = _duel_view(cog, p1, p2)

    with patch(
        "cogs.deathmatch_cog._tick_duel_gear_wear",
        new_callable=AsyncMock,
        return_value=[],
    ):
        await view._resolve(_stub_interaction(p1), "poke")  # nobody at 0 HP
        assert not view.is_settled
        duel.player2_hp = 0
        await view._resolve(_stub_interaction(p2), "hit")

    cog.update_leaderboard.assert_awaited_once()


# ---------------------------------------------------------------------------
# 2. blackjack _check_tourn_done
# ---------------------------------------------------------------------------


def _bj_tournament():
    from services.blackjack_state import _BjTournament

    tourn = _BjTournament(
        host_id=1,
        guild_id=10,
        announce_id=20,
        entry_fee=0,  # FREE tournament — the unguarded leg
        rounds=1,
        duration_mins=5,
    )
    tourn.players = [1, 2]
    tourn.results = {1: 20, 2: 18}
    return tourn


@pytest.mark.asyncio
async def test_free_tournament_pays_once_across_concurrent_checks():
    from views.blackjack import tournament_views

    tourn = _bj_tournament()
    bot = MagicMock()
    bot.get_channel.return_value = None
    bot.get_guild.return_value = None
    settle = SimpleNamespace(paid=True, amount=200, new_winner_balance=200)

    with (
        patch.object(
            tournament_views.game_wager_workflow,
            "payout_tournament",
            new_callable=AsyncMock,
            return_value=settle,
        ) as payout,
        patch.object(
            tournament_views.tournament_state_service,
            "clear_active",
            new_callable=AsyncMock,
        ),
    ):
        # Two players' _finish_round callbacks both pass the all-finished
        # check before either pays — the claim lets exactly one through.
        await tournament_views._check_tourn_done(tourn, bot)
        await tournament_views._check_tourn_done(tourn, bot)

    payout.assert_awaited_once()


@pytest.mark.asyncio
async def test_unfinished_tournament_never_takes_the_claim():
    from views.blackjack import tournament_views

    tourn = _bj_tournament()
    tourn.results = {1: 20}  # one player still playing
    bot = MagicMock()

    with patch.object(
        tournament_views.game_wager_workflow,
        "payout_tournament",
        new_callable=AsyncMock,
    ) as payout:
        await tournament_views._check_tourn_done(tourn, bot)

    payout.assert_not_awaited()
    assert not tourn.is_settled


# ---------------------------------------------------------------------------
# 3. rps check_tournament_progress
# ---------------------------------------------------------------------------


def _rps_cog():
    from cogs.rps_tournament_cog import RockPaperScissorsCog

    cog = RockPaperScissorsCog.__new__(RockPaperScissorsCog)
    cog.bot = MagicMock()
    cog.tournament_active = True
    cog.entry_fee = 0  # FREE tournament — the unguarded leg
    cog.current_round = [_player(7, "Winner")]
    cog.scores = {}
    cog.matches = {}
    cog.match_channels = {}
    cog.players = []
    return cog


def _rps_patches(rps_tournament_cog, payout_result):
    return (
        patch.object(
            rps_tournament_cog.game_wager_workflow,
            "payout_tournament",
            new_callable=AsyncMock,
            return_value=payout_result,
        ),
        patch.object(
            rps_tournament_cog.tournament_state_service,
            "clear_active",
            new_callable=AsyncMock,
        ),
        patch.object(
            rps_tournament_cog,
            "delete_all_match_channels",
            new_callable=AsyncMock,
        ),
    )


@pytest.mark.asyncio
async def test_rps_final_payout_fires_once_across_racing_checkers():
    from cogs import rps_tournament_cog

    cog = _rps_cog()
    cog.rearm_settlement()
    guild = MagicMock()
    guild.id = 99
    guild.system_channel = AsyncMock()
    channel = AsyncMock()
    settle = SimpleNamespace(paid=True, amount=100, new_winner_balance=100)

    payout_p, clear_p, delete_p = _rps_patches(rps_tournament_cog, settle)
    with payout_p as payout, clear_p, delete_p:
        await cog.check_tournament_progress(guild, channel)
        # The second racing resolver enters the winner branch while the first
        # is still mid-flight (both saw self.matches empty — each awaits
        # between deleting its pair and register_move's check). Model that
        # re-entry state: the winner is still in current_round, the claim is
        # already consumed.
        cog.current_round = [_player(7, "Winner")]
        await cog.check_tournament_progress(guild, channel)

    payout.assert_awaited_once()


@pytest.mark.asyncio
async def test_rps_rearm_allows_the_next_tournament_to_pay():
    from cogs import rps_tournament_cog

    cog = _rps_cog()
    cog.rearm_settlement()
    guild = MagicMock()
    guild.id = 99
    guild.system_channel = AsyncMock()
    channel = AsyncMock()
    settle = SimpleNamespace(paid=True, amount=100, new_winner_balance=100)

    payout_p, clear_p, delete_p = _rps_patches(rps_tournament_cog, settle)
    with payout_p as payout, clear_p, delete_p:
        await cog.check_tournament_progress(guild, channel)
        # Next tournament starts → the claim re-arms → its final pays again.
        cog.rearm_settlement()
        cog.current_round = [_player(8, "NextWinner")]
        await cog.check_tournament_progress(guild, channel)

    assert payout.await_count == 2
