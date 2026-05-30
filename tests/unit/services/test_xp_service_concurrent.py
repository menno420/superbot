"""Concurrent-invocation tests for xp_service (P1 PR-8).

Mirrors the economy_service concurrent tests.  Catches regressions
where the service layer accidentally serializes / collapses /
loses events under asyncio.gather.

Real DB-layer race protection comes from db.add_xp's UPSERT …
RETURNING; that's a Postgres property and isn't exercised here.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from services import xp_service
from services.xp_service import EVT_LEVEL_UP, EVT_XP_AWARDED, EVT_XP_RESET

_N = 20


@pytest.mark.asyncio
async def test_award_under_concurrency_emits_per_call():
    """N concurrent awards must produce N EVT_XP_AWARDED emits."""
    with (
        patch(
            "services.xp_service.db.add_xp",
            new_callable=AsyncMock,
            return_value=(100, 1, False),
        ) as add_xp,
        patch(
            "services.xp_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        results = await asyncio.gather(
            *(
                xp_service.award(
                    guild_id=1, user_id=i, amount=10, source=f"test:{i}",
                )
                for i in range(_N)
            ),
        )

    assert add_xp.await_count == _N
    assert len(results) == _N
    # No level-ups → exactly N emits of EVT_XP_AWARDED.
    assert emit.await_count == _N
    for call in emit.await_args_list:
        assert call.args[0] == EVT_XP_AWARDED


@pytest.mark.asyncio
async def test_award_with_level_up_emits_two_events_per_call():
    """Every level-up grant emits BOTH EVT_XP_AWARDED and EVT_LEVEL_UP."""
    with (
        patch(
            "services.xp_service.db.add_xp",
            new_callable=AsyncMock,
            return_value=(500, 5, True),
        ),
        patch(
            "services.xp_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await asyncio.gather(
            *(
                xp_service.award(
                    guild_id=1, user_id=i, amount=100, source=f"test:{i}",
                )
                for i in range(_N)
            ),
        )

    assert emit.await_count == _N * 2  # two emits per call
    awarded = [c for c in emit.await_args_list if c.args[0] == EVT_XP_AWARDED]
    level_up = [c for c in emit.await_args_list if c.args[0] == EVT_LEVEL_UP]
    assert len(awarded) == _N
    assert len(level_up) == _N


@pytest.mark.asyncio
async def test_reset_under_concurrency_emits_per_call():
    with (
        patch(
            "services.xp_service.db.delete_xp",
            new_callable=AsyncMock,
        ) as delete_xp,
        patch(
            "services.xp_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
        patch(
            "services.xp_service.emit_audit_action",
            new_callable=AsyncMock,
        ),
    ):
        await asyncio.gather(
            *(
                xp_service.reset(guild_id=1, user_id=i, source=f"test:{i}")
                for i in range(_N)
            ),
        )

    assert delete_xp.await_count == _N
    assert emit.await_count == _N
    for call in emit.await_args_list:
        assert call.args[0] == EVT_XP_RESET


@pytest.mark.asyncio
async def test_award_rejects_non_positive_under_concurrency():
    """Every invalid call must raise; no emit, no DB write should leak."""
    with (
        patch(
            "services.xp_service.db.add_xp",
            new_callable=AsyncMock,
        ) as add_xp,
        patch(
            "services.xp_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        results = await asyncio.gather(
            *(
                xp_service.award(guild_id=1, user_id=i, amount=0, source="x")
                for i in range(_N)
            ),
            return_exceptions=True,
        )

    assert all(isinstance(r, ValueError) for r in results)
    add_xp.assert_not_awaited()
    emit.assert_not_awaited()
