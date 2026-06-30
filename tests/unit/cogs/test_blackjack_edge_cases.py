"""Blackjack edge-case / lifecycle tests — completion-cert punch-list #3.

The Blackjack completion certificate
(``docs/planning/feature-completion/units/blackjack.md``) flagged three
code paths that exist but were untested:

1. **Tournament-timeout forfeit** — a round view that times out must
   deduct the round bet, decrement ``rounds_left``, disable its
   controls, and either advance the player to the next round or mark
   them done (chips/rounds exhausted) and run the done-check.
2. **Guild-removal cleanup** — ``on_guild_remove`` must refund + clear
   pre-debited *tournament* entries, clear solo/PvP rows **without**
   refund (no pre-debit), and recover stranded PvP escrow.
3. **Natural-blackjack auto-payout** — a dealt natural pays out
   immediately (1.5× bet, or the free-win flat for bet=0), returns a
   result with ``view=None``, and clears the active-game slot.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# 1. Tournament-timeout forfeit
# ---------------------------------------------------------------------------


def _make_round_view(rounds_left: int, chips: int):
    from services.blackjack_state import (
        TOURN_START_CHIPS,
        _active,
        _Game,
        _TournPlayerState,
    )
    from views.blackjack.tournament_views import _TournBlackjackView

    ps = _TournPlayerState(user_id=42, guild_id=7, rounds=rounds_left, channel_id=99)
    ps.chips = chips
    ps.rounds_left = rounds_left
    game = _Game(42, 7, 0, tournament_chips=TOURN_START_CHIPS, channel_id=99)
    view = _TournBlackjackView(
        game=game,
        player_state=ps,
        channel=MagicMock(),
        tourn=MagicMock(),
        bot=MagicMock(),
    )
    view.message = AsyncMock()
    # Pre-seed the active slot so we can assert the timeout clears it.
    _active[(42, 7)] = game
    return view, ps, _active


@pytest.mark.asyncio
async def test_tournament_timeout_forfeits_round_and_advances():
    from services.blackjack_state import TOURN_BET_PER_ROUND

    view, ps, active = _make_round_view(rounds_left=3, chips=1000)
    view.tourn.results = {}

    with (
        patch(
            "views.blackjack.tournament_views._start_tourn_round",
            new_callable=AsyncMock,
        ) as next_round,
        patch(
            "views.blackjack.tournament_views._check_tourn_done",
            new_callable=AsyncMock,
        ) as done,
    ):
        await view.on_timeout()

    # Round bet deducted, one round consumed.
    assert ps.chips == 1000 - TOURN_BET_PER_ROUND
    assert ps.rounds_left == 2
    # Still has chips + rounds → next round dealt, not finished.
    next_round.assert_awaited_once()
    done.assert_not_awaited()
    assert ps.done is False
    # Active slot cleared and controls disabled.
    assert (42, 7) not in active
    assert all(item.disabled for item in view.children)
    view.message.edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_tournament_timeout_finishes_player_when_rounds_exhausted():
    view, ps, _active = _make_round_view(rounds_left=1, chips=1000)
    view.tourn.results = {}

    with (
        patch(
            "views.blackjack.tournament_views._start_tourn_round",
            new_callable=AsyncMock,
        ) as next_round,
        patch(
            "views.blackjack.tournament_views._check_tourn_done",
            new_callable=AsyncMock,
        ) as done,
    ):
        await view.on_timeout()

    assert ps.rounds_left == 0
    assert ps.done is True
    # Final chips recorded for the done-check, which runs; no next round.
    assert view.tourn.results[ps.user_id] == ps.chips
    done.assert_awaited_once()
    next_round.assert_not_awaited()


@pytest.mark.asyncio
async def test_tournament_timeout_finishes_player_when_broke():
    view, ps, _active = _make_round_view(rounds_left=5, chips=200)
    view.tourn.results = {}

    with (
        patch(
            "views.blackjack.tournament_views._start_tourn_round",
            new_callable=AsyncMock,
        ) as next_round,
        patch(
            "views.blackjack.tournament_views._check_tourn_done",
            new_callable=AsyncMock,
        ) as done,
    ):
        await view.on_timeout()

    # 200 - 200 = 0 chips → forced out even though rounds remain.
    assert ps.chips == 0
    assert ps.done is True
    done.assert_awaited_once()
    next_round.assert_not_awaited()


# ---------------------------------------------------------------------------
# 2. Guild-removal cleanup
# ---------------------------------------------------------------------------


def _row(id_, *, guild_id=7, user_id=42, bet=0):
    return {
        "id": id_,
        "guild_id": guild_id,
        "user_id": user_id,
        "state": {"bet": bet},
    }


@pytest.mark.asyncio
async def test_on_guild_remove_refunds_tournament_clears_solo_pvp():
    import cogs.blackjack_cog as cog_mod
    from cogs.blackjack_cog import (
        BLACKJACK_PVP_SUBSYSTEM,
        BLACKJACK_SOLO_SUBSYSTEM,
        BLACKJACK_TOURNAMENT_SUBSYSTEM,
        BlackjackCog,
    )

    guild = MagicMock()
    guild.id = 7

    def _by_subsystem(subsystem, *, guild_id):
        if subsystem == BLACKJACK_TOURNAMENT_SUBSYSTEM:
            return [_row(1, bet=100), _row(2, bet=0, user_id=43)]
        if subsystem == BLACKJACK_SOLO_SUBSYSTEM:
            return [_row(10)]
        if subsystem == BLACKJACK_PVP_SUBSYSTEM:
            return [_row(20)]
        return []

    with (
        patch.object(
            cog_mod.game_state_service,
            "list_active_for_subsystem",
            new=AsyncMock(side_effect=_by_subsystem),
        ),
        patch.object(
            cog_mod.game_state_service, "clear_by_id", new=AsyncMock()
        ) as clear,
        patch.object(cog_mod.economy_service, "refund", new=AsyncMock()) as refund,
        patch.object(
            cog_mod.game_wager_workflow, "recover_escrow", new=AsyncMock()
        ) as recover,
    ):
        await BlackjackCog.on_guild_remove(MagicMock(), guild)

    # Only the pre-debited tournament row (bet>0) is refunded; the bet=0
    # tournament entry and the solo/PvP rows are not.
    refund.assert_awaited_once()
    assert refund.await_args.kwargs["amount"] == 100
    assert refund.await_args.kwargs["user_id"] == 42
    # Every row (tournament x2, solo, pvp) is cleared.
    cleared_ids = {
        c.args[0] if c.args else c.kwargs.get("id") for c in clear.await_args_list
    }
    assert cleared_ids == {1, 2, 10, 20}
    # Stranded PvP escrow recovered for the departing guild.
    recover.assert_awaited_once()
    assert recover.await_args.kwargs["guild_id"] == 7


@pytest.mark.asyncio
async def test_on_guild_remove_survives_refund_failure():
    """A refund error must not abort the rest of the cleanup."""
    import cogs.blackjack_cog as cog_mod
    from cogs.blackjack_cog import (
        BLACKJACK_TOURNAMENT_SUBSYSTEM,
        BlackjackCog,
    )

    guild = MagicMock()
    guild.id = 7

    def _by_subsystem(subsystem, *, guild_id):
        if subsystem == BLACKJACK_TOURNAMENT_SUBSYSTEM:
            return [_row(1, bet=100)]
        return []

    with (
        patch.object(
            cog_mod.game_state_service,
            "list_active_for_subsystem",
            new=AsyncMock(side_effect=_by_subsystem),
        ),
        patch.object(
            cog_mod.game_state_service, "clear_by_id", new=AsyncMock()
        ) as clear,
        patch.object(
            cog_mod.economy_service,
            "refund",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ),
        patch.object(
            cog_mod.game_wager_workflow, "recover_escrow", new=AsyncMock()
        ) as recover,
    ):
        await BlackjackCog.on_guild_remove(MagicMock(), guild)

    # The row is still cleared and escrow recovery still runs despite the
    # refund blowing up.
    clear.assert_awaited()
    recover.assert_awaited_once()


# ---------------------------------------------------------------------------
# 3. Natural-blackjack auto-payout
# ---------------------------------------------------------------------------


def _fake_actor(id_):
    actor = MagicMock()
    actor.id = id_
    return actor


@pytest.mark.asyncio
async def test_natural_blackjack_pays_out_and_clears_slot():
    from cogs.blackjack import actions
    from services.blackjack_state import _active

    user = _fake_actor(42)
    guild = _fake_actor(7)
    channel = _fake_actor(99)
    _active.pop((42, 7), None)

    with (
        patch.object(actions, "_is_blackjack", return_value=True),
        patch.object(
            actions.economy_service, "credit", new=AsyncMock(return_value=160)
        ) as credit,
        patch.object(actions.db, "get_coins", new=AsyncMock(return_value=1000)),
    ):
        result = await actions.start_solo_blackjack(user, guild, channel, 100)

    # Natural → immediate payout, no playable hand returned.
    assert result.embed is not None
    assert result.view is None
    assert result.game is None
    # 1.5x the 100 bet credited via the audited economy seam.
    credit.assert_awaited_once()
    assert credit.await_args.args[2] == 150
    assert credit.await_args.kwargs["reason"] == "blackjack:natural_blackjack"
    # The active slot is released so the player can deal again.
    assert (42, 7) not in _active


@pytest.mark.asyncio
async def test_natural_blackjack_free_play_uses_flat_win():
    from cogs.blackjack import actions
    from services.blackjack_state import FREE_WIN_COINS, _active

    user = _fake_actor(42)
    guild = _fake_actor(7)
    channel = _fake_actor(99)
    _active.pop((42, 7), None)

    with (
        patch.object(actions, "_is_blackjack", return_value=True),
        patch.object(
            actions.economy_service,
            "credit",
            new=AsyncMock(return_value=FREE_WIN_COINS),
        ) as credit,
    ):
        result = await actions.start_solo_blackjack(user, guild, channel, 0)

    assert result.view is None
    credit.assert_awaited_once()
    # bet=0 → flat free-win payout, not 0.
    assert credit.await_args.args[2] == FREE_WIN_COINS
    assert (42, 7) not in _active
