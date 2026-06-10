"""shop_purchase_workflow — transaction membership + failure injection.

The Q-0071 contract under test: both purchase legs (unique-item grant +
audited debit) run on the SAME workflow-owned connection; nothing is
emitted until the transaction context has exited (= committed); any
failure inside the context leaves no leg committed (rollback is the
transaction's job — these tests pin that no code path emits or writes
outside it).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import economy_service
from services import shop_purchase_workflow as wf


def _txn(sentinel_conn, events):
    @asynccontextmanager
    async def _ctx():
        events.append("txn_enter")
        yield sentinel_conn
        events.append("txn_exit")

    return _ctx


@pytest.mark.asyncio
async def test_success_runs_both_legs_on_one_conn_and_emits_after_commit():
    sentinel_conn = MagicMock(name="conn")
    events: list[str] = []

    async def _grant(user_id, guild_id, item_name, *, conn=None):
        events.append("grant")
        assert conn is sentinel_conn
        return True

    async def _debit(conn, guild_id, user_id, amount, *, reason, actor_id=None):
        events.append("debit")
        assert conn is sentinel_conn
        assert reason == "shop:car"
        assert amount == 10
        return 58

    async def _emit(event, **payload):
        events.append(f"emit:{event}")

    with (
        patch.object(wf.db, "transaction", _txn(sentinel_conn, events)),
        patch.object(
            wf.db,
            "try_grant_unique_item",
            AsyncMock(side_effect=_grant),
        ),
        patch.object(
            wf.economy_service,
            "debit_in_txn",
            AsyncMock(side_effect=_debit),
        ),
        patch.object(wf.bus, "emit", AsyncMock(side_effect=_emit)),
    ):
        result = await wf.purchase_unique_item(99, 1, "car", 10, actor_id=1)

    assert events == [
        "txn_enter",
        "grant",
        "debit",
        "txn_exit",
        "emit:economy.balance_changed",
    ]
    assert result.ok is True
    assert result.new_balance == 58
    assert result.price == 10


@pytest.mark.asyncio
async def test_already_owned_short_circuits_without_debit_or_emit():
    sentinel_conn = MagicMock(name="conn")
    events: list[str] = []

    with (
        patch.object(wf.db, "transaction", _txn(sentinel_conn, events)),
        patch.object(
            wf.db,
            "try_grant_unique_item",
            AsyncMock(return_value=False),
        ),
        patch.object(wf.economy_service, "debit_in_txn", AsyncMock()) as debit,
        patch.object(wf.bus, "emit", AsyncMock()) as emit,
    ):
        result = await wf.purchase_unique_item(99, 1, "car", 10)

    assert result.already_owned is True
    assert result.ok is False
    debit.assert_not_called()
    emit.assert_not_called()


@pytest.mark.asyncio
async def test_insufficient_funds_rolls_back_grant_and_reports_balance():
    """The debit raising inside the context propagates through it (=
    rollback in production); the workflow converts it to a result with
    the current balance and emits nothing."""
    sentinel_conn = MagicMock(name="conn")
    events: list[str] = []

    @asynccontextmanager
    async def _failing_txn():
        events.append("txn_enter")
        try:
            yield sentinel_conn
        finally:
            events.append("txn_unwind")

    with (
        patch.object(wf.db, "transaction", _failing_txn),
        patch.object(
            wf.db,
            "try_grant_unique_item",
            AsyncMock(return_value=True),
        ),
        patch.object(
            wf.economy_service,
            "debit_in_txn",
            AsyncMock(side_effect=economy_service.InsufficientFundsError("no")),
        ),
        patch.object(wf.db, "get_coins", AsyncMock(return_value=3)) as get_coins,
        patch.object(wf.bus, "emit", AsyncMock()) as emit,
    ):
        result = await wf.purchase_unique_item(99, 1, "car", 10)

    assert result.insufficient is True
    assert result.ok is False
    assert result.balance == 3
    # The balance read happens after the transaction unwound, on the pool
    # (no conn kwarg) — the rolled-back transaction must not serve it.
    assert events == ["txn_enter", "txn_unwind"]
    assert get_coins.await_args.kwargs.get("conn") is None
    emit.assert_not_called()


@pytest.mark.asyncio
async def test_unexpected_failure_propagates_without_emit():
    sentinel_conn = MagicMock(name="conn")
    events: list[str] = []

    with (
        patch.object(wf.db, "transaction", _txn(sentinel_conn, events)),
        patch.object(
            wf.db,
            "try_grant_unique_item",
            AsyncMock(return_value=True),
        ),
        patch.object(
            wf.economy_service,
            "debit_in_txn",
            AsyncMock(side_effect=RuntimeError("db down")),
        ),
        patch.object(wf.bus, "emit", AsyncMock()) as emit,
    ):
        with pytest.raises(RuntimeError, match="db down"):
            await wf.purchase_unique_item(99, 1, "car", 10)

    emit.assert_not_called()


@pytest.mark.asyncio
async def test_non_positive_price_is_rejected_before_any_io():
    with patch.object(wf.db, "transaction", MagicMock()) as txn:
        with pytest.raises(ValueError, match="price must be positive"):
            await wf.purchase_unique_item(99, 1, "car", 0)
    txn.assert_not_called()
