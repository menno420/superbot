"""R6 regression test: restore_anchors must be a no-op on second call.

on_ready fires on every Discord gateway reconnect.  Without an
idempotency guard, restore_anchors would call bot.add_view() for every
anchor on each reconnect, registering duplicate view instances bound to
the same message id.  discord.py would then dispatch the same
interaction to every duplicate.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.runtime import message_anchor_manager


@pytest.fixture(autouse=True)
def _reset_state():
    message_anchor_manager.reset_restoration_state()
    yield
    message_anchor_manager.reset_restoration_state()


@pytest.mark.asyncio
async def test_first_call_runs_restoration():
    anchors = [
        {
            "anchor_id": "a1",
            "subsystem": "role",
            "message_id": 100,
            "user_id": 1,
            "guild_id": 2,
            "channel_id": 3,
        },
    ]
    bot = MagicMock()
    bot.add_view = MagicMock()
    with (
        patch(
            "core.runtime.message_anchor_manager.db.get_all_active_panel_anchors",
            new_callable=AsyncMock,
            return_value=anchors,
        ),
        patch(
            "core.runtime.persistent_views.get_view_class",
            return_value=MagicMock(return_value=MagicMock()),
        ),
        patch(
            "core.runtime.message_anchor_manager.metrics.anchor_restore_total"
        ),
    ):
        await message_anchor_manager.restore_anchors(bot)
        bot.add_view.assert_called_once()


@pytest.mark.asyncio
async def test_second_call_is_noop():
    anchors = [
        {
            "anchor_id": "a1",
            "subsystem": "role",
            "message_id": 100,
            "user_id": 1,
            "guild_id": 2,
            "channel_id": 3,
        },
    ]
    bot = MagicMock()
    bot.add_view = MagicMock()
    with (
        patch(
            "core.runtime.message_anchor_manager.db.get_all_active_panel_anchors",
            new_callable=AsyncMock,
            return_value=anchors,
        ),
        patch(
            "core.runtime.persistent_views.get_view_class",
            return_value=MagicMock(return_value=MagicMock()),
        ),
        patch(
            "core.runtime.message_anchor_manager.metrics.anchor_restore_total"
        ),
    ):
        await message_anchor_manager.restore_anchors(bot)
        await message_anchor_manager.restore_anchors(bot)
        await message_anchor_manager.restore_anchors(bot)
        # Three reconnects, exactly ONE add_view call — duplicates blocked.
        bot.add_view.assert_called_once()


@pytest.mark.asyncio
async def test_reset_allows_re_restore():
    anchors = [
        {
            "anchor_id": "a1",
            "subsystem": "role",
            "message_id": 100,
            "user_id": 1,
            "guild_id": 2,
            "channel_id": 3,
        },
    ]
    bot = MagicMock()
    bot.add_view = MagicMock()
    with (
        patch(
            "core.runtime.message_anchor_manager.db.get_all_active_panel_anchors",
            new_callable=AsyncMock,
            return_value=anchors,
        ),
        patch(
            "core.runtime.persistent_views.get_view_class",
            return_value=MagicMock(return_value=MagicMock()),
        ),
        patch(
            "core.runtime.message_anchor_manager.metrics.anchor_restore_total"
        ),
    ):
        await message_anchor_manager.restore_anchors(bot)
        message_anchor_manager.reset_restoration_state()
        await message_anchor_manager.restore_anchors(bot)
        assert bot.add_view.call_count == 2
