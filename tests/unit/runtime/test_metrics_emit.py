"""Tests that the F7 observability metrics fire at the expected emit sites.

Covers:
- interaction_router: interaction_unhandled_total on missing prefix handler
- interaction_router: governance_fail_open_total when governance throws
- message_anchor_manager: anchor_restore_total for ok / view_missing / restore_failed
- live_update_scheduler: panel_refresh_total for ok / skipped / refresh_fn_error /
  channel_missing / message_not_found / forbidden / http_error
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from core.runtime import interaction_router, live_update_scheduler, message_anchor_manager


def _interaction(custom_id: str) -> MagicMock:
    i = MagicMock()
    i.custom_id = custom_id
    i.data = {"custom_id": custom_id}
    i.user = MagicMock()
    i.user.id = 42
    i.guild_id = None  # skip governance gate path by default
    i.channel_id = None
    i.response = MagicMock()
    i.response.is_done = MagicMock(return_value=False)
    i.response.send_message = AsyncMock()
    return i


class TestInteractionRouterMetrics:
    @pytest.mark.asyncio
    async def test_unhandled_prefix_increments_counter(self):
        i = _interaction("ghost:foo")
        with patch(
            "core.runtime.interaction_router.metrics.interaction_unhandled_total"
        ) as m:
            await interaction_router.dispatch(i)
            m.labels.assert_called_with(prefix="ghost")
            m.labels.return_value.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_governance_fail_open_increments_counter(self):
        i = _interaction("economy:foo")
        i.guild_id = 999

        async def handler(*_a, **_kw):  # noqa: D401
            return None

        # Register handler so router proceeds past the prefix check.
        interaction_router._handlers["economy"] = handler
        try:
            with (
                patch("governance.GovernanceContext.from_interaction") as ctx_fn,
                patch(
                    "governance.get_visible_subsystems",
                    new_callable=AsyncMock,
                    side_effect=RuntimeError("governance down"),
                ),
                patch(
                    "core.runtime.interaction_router.metrics.governance_fail_open_total"
                ) as m,
            ):
                ctx_fn.return_value = MagicMock()
                await interaction_router.dispatch(i)
                m.labels.assert_called_with(subsystem="economy")
                m.labels.return_value.inc.assert_called_once()
        finally:
            interaction_router._handlers.pop("economy", None)


class TestAnchorRestoreMetrics:
    @pytest.fixture(autouse=True)
    def _reset_restore_guard(self):
        # R6 added a once-only guard on restore_anchors; tests in this
        # class invoke it multiple times so we reset around each.
        message_anchor_manager.reset_restoration_state()
        yield
        message_anchor_manager.reset_restoration_state()

    @pytest.mark.asyncio
    async def test_view_missing_increments(self):
        anchors = [
            {
                "anchor_id": "a1",
                "subsystem": "ghost",
                "message_id": 100,
                "user_id": 1,
                "guild_id": 2,
                "channel_id": 3,
            },
        ]
        bot = MagicMock()
        with (
            patch(
                "core.runtime.message_anchor_manager.db.get_all_active_panel_anchors",
                new_callable=AsyncMock,
                return_value=anchors,
            ),
            patch(
                "core.runtime.persistent_views.get_view_class",
                return_value=None,
            ),
            patch(
                "core.runtime.message_anchor_manager.metrics.anchor_restore_total"
            ) as m,
        ):
            await message_anchor_manager.restore_anchors(bot)
            m.labels.assert_called_with(subsystem="ghost", result="view_missing")
            m.labels.return_value.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_ok_increments_when_view_added(self):
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
        view_cls = MagicMock(return_value=MagicMock())
        with (
            patch(
                "core.runtime.message_anchor_manager.db.get_all_active_panel_anchors",
                new_callable=AsyncMock,
                return_value=anchors,
            ),
            patch(
                "core.runtime.persistent_views.get_view_class",
                return_value=view_cls,
            ),
            patch(
                "core.runtime.message_anchor_manager.metrics.anchor_restore_total"
            ) as m,
        ):
            await message_anchor_manager.restore_anchors(bot)
            m.labels.assert_called_with(subsystem="role", result="ok")
            m.labels.return_value.inc.assert_called_once()
            bot.add_view.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_failed_increments_on_exception(self):
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
        bot.add_view = MagicMock(side_effect=RuntimeError("boom"))
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
                "core.runtime.message_anchor_manager.db.mark_panel_anchor_stale",
                new_callable=AsyncMock,
            ),
            patch(
                "core.runtime.message_anchor_manager.metrics.anchor_restore_total"
            ) as m,
        ):
            await message_anchor_manager.restore_anchors(bot)
            m.labels.assert_called_with(subsystem="role", result="restore_failed")
            m.labels.return_value.inc.assert_called_once()


class TestPanelRefreshMetrics:
    @pytest.mark.asyncio
    async def test_ok_increments_on_successful_refresh(self):
        embed = MagicMock(spec=discord.Embed)
        view = MagicMock(spec=discord.ui.View)
        refresh_fn = AsyncMock(return_value=(embed, view))

        message = MagicMock()
        message.edit = AsyncMock()
        channel = MagicMock(spec=discord.TextChannel)
        channel.fetch_message = AsyncMock(return_value=message)
        bot = MagicMock()
        bot.get_channel = MagicMock(return_value=channel)

        with patch(
            "core.runtime.live_update_scheduler._metrics.panel_refresh_total"
        ) as m:
            await live_update_scheduler._refresh_panel(
                bot, refresh_fn, 1, 2, 3, 100, "economy"
            )
            m.labels.assert_called_with(subsystem="economy", result="ok")
            m.labels.return_value.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_fn_error_increments(self):
        refresh_fn = AsyncMock(side_effect=RuntimeError("boom"))
        bot = MagicMock()
        with patch(
            "core.runtime.live_update_scheduler._metrics.panel_refresh_total"
        ) as m:
            await live_update_scheduler._refresh_panel(
                bot, refresh_fn, 1, 2, 3, 100, "economy"
            )
            m.labels.assert_called_with(subsystem="economy", result="refresh_fn_error")

    @pytest.mark.asyncio
    async def test_skipped_increments_when_fn_returns_none(self):
        refresh_fn = AsyncMock(return_value=None)
        bot = MagicMock()
        with patch(
            "core.runtime.live_update_scheduler._metrics.panel_refresh_total"
        ) as m:
            await live_update_scheduler._refresh_panel(
                bot, refresh_fn, 1, 2, 3, 100, "economy"
            )
            m.labels.assert_called_with(subsystem="economy", result="skipped")

    @pytest.mark.asyncio
    async def test_channel_missing_increments(self):
        embed = MagicMock(spec=discord.Embed)
        view = MagicMock(spec=discord.ui.View)
        refresh_fn = AsyncMock(return_value=(embed, view))
        bot = MagicMock()
        bot.get_channel = MagicMock(return_value=None)
        with patch(
            "core.runtime.live_update_scheduler._metrics.panel_refresh_total"
        ) as m:
            await live_update_scheduler._refresh_panel(
                bot, refresh_fn, 1, 2, 3, 100, "economy"
            )
            m.labels.assert_called_with(subsystem="economy", result="channel_missing")
