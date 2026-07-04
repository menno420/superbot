"""PR G5 / P0-1 — blackjack tournament persists per-player entry fees.

Tournaments are the highest-stakes path in the cog: each player's
entry_fee is debited BEFORE any rounds run.  Since P0-1 the debit and
the recovery row are written together by
``services.game_wager_workflow.enter_tournament`` (one transaction), so
a crash can no longer leave the money in limbo.

The persistence design is per-player rows (one row per registered
participant) — avoids the "sentinel user_id for guild-wide state"
problem entirely.  Recovery refunds each row's ``bet`` (which equals
the entry_fee) via ``economy_service.refund`` with a filterable
reason, then deletes the row.  Natural completion is handled by
``payout_tournament``: it credits the winner and deletes the rows in
one idempotent transaction, so a replay cannot double-pay.

The ``_save_tournament_entry`` / ``_clear_tournament_entry`` helpers
exercised below remain the row read/write primitives; P0-1 moved the
*money* atomicity into ``enter_tournament`` / ``payout_tournament``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _tournament_row(id_=1, version=1, *, guild_id=111, user_id=222, bet=100):
    return {
        "id": id_,
        "guild_id": guild_id,
        "user_id": user_id,
        "channel_id": 333,
        "subsystem": "blackjack_tournament",
        "state": {"bet": bet, "rounds": 5},
        "version": version,
        "updated_at": "2025-01-01",
    }


@pytest.mark.asyncio
async def test_save_tournament_entry_writes_bet_and_rounds():
    from cogs.blackjack_cog import (
        BLACKJACK_TOURNAMENT_SUBSYSTEM,
        BLACKJACK_TOURNAMENT_VERSION,
        _save_tournament_entry,
    )

    with patch(
        "cogs.blackjack._persistence.game_state_service.save",
        new_callable=AsyncMock,
    ) as mock_save:
        await _save_tournament_entry(
            guild_id=111,
            user_id=222,
            channel_id=333,
            entry_fee=100,
            rounds=5,
        )
    mock_save.assert_awaited_once()
    kwargs = mock_save.await_args.kwargs
    assert kwargs["subsystem"] == BLACKJACK_TOURNAMENT_SUBSYSTEM
    assert kwargs["version"] == BLACKJACK_TOURNAMENT_VERSION
    assert kwargs["guild_id"] == 111
    assert kwargs["user_id"] == 222
    assert kwargs["channel_id"] == 333
    assert kwargs["state"]["bet"] == 100  # matches G0 GC convention
    assert kwargs["state"]["rounds"] == 5


@pytest.mark.asyncio
async def test_save_tournament_entry_failure_is_logged_not_raised():
    from cogs.blackjack_cog import _save_tournament_entry

    with patch(
        "cogs.blackjack._persistence.game_state_service.save",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB down"),
    ):
        await _save_tournament_entry(
            guild_id=111,
            user_id=222,
            channel_id=333,
            entry_fee=100,
            rounds=5,
        )


@pytest.mark.asyncio
async def test_clear_tournament_entry_uses_natural_key():
    from cogs.blackjack_cog import (
        BLACKJACK_TOURNAMENT_SUBSYSTEM,
        _clear_tournament_entry,
    )

    with patch(
        "cogs.blackjack._persistence.game_state_service.clear",
        new_callable=AsyncMock,
    ) as mock_clear:
        await _clear_tournament_entry(
            guild_id=111,
            user_id=222,
            channel_id=333,
        )
    kwargs = mock_clear.await_args.kwargs
    assert kwargs["subsystem"] == BLACKJACK_TOURNAMENT_SUBSYSTEM
    assert kwargs["guild_id"] == 111
    assert kwargs["user_id"] == 222
    assert kwargs["channel_id"] == 333


@pytest.mark.asyncio
async def test_recover_blackjack_tournament_refunds_each_row():
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog.__new__(BlackjackCog)
    rows = [
        _tournament_row(1, user_id=222, bet=100),
        _tournament_row(2, user_id=333, bet=50),
        _tournament_row(3, user_id=444, bet=200),
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
        await cog._recover_blackjack_tournament()
    # Every row was refunded with its bet amount.
    assert mock_refund.await_count == 3
    refunds = {
        (c.kwargs["user_id"], c.kwargs["amount"]) for c in mock_refund.await_args_list
    }
    assert refunds == {(222, 100), (333, 50), (444, 200)}
    # Reason string is filterable in economy_audit_log.
    for c in mock_refund.await_args_list:
        assert "blackjack_tournament:restart_refund" == c.kwargs["reason"]
    # Every row was cleared.
    cleared = {c.args[0] for c in mock_clear.await_args_list}
    assert cleared == {1, 2, 3}


@pytest.mark.asyncio
async def test_recover_blackjack_tournament_refunds_version_mismatch():
    """A VERSION bump must NOT forfeit live tournament entry fees.

    The entry fee was debited at launch and is owed regardless of the
    state-schema version, so recovery refunds the row's ``bet`` (guarded
    by the int>0 sanity check) and then clears it even when the saved
    version differs from the current one.  Owner decision 2026-07-03:
    the money is really lost in the common case where ``bet`` is
    unchanged, and whoever bumps the version owns keeping ``bet`` = the
    entry fee (or updating this handler).  Previously the mismatch branch
    cleared the row without refunding.
    """
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog.__new__(BlackjackCog)
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
        await cog._recover_blackjack_tournament()
    mock_refund.assert_awaited_once()
    assert mock_refund.await_args.kwargs["user_id"] == 222
    assert mock_refund.await_args.kwargs["amount"] == 999
    assert (
        mock_refund.await_args.kwargs["reason"]
        == "blackjack_tournament:restart_refund"
    )
    mock_clear.assert_awaited_once_with(7)


@pytest.mark.asyncio
async def test_recover_blackjack_tournament_refund_failure_still_clears_row():
    """A permanently-failing refund must not loop forever — log a
    warning and proceed with the clear.  The 24 h GC sweep will retry
    if the row somehow re-appears.
    """
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog.__new__(BlackjackCog)
    rows = [_tournament_row(9, bet=100)]
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
            side_effect=RuntimeError("refund DB hiccup"),
        ),
    ):
        await cog._recover_blackjack_tournament()
    mock_clear.assert_awaited_once_with(9)


@pytest.mark.asyncio
async def test_recover_blackjack_tournament_zero_bet_does_not_refund():
    """Free-play tournaments (entry_fee=0) carry bet=0 in the payload.
    No refund is issued; the row is still cleared.
    """
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog.__new__(BlackjackCog)
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
        await cog._recover_blackjack_tournament()
    mock_refund.assert_not_called()
    mock_clear.assert_awaited_once_with(11)


@pytest.mark.asyncio
async def test_on_guild_remove_refunds_tournament_entries_for_guild():
    """on_guild_remove now triggers refunds for the tournament subsystem
    in addition to clearing the rows.
    """
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog.__new__(BlackjackCog)
    guild = MagicMock()
    guild.id = 999

    async def fake_list(subsystem, *, guild_id):
        assert guild_id == 999
        if subsystem == "blackjack_tournament":
            return [
                _tournament_row(1, guild_id=999, user_id=222, bet=100),
                _tournament_row(2, guild_id=999, user_id=333, bet=50),
            ]
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
    # Both tournament rows refunded with their bets.
    refunds = {
        (c.kwargs["user_id"], c.kwargs["amount"]) for c in mock_refund.await_args_list
    }
    assert refunds == {(222, 100), (333, 50)}
    for c in mock_refund.await_args_list:
        assert "blackjack_tournament:guild_remove_refund" == c.kwargs["reason"]
    # Both tournament rows cleared.
    assert mock_clear.await_count >= 2
