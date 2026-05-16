"""PR G3 — blackjack PvP persists match state to game_state.

Pattern: single row per match (canonical user_id = ``min(p1, p2)``)
captures both players' hands plus the ``_PvPState.results`` dict.
Settlement happens at ``_resolve_pvp``; bets are NOT pre-debited.
Recovery is cancel-and-clear because live views cannot be re-attached.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _pvp_row(id_=1, version=1, guild_id=111, p1=100, p2=200):
    return {
        "id": id_,
        "guild_id": guild_id,
        "user_id": min(p1, p2),
        "channel_id": 333,
        "subsystem": "blackjack_pvp",
        "state": {
            "p1_id": p1,
            "p2_id": p2,
            "bet": 50,
            "results": {},
            "p1_game": {
                "bet": 50,
                "doubled": False,
                "deck": ["AS"],
                "player": ["KH", "5C"],
                "dealer": ["7D"],
            },
            "p2_game": {
                "bet": 50,
                "doubled": False,
                "deck": ["2D"],
                "player": ["JH", "QC"],
                "dealer": ["8S"],
            },
        },
        "version": version,
        "updated_at": "2025-01-01",
    }


@pytest.mark.asyncio
async def test_save_pvp_match_writes_both_hands():
    from cogs.blackjack_cog import (
        BLACKJACK_PVP_SUBSYSTEM,
        BLACKJACK_PVP_VERSION,
        _active,
        _Game,
        _PvPState,
        _save_pvp_match,
    )

    state = _PvPState(p1=100, p2=200, guild_id=111, bet=50, channel_id=333)
    g1 = _Game(100, 111, 50, channel_id=333)
    g1.pvp_peer_id = 200
    g1.pvp_state = state
    g2 = _Game(200, 111, 50, channel_id=333)
    g2.pvp_peer_id = 100
    g2.pvp_state = state
    _active[(100, 111)] = g1
    _active[(200, 111)] = g2

    try:
        with patch(
            "cogs.blackjack_cog.game_state_service.save",
            new_callable=AsyncMock,
        ) as mock_save:
            await _save_pvp_match(state)
        mock_save.assert_awaited_once()
        kwargs = mock_save.await_args.kwargs
        assert kwargs["subsystem"] == BLACKJACK_PVP_SUBSYSTEM
        assert kwargs["version"] == BLACKJACK_PVP_VERSION
        assert kwargs["guild_id"] == 111
        # Canonical user_id is min(p1, p2).
        assert kwargs["user_id"] == 100
        assert kwargs["channel_id"] == 333
        st = kwargs["state"]
        assert st["p1_id"] == 100
        assert st["p2_id"] == 200
        assert st["bet"] == 50
        # Both hands are serialised.
        assert st["p1_game"]["player"] == g1.player
        assert st["p2_game"]["player"] == g2.player
    finally:
        _active.pop((100, 111), None)
        _active.pop((200, 111), None)


@pytest.mark.asyncio
async def test_save_pvp_match_handles_finished_player():
    """When one player has already finished (popped from _active), the
    serialiser returns None for that side.  The match is still
    persistable so the cog_load sweep can find it.
    """
    from cogs.blackjack_cog import (
        _active,
        _Game,
        _PvPState,
        _save_pvp_match,
    )

    state = _PvPState(p1=100, p2=200, guild_id=111, bet=50, channel_id=333)
    state.results = {100: 19}  # p1 finished with hand value 19
    g2 = _Game(200, 111, 50, channel_id=333)
    g2.pvp_peer_id = 100
    g2.pvp_state = state
    _active[(200, 111)] = g2
    # p1 is NOT in _active — they just finished.

    try:
        with patch(
            "cogs.blackjack_cog.game_state_service.save",
            new_callable=AsyncMock,
        ) as mock_save:
            await _save_pvp_match(state)
        st = mock_save.await_args.kwargs["state"]
        assert st["p1_game"] is None  # finished
        assert st["p2_game"] is not None  # still active
        # results dict is JSON-safe (string keys).
        assert st["results"] == {"100": 19}
    finally:
        _active.pop((200, 111), None)


@pytest.mark.asyncio
async def test_save_pvp_match_failure_is_logged_not_raised():
    from cogs.blackjack_cog import _PvPState, _save_pvp_match

    state = _PvPState(p1=100, p2=200, guild_id=111, bet=50, channel_id=333)
    with patch(
        "cogs.blackjack_cog.game_state_service.save",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB down"),
    ):
        await _save_pvp_match(state)  # must not raise


@pytest.mark.asyncio
async def test_clear_pvp_match_uses_canonical_user_id():
    from cogs.blackjack_cog import (
        BLACKJACK_PVP_SUBSYSTEM,
        _clear_pvp_match,
        _PvPState,
    )

    state = _PvPState(p1=100, p2=200, guild_id=111, bet=50, channel_id=333)
    with patch(
        "cogs.blackjack_cog.game_state_service.clear",
        new_callable=AsyncMock,
    ) as mock_clear:
        await _clear_pvp_match(state)
    kwargs = mock_clear.await_args.kwargs
    assert kwargs["subsystem"] == BLACKJACK_PVP_SUBSYSTEM
    assert kwargs["guild_id"] == 111
    assert kwargs["user_id"] == 100  # canonical
    assert kwargs["channel_id"] == 333


@pytest.mark.asyncio
async def test_save_game_state_dispatches_pvp_vs_solo():
    """The dispatcher must route to the right helper based on
    ``game.pvp_state``.  Solo games go to ``_save_solo_game``; PvP
    games go to ``_save_pvp_match``; tournament games no-op (G5).
    """
    from cogs.blackjack_cog import _Game, _PvPState, _save_game_state

    state = _PvPState(p1=100, p2=200, guild_id=111, bet=50, channel_id=333)
    pvp_game = _Game(100, 111, 50, channel_id=333)
    pvp_game.pvp_peer_id = 200
    pvp_game.pvp_state = state
    solo_game = _Game(300, 111, 25, channel_id=333)
    tourn_game = _Game(400, 111, 0, tournament_chips=500, channel_id=333)

    with (
        patch(
            "cogs.blackjack_cog._save_solo_game",
            new_callable=AsyncMock,
        ) as mock_solo,
        patch(
            "cogs.blackjack_cog._save_pvp_match",
            new_callable=AsyncMock,
        ) as mock_pvp,
    ):
        await _save_game_state(pvp_game)
        await _save_game_state(solo_game)
        await _save_game_state(tourn_game)

    mock_pvp.assert_awaited_once_with(state)
    mock_solo.assert_awaited_once_with(solo_game)
    # Tournament game routes nowhere yet.


@pytest.mark.asyncio
async def test_recover_blackjack_pvp_clears_orphan_rows():
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog.__new__(BlackjackCog)
    rows = [_pvp_row(1), _pvp_row(2), _pvp_row(3)]
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
        await cog._recover_blackjack_pvp()
    cleared_ids = {c.args[0] for c in mock_clear.await_args_list}
    assert cleared_ids == {1, 2, 3}


@pytest.mark.asyncio
async def test_recover_blackjack_pvp_drops_version_mismatch():
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog.__new__(BlackjackCog)
    rows = [_pvp_row(99, version=42)]
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
        await cog._recover_blackjack_pvp()
    mock_clear.assert_awaited_once_with(99)


@pytest.mark.asyncio
async def test_on_guild_remove_clears_both_solo_and_pvp():
    """After PR G3, ``on_guild_remove`` covers BOTH blackjack_solo
    and blackjack_pvp subsystems for the departed guild.
    """
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog.__new__(BlackjackCog)
    guild = MagicMock()
    guild.id = 999
    # Return different rows for each subsystem call.
    seen_subsystems: list[str] = []

    async def fake_list(subsystem, *, guild_id):
        seen_subsystems.append(subsystem)
        return [{"id": hash(subsystem) % 1000}]

    with (
        patch(
            "services.game_state_service.list_active_for_subsystem",
            side_effect=fake_list,
        ),
        patch(
            "services.game_state_service.clear_by_id",
            new_callable=AsyncMock,
        ) as mock_clear,
    ):
        await cog.on_guild_remove(guild)
    # Both subsystems queried.
    assert "blackjack_solo" in seen_subsystems
    assert "blackjack_pvp" in seen_subsystems
    # Each subsystem's row cleared.
    assert mock_clear.await_count == 2
