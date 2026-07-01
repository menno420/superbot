"""Tests for services.xp_service.import_level (bot-to-bot migration seam)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import xp_service
from utils.db.xp import total_xp_for_level


@pytest.mark.asyncio
async def test_import_level_converts_level_to_xp_and_writes():
    with (
        patch(
            "services.xp_service.db.set_imported_xp",
            new_callable=AsyncMock,
            return_value=(total_xp_for_level(13), 13, True),
        ) as set_xp,
        patch("services.xp_service.bus.emit", new_callable=AsyncMock) as emit,
    ):
        result = await xp_service.import_level(
            guild_id=1,
            user_id=2,
            level=13,
            source="import:arcane",
            now=1000,
        )
    # The scraped *level* is converted to the concrete XP total that reaches it.
    set_xp.assert_awaited_once_with(2, 1, total_xp_for_level(13), 13, 1000)
    assert result.final_level == 13
    assert result.final_xp == total_xp_for_level(13)
    assert result.raised is True
    assert result.source == "import:arcane"
    # A bulk migration must stay silent — no awarded/level-up events.
    assert emit.await_count == 0


@pytest.mark.asyncio
async def test_import_level_reports_not_raised_when_member_already_higher():
    with (
        patch(
            "services.xp_service.db.set_imported_xp",
            new_callable=AsyncMock,
            return_value=(999999, 50, False),  # existing row already higher
        ),
        patch("services.xp_service.bus.emit", new_callable=AsyncMock),
    ):
        result = await xp_service.import_level(
            guild_id=1,
            user_id=2,
            level=13,
            source="import:arcane",
        )
    assert result.raised is False
    assert result.final_level == 50


@pytest.mark.asyncio
async def test_import_level_rejects_negative_level():
    with patch(
        "services.xp_service.db.set_imported_xp",
        new_callable=AsyncMock,
    ) as set_xp:
        with pytest.raises(ValueError, match="level must be >= 0"):
            await xp_service.import_level(
                guild_id=1,
                user_id=2,
                level=-1,
                source="import:arcane",
            )
    set_xp.assert_not_awaited()


@pytest.mark.asyncio
async def test_import_level_zero_targets_zero_xp():
    with (
        patch(
            "services.xp_service.db.set_imported_xp",
            new_callable=AsyncMock,
            return_value=(0, 0, False),
        ) as set_xp,
        patch("services.xp_service.bus.emit", new_callable=AsyncMock),
    ):
        await xp_service.import_level(
            guild_id=1,
            user_id=2,
            level=0,
            source="import:arcane",
            now=5,
        )
    set_xp.assert_awaited_once_with(2, 1, 0, 0, 5)
