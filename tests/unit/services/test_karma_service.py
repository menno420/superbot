"""Tests for services.karma_service — the single audited karma seam.

Verify that ``give``:

- credits the recipient, bumps the giver's given_count, writes an audit
  row, and emits the catalogued EVT_KARMA_GRANTED
- rejects self-karma, non-positive amounts, and a disabled guild
- enforces the per-(giver -> receiver) cooldown and the per-giver daily cap
  via the audit-log reads (no write happens when a rule blocks)
- the event is catalogued (no unknown-event metric fires)
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from core.events_catalogue import KNOWN_EVENTS
from services import karma_service
from services.karma_config import KarmaPolicy
from services.karma_service import (
    EVT_KARMA_GRANTED,
    KarmaCooldownError,
    KarmaDailyCapError,
    KarmaDisabledError,
    SelfKarmaError,
)

_NOW = datetime(2026, 6, 22, 12, 0, 0, tzinfo=timezone.utc)
_POLICY = KarmaPolicy(enabled=True, cooldown_seconds=3600, daily_cap=10)


def test_event_is_catalogued():
    assert EVT_KARMA_GRANTED in KNOWN_EVENTS


class TestGive:
    @pytest.mark.asyncio
    async def test_credits_audits_emits(self):
        with (
            patch(
                "services.karma_service.db.recent_grant_count",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "services.karma_service.db.grants_given_since",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "services.karma_service.db.credit_karma",
                new_callable=AsyncMock,
                return_value=5,
            ),
            patch(
                "services.karma_service.db.increment_given",
                new_callable=AsyncMock,
            ) as given,
            patch(
                "services.karma_service.db.insert_karma_audit",
                new_callable=AsyncMock,
            ) as audit,
            patch(
                "services.karma_service.bus.emit",
                new_callable=AsyncMock,
            ) as emit,
        ):
            grant = await karma_service.give(
                1,
                from_user=10,
                to_user=20,
                source="command",
                reason="helpful",
                now=_NOW,
                policy=_POLICY,
            )
            assert grant.new_total == 5
            assert grant.to_user == 20
            given.assert_awaited_once_with(10, 1)
            audit.assert_awaited_once_with(1, 10, 20, 1, "command", "helpful")
            emit.assert_awaited_once_with(
                EVT_KARMA_GRANTED,
                guild_id=1,
                from_user=10,
                to_user=20,
                delta=1,
                new_total=5,
                source="command",
            )

    @pytest.mark.asyncio
    async def test_self_karma_rejected(self):
        with pytest.raises(SelfKarmaError):
            await karma_service.give(
                1, from_user=10, to_user=10, source="command", policy=_POLICY,
            )

    @pytest.mark.asyncio
    async def test_non_positive_amount_rejected(self):
        with pytest.raises(ValueError, match="positive"):
            await karma_service.give(
                1,
                from_user=10,
                to_user=20,
                amount=0,
                source="command",
                policy=_POLICY,
            )

    @pytest.mark.asyncio
    async def test_disabled_guild_rejected(self):
        disabled = KarmaPolicy(enabled=False)
        with pytest.raises(KarmaDisabledError):
            await karma_service.give(
                1,
                from_user=10,
                to_user=20,
                source="command",
                policy=disabled,
            )

    @pytest.mark.asyncio
    async def test_cooldown_blocks_and_does_not_write(self):
        with (
            patch(
                "services.karma_service.db.recent_grant_count",
                new_callable=AsyncMock,
                return_value=1,
            ),
            patch(
                "services.karma_service.db.credit_karma",
                new_callable=AsyncMock,
            ) as credit,
        ):
            with pytest.raises(KarmaCooldownError):
                await karma_service.give(
                    1,
                    from_user=10,
                    to_user=20,
                    source="command",
                    now=_NOW,
                    policy=_POLICY,
                )
            credit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_daily_cap_blocks_and_does_not_write(self):
        with (
            patch(
                "services.karma_service.db.recent_grant_count",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "services.karma_service.db.grants_given_since",
                new_callable=AsyncMock,
                return_value=10,
            ),
            patch(
                "services.karma_service.db.credit_karma",
                new_callable=AsyncMock,
            ) as credit,
        ):
            with pytest.raises(KarmaDailyCapError):
                await karma_service.give(
                    1,
                    from_user=10,
                    to_user=20,
                    source="command",
                    now=_NOW,
                    policy=_POLICY,
                )
            credit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_zero_cooldown_skips_recent_check(self):
        no_cooldown = KarmaPolicy(enabled=True, cooldown_seconds=0, daily_cap=10)
        with (
            patch(
                "services.karma_service.db.recent_grant_count",
                new_callable=AsyncMock,
            ) as recent,
            patch(
                "services.karma_service.db.grants_given_since",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "services.karma_service.db.credit_karma",
                new_callable=AsyncMock,
                return_value=1,
            ),
            patch(
                "services.karma_service.db.increment_given",
                new_callable=AsyncMock,
            ),
            patch(
                "services.karma_service.db.insert_karma_audit",
                new_callable=AsyncMock,
            ),
            patch("services.karma_service.bus.emit", new_callable=AsyncMock),
        ):
            await karma_service.give(
                1,
                from_user=10,
                to_user=20,
                source="command",
                now=_NOW,
                policy=no_cooldown,
            )
            recent.assert_not_awaited()


class TestGetRecord:
    @pytest.mark.asyncio
    async def test_record_with_rank(self):
        with (
            patch(
                "services.karma_service.db.get_karma",
                new_callable=AsyncMock,
                return_value={
                    "karma_points": 7,
                    "received_count": 7,
                    "given_count": 3,
                    "last_received": None,
                },
            ),
            patch(
                "services.karma_service.db.karma_rank",
                new_callable=AsyncMock,
                return_value=2,
            ),
        ):
            rec = await karma_service.get_record(1, 20)
            assert rec.points == 7
            assert rec.received_count == 7
            assert rec.given_count == 3
            assert rec.rank == 2

    @pytest.mark.asyncio
    async def test_record_zero_is_unranked(self):
        with (
            patch(
                "services.karma_service.db.get_karma",
                new_callable=AsyncMock,
                return_value={
                    "karma_points": 0,
                    "received_count": 0,
                    "given_count": 0,
                    "last_received": None,
                },
            ),
            patch(
                "services.karma_service.db.karma_rank",
                new_callable=AsyncMock,
            ) as rank,
        ):
            rec = await karma_service.get_record(1, 20)
            assert rec.points == 0
            assert rec.rank is None
            rank.assert_not_awaited()
