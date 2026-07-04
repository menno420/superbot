"""Tests for the ``!slowmode`` / ``!topic`` channel-edit cog commands.

Both route through the audited :class:`ChannelLifecycleService` seam (the same
path as ``!rename``), so the cog-level tests pin the typed request handed to the
service + the operator-facing reply. The service-level behaviour (the actual
``channel.edit`` call, clamping, audit/event) is covered in
``tests/unit/services/test_channel_lifecycle_service.py``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogs.channel_cog import ChannelCog
from services.lifecycle import SUCCESS


def _ctx():
    ctx = MagicMock()
    ctx.guild = MagicMock()
    ctx.author = MagicMock()
    ctx.send = AsyncMock()
    return ctx


def _ok_result():
    return MagicMock(outcome=SUCCESS)


@pytest.mark.asyncio
async def test_slowmode_routes_through_lifecycle_seam():
    cog = ChannelCog(MagicMock())
    ctx = _ctx()
    channel = MagicMock(id=10, name="general")

    with (
        patch.object(cog, "_resolve_channel", return_value=channel),
        patch(
            "cogs.channel_cog.ChannelLifecycleService.apply",
            new_callable=AsyncMock,
            return_value=_ok_result(),
        ) as apply_mock,
    ):
        await cog.set_slowmode.callback(cog, ctx, "general", 30)

    apply_mock.assert_awaited_once()
    request = apply_mock.await_args.args[1]
    assert request.operation == "set_slowmode"
    assert request.channel_ids == (10,)
    assert request.slowmode_seconds == 30
    assert apply_mock.await_args.kwargs["actor_type"] == "admin"
    assert "30s" in ctx.send.await_args.args[0]


@pytest.mark.asyncio
async def test_slowmode_zero_reports_disabled():
    cog = ChannelCog(MagicMock())
    ctx = _ctx()
    channel = MagicMock(id=10, name="general")

    with (
        patch.object(cog, "_resolve_channel", return_value=channel),
        patch(
            "cogs.channel_cog.ChannelLifecycleService.apply",
            new_callable=AsyncMock,
            return_value=_ok_result(),
        ),
    ):
        await cog.set_slowmode.callback(cog, ctx, "general", 0)

    assert "disabled" in ctx.send.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_slowmode_rejects_negative_without_calling_service():
    cog = ChannelCog(MagicMock())
    ctx = _ctx()
    channel = MagicMock(id=10, name="general")

    with (
        patch.object(cog, "_resolve_channel", return_value=channel),
        patch(
            "cogs.channel_cog.ChannelLifecycleService.apply",
            new_callable=AsyncMock,
        ) as apply_mock,
    ):
        await cog.set_slowmode.callback(cog, ctx, "general", -5)

    apply_mock.assert_not_awaited()
    assert "0 or more" in ctx.send.await_args.args[0]


@pytest.mark.asyncio
async def test_slowmode_rejects_above_cap_without_calling_service():
    cog = ChannelCog(MagicMock())
    ctx = _ctx()
    channel = MagicMock(id=10, name="general")

    with (
        patch.object(cog, "_resolve_channel", return_value=channel),
        patch(
            "cogs.channel_cog.ChannelLifecycleService.apply",
            new_callable=AsyncMock,
        ) as apply_mock,
    ):
        await cog.set_slowmode.callback(cog, ctx, "general", 99999)

    apply_mock.assert_not_awaited()
    assert "21600" in ctx.send.await_args.args[0]


@pytest.mark.asyncio
async def test_slowmode_unknown_channel_short_circuits():
    cog = ChannelCog(MagicMock())
    ctx = _ctx()

    with (
        patch.object(cog, "_resolve_channel", return_value=None),
        patch(
            "cogs.channel_cog.ChannelLifecycleService.apply",
            new_callable=AsyncMock,
        ) as apply_mock,
    ):
        await cog.set_slowmode.callback(cog, ctx, "ghost", 10)

    apply_mock.assert_not_awaited()
    assert "not found" in ctx.send.await_args.args[0]


@pytest.mark.asyncio
async def test_topic_routes_through_lifecycle_seam():
    cog = ChannelCog(MagicMock())
    ctx = _ctx()
    channel = MagicMock(id=10, name="general")

    with (
        patch.object(cog, "_resolve_channel", return_value=channel),
        patch(
            "cogs.channel_cog.ChannelLifecycleService.apply",
            new_callable=AsyncMock,
            return_value=_ok_result(),
        ) as apply_mock,
    ):
        await cog.set_topic.callback(cog, ctx, "general", text="hello there")

    request = apply_mock.await_args.args[1]
    assert request.operation == "set_topic"
    assert request.channel_ids == (10,)
    assert request.topic == "hello there"
    assert "updated" in ctx.send.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_topic_empty_reports_cleared():
    cog = ChannelCog(MagicMock())
    ctx = _ctx()
    channel = MagicMock(id=10, name="general")

    with (
        patch.object(cog, "_resolve_channel", return_value=channel),
        patch(
            "cogs.channel_cog.ChannelLifecycleService.apply",
            new_callable=AsyncMock,
            return_value=_ok_result(),
        ),
    ):
        await cog.set_topic.callback(cog, ctx, "general", text="")

    assert "cleared" in ctx.send.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_topic_reports_seam_failure():
    cog = ChannelCog(MagicMock())
    ctx = _ctx()
    channel = MagicMock(id=10, name="general")
    failed = MagicMock(outcome="failed")

    with (
        patch.object(cog, "_resolve_channel", return_value=channel),
        patch.object(cog, "_channel_result_error", return_value="missing permission"),
        patch(
            "cogs.channel_cog.ChannelLifecycleService.apply",
            new_callable=AsyncMock,
            return_value=failed,
        ),
    ):
        await cog.set_topic.callback(cog, ctx, "general", text="hi")

    assert "❌" in ctx.send.await_args.args[0]
    assert "missing permission" in ctx.send.await_args.args[0]
