"""Tests for services.economy_service (S2).

The service is the single path for balance mutations; these tests
verify:

- credit / debit / bet_and_settle write an audit row + emit
  EVT_BALANCE_CHANGED
- debit raises InsufficientFundsError when the user is short
- transfer is atomic (no commit on insufficient funds) and writes two
  audit rows
- non-positive amounts raise ValueError
- the event is catalogued (no unknown-event metric fires)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.events_catalogue import KNOWN_EVENTS
from services import economy_service
from services.economy_service import EVT_BALANCE_CHANGED, InsufficientFundsError


def test_event_is_catalogued():
    assert EVT_BALANCE_CHANGED in KNOWN_EVENTS


class TestCredit:
    @pytest.mark.asyncio
    async def test_credits_audits_emits(self):
        with (
            patch(
                "services.economy_service.db.add_coins",
                new_callable=AsyncMock,
                return_value=150,
            ),
            patch(
                "services.economy_service.db.insert_economy_audit",
                new_callable=AsyncMock,
            ) as audit,
            patch(
                "services.economy_service.bus.emit",
                new_callable=AsyncMock,
            ) as emit,
        ):
            new_bal = await economy_service.credit(
                guild_id=1, user_id=42, amount=50, reason="daily",
            )
            assert new_bal == 150
            audit.assert_awaited_once()
            assert audit.call_args.args == (1, 42, None, 50, 150, "daily")
            emit.assert_awaited_once_with(
                EVT_BALANCE_CHANGED,
                guild_id=1,
                user_id=42,
                delta=50,
                new_balance=150,
                reason="daily",
            )

    @pytest.mark.asyncio
    async def test_negative_amount_rejected(self):
        with pytest.raises(ValueError, match="positive"):
            await economy_service.credit(
                guild_id=1, user_id=2, amount=-5, reason="x",
            )

    @pytest.mark.asyncio
    async def test_zero_amount_rejected(self):
        with pytest.raises(ValueError, match="positive"):
            await economy_service.credit(
                guild_id=1, user_id=2, amount=0, reason="x",
            )


class TestDebit:
    @pytest.mark.asyncio
    async def test_insufficient_funds_raises(self):
        with patch(
            "services.economy_service.db.get_coins",
            new_callable=AsyncMock,
            return_value=10,
        ):
            with pytest.raises(InsufficientFundsError):
                await economy_service.debit(
                    guild_id=1, user_id=2, amount=50, reason="purchase",
                )

    @pytest.mark.asyncio
    async def test_allow_overdraft_succeeds(self):
        with (
            patch(
                "services.economy_service.db.get_coins",
                new_callable=AsyncMock,
                return_value=10,
            ),
            patch(
                "services.economy_service.db.add_coins",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "services.economy_service.db.insert_economy_audit",
                new_callable=AsyncMock,
            ),
            patch(
                "services.economy_service.bus.emit",
                new_callable=AsyncMock,
            ),
        ):
            new_bal = await economy_service.debit(
                guild_id=1,
                user_id=2,
                amount=50,
                reason="forfeit",
                allow_overdraft=True,
            )
            assert new_bal == 0

    @pytest.mark.asyncio
    async def test_sufficient_funds_succeeds_and_audits(self):
        with (
            patch(
                "services.economy_service.db.get_coins",
                new_callable=AsyncMock,
                return_value=100,
            ),
            patch(
                "services.economy_service.db.add_coins",
                new_callable=AsyncMock,
                return_value=80,
            ),
            patch(
                "services.economy_service.db.insert_economy_audit",
                new_callable=AsyncMock,
            ) as audit,
            patch(
                "services.economy_service.bus.emit",
                new_callable=AsyncMock,
            ) as emit,
        ):
            new_bal = await economy_service.debit(
                guild_id=1, user_id=2, amount=20, reason="shop:potion",
            )
            assert new_bal == 80
            # negative delta in audit row
            assert audit.call_args.args == (1, 2, None, -20, 80, "shop:potion")
            assert emit.call_args.kwargs["delta"] == -20


class TestTransfer:
    @pytest.mark.asyncio
    async def test_insufficient_funds_no_commit(self):
        pool = MagicMock()
        conn = MagicMock()
        conn.fetchrow = AsyncMock(return_value={"coins": 5})
        conn.execute = AsyncMock()
        # Build an async context-manager chain for `pool.acquire() as conn`.
        acquire_cm = AsyncMock()
        acquire_cm.__aenter__ = AsyncMock(return_value=conn)
        acquire_cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=acquire_cm)
        tx_cm = AsyncMock()
        tx_cm.__aenter__ = AsyncMock(return_value=None)
        tx_cm.__aexit__ = AsyncMock(return_value=None)
        conn.transaction = MagicMock(return_value=tx_cm)

        with patch("services.economy_service.db.get", return_value=pool):
            with pytest.raises(InsufficientFundsError):
                await economy_service.transfer(
                    guild_id=1,
                    from_user=2,
                    to_user=3,
                    amount=10,
                    reason="gift",
                )
        # Only the SELECT ran — no UPDATE/INSERT.
        assert conn.fetchrow.await_count == 1
        conn.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_same_user_rejected(self):
        with pytest.raises(ValueError, match="differ"):
            await economy_service.transfer(
                guild_id=1, from_user=2, to_user=2, amount=10, reason="x",
            )


class TestBetAndSettle:
    @pytest.mark.asyncio
    async def test_win_increments_balance(self):
        with (
            patch(
                "services.economy_service.db.get_coins",
                new_callable=AsyncMock,
                return_value=100,
            ),
            patch(
                "services.economy_service.db.add_coins",
                new_callable=AsyncMock,
                return_value=200,
            ),
            patch(
                "services.economy_service.db.insert_economy_audit",
                new_callable=AsyncMock,
            ),
            patch(
                "services.economy_service.bus.emit",
                new_callable=AsyncMock,
            ) as emit,
        ):
            new_bal = await economy_service.bet_and_settle(
                guild_id=1,
                user_id=2,
                bet=50,
                outcome_delta=100,
                reason="blackjack:win",
            )
            assert new_bal == 200
            assert emit.call_args.kwargs["delta"] == 100

    @pytest.mark.asyncio
    async def test_cannot_afford_bet(self):
        with patch(
            "services.economy_service.db.get_coins",
            new_callable=AsyncMock,
            return_value=5,
        ):
            with pytest.raises(InsufficientFundsError):
                await economy_service.bet_and_settle(
                    guild_id=1,
                    user_id=2,
                    bet=50,
                    outcome_delta=-50,
                    reason="blackjack:lose",
                )


# ---------------------------------------------------------------------------
# refund() — P2 PR-13: shutdown / cancelled-game money return
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refund_credits_amount_with_reason_attribution():
    with (
        patch(
            "services.economy_service.db.add_coins",
            new_callable=AsyncMock,
            return_value=750,
        ) as add_coins,
        patch(
            "services.economy_service.db.insert_economy_audit",
            new_callable=AsyncMock,
        ),
        patch(
            "services.economy_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        new_balance = await economy_service.refund(
            guild_id=1,
            user_id=2,
            amount=250,
            reason="blackjack:refund:shutdown",
            actor_id=None,
        )

    assert new_balance == 750
    add_coins.assert_awaited_once_with(2, 1, 250)
    emit.assert_awaited_once()
    assert emit.await_args.kwargs["delta"] == 250
    assert emit.await_args.kwargs["reason"] == "blackjack:refund:shutdown"
