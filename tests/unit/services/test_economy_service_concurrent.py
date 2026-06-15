"""Concurrent-invocation tests for economy_service (P1 PR-8).

The real concurrency guarantee economy_service provides comes from:
  - asyncpg UPSERT … RETURNING (single-row atomicity)
  - conn.transaction() context manager (transfer's two-row atomicity)

Both rely on Postgres, which isn't available in unit-test CI. What
WE can verify at the asyncio layer is that N concurrent
``await asyncio.gather(*[op() for _ in range(N)])`` invocations:

  - All complete without raising
  - Each invocation emits exactly one EVT_BALANCE_CHANGED
  - Audit rows are written N times (not deduplicated)
  - Mock db.add_coins / db.execute are called N times each (no
    silent collapse)

Catching a regression where a developer adds shared module-level
state to the service (a cache, a counter, a lock) and accidentally
loses events under concurrent calls.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from services import economy_service
from services.economy_service import EVT_BALANCE_CHANGED

_N = 20  # concurrent ops


@pytest.mark.asyncio
async def test_credit_under_concurrency_emits_per_call():
    with (
        patch(
            "services.economy_service.db.add_coins",
            new_callable=AsyncMock,
            return_value=100,
        ) as add_coins,
        patch(
            "services.economy_service.db.insert_economy_audit",
            new_callable=AsyncMock,
        ) as audit,
        patch(
            "services.economy_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await asyncio.gather(
            *(
                economy_service.credit(
                    guild_id=1,
                    user_id=2,
                    amount=10,
                    reason=f"test:{i}",
                )
                for i in range(_N)
            ),
        )

    assert add_coins.await_count == _N
    assert audit.await_count == _N
    assert emit.await_count == _N
    # Every emit is the catalogued event name.
    for call in emit.await_args_list:
        assert call.args[0] == EVT_BALANCE_CHANGED


@pytest.mark.asyncio
async def test_debit_under_concurrency_emits_per_call():
    with (
        patch(
            "services.economy_service.db.get_coins",
            new_callable=AsyncMock,
            return_value=10_000,  # enough for every debit
        ),
        patch(
            "services.economy_service.db.add_coins",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "services.economy_service.db.insert_economy_audit", new_callable=AsyncMock
        ),
        patch(
            "services.economy_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await asyncio.gather(
            *(
                economy_service.debit(
                    guild_id=1,
                    user_id=2,
                    amount=5,
                    reason=f"test:{i}",
                )
                for i in range(_N)
            ),
        )

    assert emit.await_count == _N
    # delta is negative for every emit
    for call in emit.await_args_list:
        assert call.kwargs["delta"] < 0


@pytest.mark.asyncio
async def test_debit_insufficient_funds_raises_before_emit():
    """A failed debit must NOT leak EVT_BALANCE_CHANGED."""
    with (
        patch(
            "services.economy_service.db.get_coins",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "services.economy_service.db.add_coins",
            new_callable=AsyncMock,
        ) as add_coins,
        patch(
            "services.economy_service.db.insert_economy_audit", new_callable=AsyncMock
        ),
        patch(
            "services.economy_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        with pytest.raises(economy_service.InsufficientFundsError):
            await economy_service.debit(
                guild_id=1,
                user_id=2,
                amount=100,
                reason="test",
            )

    add_coins.assert_not_awaited()
    emit.assert_not_awaited()
