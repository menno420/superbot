"""treasury_service — transaction membership + failure injection.

The Q-0071 contract under test (mirrors test_shop_purchase_workflow): both legs
of a contribute/disburse run on the SAME workflow-owned connection; nothing is
emitted until the transaction context exits (= committed); an underfunded party
writes nothing and the workflow converts it to a failure result with no emit.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import economy_service
from services import treasury_service as ts


def _txn(sentinel_conn, events):
    @asynccontextmanager
    async def _ctx():
        events.append("txn_enter")
        yield sentinel_conn
        events.append("txn_exit")

    return _ctx


# ---------------------------------------------------------------------------
# contribute
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_contribute_runs_both_legs_on_one_conn_and_emits_after_commit():
    sentinel_conn = MagicMock(name="conn")
    events: list[str] = []

    async def _debit(conn, guild_id, user_id, amount, *, reason, actor_id=None):
        events.append("debit_user")
        assert conn is sentinel_conn
        assert reason == ts.CONTRIBUTE_REASON
        assert amount == 100
        return 400  # user wallet after

    async def _credit_treasury(guild_id, amount, updated_at, *, conn=None):
        events.append("credit_treasury")
        assert conn is sentinel_conn
        assert amount == 100
        return 1100  # pool after

    async def _emit(event, **payload):
        events.append(f"emit:{event}")

    with (
        patch.object(ts.db, "transaction", _txn(sentinel_conn, events)),
        patch.object(ts.economy_service, "debit_in_txn", AsyncMock(side_effect=_debit)),
        patch.object(ts.db, "credit_treasury", AsyncMock(side_effect=_credit_treasury)),
        patch.object(ts.bus, "emit", AsyncMock(side_effect=_emit)),
    ):
        result = await ts.contribute(guild_id=1, user_id=99, amount=100)

    assert events == [
        "txn_enter",
        "debit_user",
        "credit_treasury",
        "txn_exit",
        "emit:economy.balance_changed",
    ]
    assert result.success is True
    assert result.treasury_balance == 1100
    assert result.user_balance == 400


@pytest.mark.asyncio
async def test_contribute_insufficient_funds_rolls_back_and_does_not_emit():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _failing_txn():
        yield sentinel_conn

    with (
        patch.object(ts.db, "transaction", _failing_txn),
        patch.object(
            ts.economy_service,
            "debit_in_txn",
            AsyncMock(side_effect=economy_service.InsufficientFundsError("no")),
        ),
        patch.object(ts.db, "credit_treasury", AsyncMock()) as credit_treasury,
        patch.object(ts.db, "get_coins", AsyncMock(return_value=5)),
        patch.object(ts.bus, "emit", AsyncMock()) as emit,
    ):
        result = await ts.contribute(guild_id=1, user_id=99, amount=100)

    assert result.success is False
    assert "5" in result.message
    credit_treasury.assert_not_called()
    emit.assert_not_called()


@pytest.mark.asyncio
async def test_contribute_rejects_non_positive_before_any_io():
    with patch.object(ts.db, "transaction", MagicMock()) as txn:
        with pytest.raises(ValueError, match="must be positive"):
            await ts.contribute(guild_id=1, user_id=99, amount=0)
    txn.assert_not_called()


# ---------------------------------------------------------------------------
# disburse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_disburse_debits_pool_then_credits_user_and_emits_after_commit():
    sentinel_conn = MagicMock(name="conn")
    events: list[str] = []

    async def _try_debit_treasury(guild_id, amount, updated_at, *, conn=None):
        events.append("debit_treasury")
        assert conn is sentinel_conn
        assert amount == 50
        return 950  # pool after

    async def _credit(conn, guild_id, user_id, amount, *, reason, actor_id=None):
        events.append("credit_user")
        assert conn is sentinel_conn
        assert reason == ts.DISBURSE_REASON
        assert actor_id == 7  # the manager who ran the grant
        return 250  # target wallet after

    async def _emit(event, **payload):
        events.append(f"emit:{event}")

    with (
        patch.object(ts.db, "transaction", _txn(sentinel_conn, events)),
        patch.object(
            ts.db,
            "try_debit_treasury",
            AsyncMock(side_effect=_try_debit_treasury),
        ),
        patch.object(
            ts.economy_service, "credit_in_txn", AsyncMock(side_effect=_credit)
        ),
        patch.object(ts.bus, "emit", AsyncMock(side_effect=_emit)),
    ):
        result = await ts.disburse(guild_id=1, actor_id=7, target_id=99, amount=50)

    assert events == [
        "txn_enter",
        "debit_treasury",
        "credit_user",
        "txn_exit",
        "emit:economy.balance_changed",
    ]
    assert result.success is True
    assert result.treasury_balance == 950
    assert result.user_balance == 250


@pytest.mark.asyncio
async def test_disburse_underfunded_pool_writes_nothing_and_does_not_emit():
    sentinel_conn = MagicMock(name="conn")
    events: list[str] = []

    with (
        patch.object(ts.db, "transaction", _txn(sentinel_conn, events)),
        patch.object(ts.db, "try_debit_treasury", AsyncMock(return_value=None)),
        patch.object(ts.db, "get_treasury", AsyncMock(return_value=20)),
        patch.object(ts.economy_service, "credit_in_txn", AsyncMock()) as credit_user,
        patch.object(ts.bus, "emit", AsyncMock()) as emit,
    ):
        result = await ts.disburse(guild_id=1, actor_id=7, target_id=99, amount=50)

    assert result.success is False
    assert result.treasury_balance == 20
    assert "20" in result.message
    credit_user.assert_not_called()
    emit.assert_not_called()


@pytest.mark.asyncio
async def test_disburse_rejects_non_positive_before_any_io():
    with patch.object(ts.db, "transaction", MagicMock()) as txn:
        with pytest.raises(ValueError, match="must be positive"):
            await ts.disburse(guild_id=1, actor_id=7, target_id=99, amount=-5)
    txn.assert_not_called()
