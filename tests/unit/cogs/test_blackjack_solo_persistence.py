"""PR G2 — blackjack solo persists hand state to game_state.

Bets are NOT pre-debited (the outcome delta is applied at ``_finish``)
so this mirrors the RPS PvP pattern from PR G1: save on every state
change, clear on natural completion, clear-on-cog-load for stranded
rows.  No refund is involved because no money was ever in escrow.

Tournament and PvP blackjack games run through the same _Game and
view classes; persistence is gated to solo-only via the
``_is_solo_game`` predicate so PR G3 / G5 can layer their own
subsystems without colliding.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _solo_row(id_=1, version=1, guild_id=111, user_id=222):
    return {
        "id": id_,
        "guild_id": guild_id,
        "user_id": user_id,
        "channel_id": 333,
        "subsystem": "blackjack_solo",
        "state": {
            "bet": 50,
            "doubled": False,
            "deck": ["AS", "2H"],
            "player": ["KH", "5C"],
            "dealer": ["7D"],
        },
        "version": version,
        "updated_at": "2025-01-01",
    }


@pytest.mark.asyncio
async def test_save_solo_game_writes_state():
    from cogs.blackjack_cog import (
        BLACKJACK_SOLO_SUBSYSTEM,
        BLACKJACK_SOLO_VERSION,
        _Game,
        _save_solo_game,
    )

    game = _Game(user_id=222, guild_id=111, bet=50, channel_id=333)
    with patch(
        "cogs.blackjack_cog.game_state_service.save",
        new_callable=AsyncMock,
    ) as mock_save:
        await _save_solo_game(game)
    mock_save.assert_awaited_once()
    kwargs = mock_save.await_args.kwargs
    assert kwargs["subsystem"] == BLACKJACK_SOLO_SUBSYSTEM
    assert kwargs["version"] == BLACKJACK_SOLO_VERSION
    assert kwargs["guild_id"] == 111
    assert kwargs["user_id"] == 222
    assert kwargs["channel_id"] == 333
    state = kwargs["state"]
    assert state["bet"] == 50
    assert state["doubled"] is False
    assert isinstance(state["deck"], list)
    assert len(state["player"]) == 2
    assert len(state["dealer"]) == 2


@pytest.mark.asyncio
async def test_save_solo_game_skips_pvp_games():
    """``pvp_peer_id is not None`` means it's a PvP game — G3's
    territory, not G2's.  The save helper must no-op.
    """
    from cogs.blackjack_cog import _Game, _save_solo_game

    game = _Game(user_id=222, guild_id=111, bet=50, channel_id=333)
    game.pvp_peer_id = 999  # mark as PvP
    with patch(
        "cogs.blackjack_cog.game_state_service.save",
        new_callable=AsyncMock,
    ) as mock_save:
        await _save_solo_game(game)
    mock_save.assert_not_called()


@pytest.mark.asyncio
async def test_save_solo_game_skips_tournament_games():
    """``tournament_chips is not None`` means it's a tournament game —
    G5's territory, not G2's.  The save helper must no-op.
    """
    from cogs.blackjack_cog import _Game, _save_solo_game

    game = _Game(
        user_id=222,
        guild_id=111,
        bet=0,
        tournament_chips=1000,
        channel_id=333,
    )
    with patch(
        "cogs.blackjack_cog.game_state_service.save",
        new_callable=AsyncMock,
    ) as mock_save:
        await _save_solo_game(game)
    mock_save.assert_not_called()


@pytest.mark.asyncio
async def test_save_solo_game_skips_when_channel_id_missing():
    """Defensive: if channel_id is somehow None, skip the save rather
    than write a row with a NULL key (which would violate the NOT NULL
    constraint on game_state.channel_id).
    """
    from cogs.blackjack_cog import _Game, _save_solo_game

    game = _Game(user_id=222, guild_id=111, bet=50, channel_id=None)
    with patch(
        "cogs.blackjack_cog.game_state_service.save",
        new_callable=AsyncMock,
    ) as mock_save:
        await _save_solo_game(game)
    mock_save.assert_not_called()


@pytest.mark.asyncio
async def test_save_failure_does_not_raise():
    """DB hiccup must not block the user-facing flow.  The in-memory
    _active dict is authoritative; persistence is a best-effort backup.
    """
    from cogs.blackjack_cog import _Game, _save_solo_game

    game = _Game(user_id=222, guild_id=111, bet=50, channel_id=333)
    with patch(
        "cogs.blackjack_cog.game_state_service.save",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB down"),
    ):
        # Must not raise.
        await _save_solo_game(game)


@pytest.mark.asyncio
async def test_clear_solo_game_deletes_state():
    from cogs.blackjack_cog import (
        BLACKJACK_SOLO_SUBSYSTEM,
        _Game,
        _clear_solo_game,
    )

    game = _Game(user_id=222, guild_id=111, bet=50, channel_id=333)
    with patch(
        "cogs.blackjack_cog.game_state_service.clear",
        new_callable=AsyncMock,
    ) as mock_clear:
        await _clear_solo_game(game)
    mock_clear.assert_awaited_once()
    kwargs = mock_clear.await_args.kwargs
    assert kwargs["subsystem"] == BLACKJACK_SOLO_SUBSYSTEM
    assert kwargs["guild_id"] == 111
    assert kwargs["user_id"] == 222
    assert kwargs["channel_id"] == 333


@pytest.mark.asyncio
async def test_clear_solo_game_skips_pvp_and_tournament():
    from cogs.blackjack_cog import _Game, _clear_solo_game

    pvp_game = _Game(user_id=222, guild_id=111, bet=50, channel_id=333)
    pvp_game.pvp_peer_id = 999
    tourn_game = _Game(
        user_id=222,
        guild_id=111,
        bet=0,
        tournament_chips=100,
        channel_id=333,
    )
    with patch(
        "cogs.blackjack_cog.game_state_service.clear",
        new_callable=AsyncMock,
    ) as mock_clear:
        await _clear_solo_game(pvp_game)
        await _clear_solo_game(tourn_game)
    mock_clear.assert_not_called()


@pytest.mark.asyncio
async def test_recover_blackjack_solo_clears_orphan_rows():
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog.__new__(BlackjackCog)
    rows = [_solo_row(7), _solo_row(8), _solo_row(9)]
    with (
        patch(
            "services.game_state_service.list_active_for_subsystem",
            new_callable=AsyncMock,
            return_value=rows,
        ),
        patch(
            "services.game_state_service.clear_by_id",
            new_callable=AsyncMock,
        ) as mock_clear,
    ):
        await cog._recover_blackjack_solo()
    cleared_ids = {c.args[0] for c in mock_clear.await_args_list}
    assert cleared_ids == {7, 8, 9}


@pytest.mark.asyncio
async def test_recover_blackjack_solo_drops_version_mismatch():
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog.__new__(BlackjackCog)
    rows = [_solo_row(42, version=99)]
    with (
        patch(
            "services.game_state_service.list_active_for_subsystem",
            new_callable=AsyncMock,
            return_value=rows,
        ),
        patch(
            "services.game_state_service.clear_by_id",
            new_callable=AsyncMock,
        ) as mock_clear,
    ):
        await cog._recover_blackjack_solo()
    mock_clear.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_recover_blackjack_solo_list_failure_is_logged_not_raised():
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog.__new__(BlackjackCog)
    with patch(
        "services.game_state_service.list_active_for_subsystem",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB down"),
    ):
        # Must not raise.
        await cog._recover_blackjack_solo()


@pytest.mark.asyncio
async def test_on_guild_remove_wipes_rows_for_guild():
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog.__new__(BlackjackCog)
    guild = MagicMock()
    guild.id = 999
    rows = [_solo_row(1, guild_id=999), _solo_row(2, guild_id=999)]
    with (
        patch(
            "services.game_state_service.list_active_for_subsystem",
            new_callable=AsyncMock,
            return_value=rows,
        ) as mock_list,
        patch(
            "services.game_state_service.clear_by_id",
            new_callable=AsyncMock,
        ) as mock_clear,
    ):
        await cog.on_guild_remove(guild)
    assert mock_list.await_args.kwargs.get("guild_id") == 999
    assert mock_clear.await_count == 2
