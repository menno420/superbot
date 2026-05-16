"""PR G6 — RPS tournament persists per-player entry fees.

Mirrors PR G5 for the blackjack tournament path: entry fees debited at
``try_register_player`` and refunded on cog_load / on_guild_remove if
the bot crashed before ``check_tournament_progress`` settled the pot.

Per-player rows are keyed with ``channel_id=0`` (sentinel) because an
RPS tournament is guild-wide, not channel-local.  The natural
game_state UNIQUE constraint on
``(guild_id, user_id, channel_id, subsystem)`` then enforces "one
tournament entry per user per guild", which is also the cog's
in-memory invariant.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _tournament_row(id_=1, version=1, *, guild_id=111, user_id=222, bet=50):
    return {
        "id": id_,
        "guild_id": guild_id,
        "user_id": user_id,
        "channel_id": 0,
        "subsystem": "rps_tournament",
        "state": {"bet": bet},
        "version": version,
        "updated_at": "2025-01-01",
    }


def test_rps_tournament_subsystem_constants_exist():
    """Defensive check: the subsystem string and version must match
    what cog_load recovery looks for.  A typo here would silently
    leave entries stranded forever.
    """
    from cogs.rps_tournament_cog import (
        RPS_TOURNAMENT_SUBSYSTEM,
        RPS_TOURNAMENT_VERSION,
    )

    assert RPS_TOURNAMENT_SUBSYSTEM == "rps_tournament"
    assert RPS_TOURNAMENT_VERSION == 1


def test_try_register_player_wires_through_save():
    """Source-level check that ``try_register_player`` calls
    ``game_state_service.save`` with the documented payload shape.
    Direct invocation requires a fully-initialised cog + economy
    service patching that exceeds unit-test scope; source-grep here
    matches the same pattern PR G1 used for the pvp_challenge wiring.
    """
    import inspect

    from cogs import rps_tournament_cog

    src = inspect.getsource(rps_tournament_cog.RPSTournamentCog.try_register_player)
    assert "game_state_service.save" in src
    assert "RPS_TOURNAMENT_SUBSYSTEM" in src
    assert "RPS_TOURNAMENT_VERSION" in src
    # bet field name matches the G0 GC convention.
    assert '"bet":' in src or "'bet':" in src


@pytest.mark.asyncio
async def test_recover_rps_tournament_refunds_each_row():
    from cogs.rps_tournament_cog import RPSTournamentCog

    cog = RPSTournamentCog.__new__(RPSTournamentCog)
    rows = [
        _tournament_row(1, user_id=222, bet=50),
        _tournament_row(2, user_id=333, bet=100),
    ]
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
        patch(
            "services.economy_service.refund",
            new_callable=AsyncMock,
        ) as mock_refund,
    ):
        await cog._recover_rps_tournament()
    refunds = {
        (c.kwargs["user_id"], c.kwargs["amount"])
        for c in mock_refund.await_args_list
    }
    assert refunds == {(222, 50), (333, 100)}
    for c in mock_refund.await_args_list:
        assert "rps_tournament:restart_refund" == c.kwargs["reason"]
    cleared = {c.args[0] for c in mock_clear.await_args_list}
    assert cleared == {1, 2}


@pytest.mark.asyncio
async def test_recover_rps_tournament_drops_version_mismatch_without_refund():
    from cogs.rps_tournament_cog import RPSTournamentCog

    cog = RPSTournamentCog.__new__(RPSTournamentCog)
    rows = [_tournament_row(7, version=99, bet=999)]
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
        patch(
            "services.economy_service.refund",
            new_callable=AsyncMock,
        ) as mock_refund,
    ):
        await cog._recover_rps_tournament()
    mock_refund.assert_not_called()
    mock_clear.assert_awaited_once_with(7)


@pytest.mark.asyncio
async def test_recover_rps_tournament_zero_bet_clears_without_refund():
    """Free-play tournaments save ``bet=0`` — no refund needed."""
    from cogs.rps_tournament_cog import RPSTournamentCog

    cog = RPSTournamentCog.__new__(RPSTournamentCog)
    rows = [_tournament_row(11, bet=0)]
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
        patch(
            "services.economy_service.refund",
            new_callable=AsyncMock,
        ) as mock_refund,
    ):
        await cog._recover_rps_tournament()
    mock_refund.assert_not_called()
    mock_clear.assert_awaited_once_with(11)


@pytest.mark.asyncio
async def test_on_guild_remove_refunds_tournament_and_clears_pending():
    """on_guild_remove for the RPS cog covers BOTH rps_pvp_pending
    (clear-only) and rps_tournament (refund + clear).
    """
    from cogs.rps_tournament_cog import RPSTournamentCog

    cog = RPSTournamentCog.__new__(RPSTournamentCog)
    guild = MagicMock()
    guild.id = 999

    async def fake_list(subsystem, *, guild_id):
        assert guild_id == 999
        if subsystem == "rps_tournament":
            return [
                _tournament_row(1, guild_id=999, user_id=222, bet=75),
            ]
        if subsystem == "rps_pvp_pending":
            return [{"id": 42, "state": {}}]
        return []

    with (
        patch(
            "services.game_state_service.list_active_for_subsystem",
            side_effect=fake_list,
        ),
        patch(
            "services.game_state_service.clear_by_id",
            new_callable=AsyncMock,
        ) as mock_clear,
        patch(
            "services.economy_service.refund",
            new_callable=AsyncMock,
        ) as mock_refund,
    ):
        await cog.on_guild_remove(guild)
    # Tournament path: refund with the guild-remove reason string.
    mock_refund.assert_awaited_once()
    refund_kwargs = mock_refund.await_args.kwargs
    assert refund_kwargs["user_id"] == 222
    assert refund_kwargs["amount"] == 75
    assert "rps_tournament:guild_remove_refund" == refund_kwargs["reason"]
    # Both rows cleared (tournament + pvp_pending).
    cleared_ids = {c.args[0] for c in mock_clear.await_args_list}
    assert {1, 42} <= cleared_ids
