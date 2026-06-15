"""Tests that the F7 observability metrics fire at the expected emit sites.

Covers:
- interaction_router: interaction_unhandled_total on missing prefix
- interaction_router: governance_fail_open_total when governance throws
- message_anchor_manager: anchor_restore_total for ok / view_missing /
  restore_failed (one parametrized test, three cases)
- live_update_scheduler: panel_refresh_total for ok / skipped /
  refresh_fn_error / channel_missing (one parametrized test, four cases)

P1 PR-7 consolidation: 9 tests collapsed into 4 (2 router + 1
parametrized anchor + 1 parametrized scheduler). The collected
case count stays similar, but each behaviour now lives in one
place keyed by its outcome label, so adding a new outcome means
adding one row to the parameter list rather than copying 25 LOC
of mock setup.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from core.runtime import (
    interaction_router,
    live_update_scheduler,
    message_anchor_manager,
)


def _interaction(custom_id: str) -> MagicMock:
    i = MagicMock()
    i.custom_id = custom_id
    i.data = {"custom_id": custom_id}
    i.user = MagicMock()
    i.user.id = 42
    i.guild_id = None
    i.channel_id = None
    i.response = MagicMock()
    i.response.is_done = MagicMock(return_value=False)
    i.response.send_message = AsyncMock()
    return i


def _anchor_row(subsystem: str = "role") -> dict:
    return {
        "anchor_id": "a1",
        "subsystem": subsystem,
        "message_id": 100,
        "user_id": 1,
        "guild_id": 2,
        "channel_id": 3,
    }


# ---------------------------------------------------------------------------
# interaction_router metrics
# ---------------------------------------------------------------------------


class TestInteractionRouterMetrics:
    @pytest.mark.asyncio
    async def test_unhandled_prefix_increments_counter(self):
        i = _interaction("ghost:foo")
        with patch(
            "core.runtime.interaction_router.metrics.interaction_unhandled_total",
        ) as m:
            await interaction_router.dispatch(i)
            m.labels.assert_called_with(prefix="ghost")
            m.labels.return_value.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_governance_fail_open_increments_counter(self):
        i = _interaction("economy:foo")
        i.guild_id = 999

        async def handler(*_a, **_kw):
            return None

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
                    "core.runtime.interaction_router.metrics.governance_fail_open_total",
                ) as m,
            ):
                ctx_fn.return_value = MagicMock()
                await interaction_router.dispatch(i)
                m.labels.assert_called_with(subsystem="economy")
                m.labels.return_value.inc.assert_called_once()
        finally:
            interaction_router._handlers.pop("economy", None)


# ---------------------------------------------------------------------------
# message_anchor_manager metrics
# ---------------------------------------------------------------------------


@pytest.fixture
def _reset_restore_guard():
    message_anchor_manager.reset_restoration_state()
    yield
    message_anchor_manager.reset_restoration_state()


def _restore_setup(*, view_cls, add_view_side_effect=None):
    """Build the patch stack for restore_anchors() — returns a context tuple."""
    bot = MagicMock()
    if add_view_side_effect is not None:
        bot.add_view = MagicMock(side_effect=add_view_side_effect)
    else:
        bot.add_view = MagicMock()
    return bot


@pytest.mark.parametrize(
    "subsystem, view_cls, add_view_side_effect, expected_result",
    [
        ("ghost", None, None, "view_missing"),
        ("role", MagicMock(return_value=MagicMock()), None, "ok"),
        (
            "role",
            MagicMock(return_value=MagicMock()),
            RuntimeError("boom"),
            "restore_failed",
        ),
    ],
    ids=["view_missing", "ok", "restore_failed"],
)
@pytest.mark.asyncio
async def test_anchor_restore_metric(
    _reset_restore_guard,
    subsystem: str,
    view_cls,
    add_view_side_effect,
    expected_result: str,
):
    bot = _restore_setup(view_cls=view_cls, add_view_side_effect=add_view_side_effect)
    with (
        patch(
            "core.runtime.message_anchor_manager.db.get_all_active_panel_anchors",
            new_callable=AsyncMock,
            return_value=[_anchor_row(subsystem)],
        ),
        patch(
            "core.runtime.persistent_views.get_view_class",
            return_value=view_cls,
        ),
        patch(
            "core.runtime.message_anchor_manager.db.mark_panel_anchor_stale",
            new_callable=AsyncMock,
        ),
        patch(
            "core.runtime.message_anchor_manager.metrics.anchor_restore_total",
        ) as m,
    ):
        await message_anchor_manager.restore_anchors(bot)
        m.labels.assert_called_with(subsystem=subsystem, result=expected_result)
        m.labels.return_value.inc.assert_called_once()


# ---------------------------------------------------------------------------
# live_update_scheduler metrics
# ---------------------------------------------------------------------------


def _refresh_inputs(*, return_value, channel=None):
    refresh_fn = AsyncMock(return_value=return_value)
    if isinstance(return_value, BaseException) or (
        getattr(refresh_fn, "side_effect", None) is not None
    ):
        pass  # handled by side_effect setting below
    bot = MagicMock()
    if channel is not None:
        bot.get_channel = MagicMock(return_value=channel)
    return refresh_fn, bot


@pytest.mark.parametrize(
    "scenario, expected_result",
    [
        ("ok", "ok"),
        ("refresh_fn_error", "refresh_fn_error"),
        ("skipped", "skipped"),
        ("channel_missing", "channel_missing"),
    ],
    ids=["ok", "refresh_fn_error", "skipped", "channel_missing"],
)
@pytest.mark.asyncio
async def test_panel_refresh_metric(scenario: str, expected_result: str):
    embed = MagicMock(spec=discord.Embed)
    view = MagicMock(spec=discord.ui.View)

    if scenario == "ok":
        refresh_fn = AsyncMock(return_value=(embed, view))
        message = MagicMock()
        message.edit = AsyncMock()
        channel = MagicMock(spec=discord.TextChannel)
        channel.fetch_message = AsyncMock(return_value=message)
        bot = MagicMock()
        bot.get_channel = MagicMock(return_value=channel)
    elif scenario == "refresh_fn_error":
        refresh_fn = AsyncMock(side_effect=RuntimeError("boom"))
        bot = MagicMock()
    elif scenario == "skipped":
        refresh_fn = AsyncMock(return_value=None)
        bot = MagicMock()
    elif scenario == "channel_missing":
        refresh_fn = AsyncMock(return_value=(embed, view))
        bot = MagicMock()
        bot.get_channel = MagicMock(return_value=None)
    else:
        raise AssertionError(f"unhandled scenario {scenario}")

    with patch(
        "core.runtime.live_update_scheduler._metrics.panel_refresh_total",
    ) as m:
        await live_update_scheduler._refresh_panel(
            bot,
            refresh_fn,
            1,
            2,
            3,
            100,
            "economy",
        )
        m.labels.assert_called_with(subsystem="economy", result=expected_result)
