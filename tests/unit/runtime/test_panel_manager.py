"""Panel re-invocation lifecycle tests.

The user-facing contract: every invocation of a panel command produces a
NEW message at the bottom of the channel.  Any prior anchored message for
the same (user, channel, subsystem) is deleted first so the channel does
not accumulate orphans.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from core.runtime import panel_manager


def _make_ctx(*, user_id: int = 111, guild_id: int = 222, channel_id: int = 333):
    ctx = MagicMock()
    ctx.author.id = user_id
    ctx.guild.id = guild_id
    ctx.channel.id = channel_id
    ctx.send = AsyncMock(return_value=MagicMock(id=88888))
    return ctx


@pytest.mark.asyncio
async def test_no_prior_anchor_sends_fresh_and_upserts():
    ctx = _make_ctx()
    embed = MagicMock()
    view = MagicMock()

    with (
        patch(
            "core.runtime.panel_manager.message_anchor_manager.get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "core.runtime.panel_manager.message_anchor_manager.mark_stale",
            new_callable=AsyncMock,
        ) as mark_stale,
        patch(
            "core.runtime.panel_manager.message_anchor_manager.upsert",
            new_callable=AsyncMock,
        ) as upsert,
    ):
        msg = await panel_manager.get_or_render_panel(ctx, "economy", embed, view)

    ctx.send.assert_awaited_once_with(embed=embed, view=view)
    mark_stale.assert_not_awaited()
    upsert.assert_awaited_once_with(111, 222, 333, "economy", 88888)
    assert msg.id == 88888


@pytest.mark.asyncio
async def test_existing_anchor_deletes_old_then_sends_fresh():
    ctx = _make_ctx()
    embed = MagicMock()
    view = MagicMock()

    old_msg = MagicMock()
    old_msg.delete = AsyncMock()
    ctx.channel.fetch_message = AsyncMock(return_value=old_msg)

    anchor = {
        "anchor_id": "anchor-abc",
        "message_id": 55555,
        "is_stale": False,
    }

    with (
        patch(
            "core.runtime.panel_manager.message_anchor_manager.get",
            new_callable=AsyncMock,
            return_value=anchor,
        ),
        patch(
            "core.runtime.panel_manager.message_anchor_manager.mark_stale",
            new_callable=AsyncMock,
        ) as mark_stale,
        patch(
            "core.runtime.panel_manager.message_anchor_manager.upsert",
            new_callable=AsyncMock,
        ) as upsert,
    ):
        await panel_manager.get_or_render_panel(ctx, "mining", embed, view)

    ctx.channel.fetch_message.assert_awaited_once_with(55555)
    old_msg.delete.assert_awaited_once()
    mark_stale.assert_awaited_once_with("anchor-abc")
    ctx.send.assert_awaited_once_with(embed=embed, view=view)
    upsert.assert_awaited_once_with(111, 222, 333, "mining", 88888)


@pytest.mark.asyncio
async def test_stale_anchor_skips_delete_and_sends_fresh():
    ctx = _make_ctx()
    embed = MagicMock()
    view = MagicMock()

    anchor = {
        "anchor_id": "anchor-xyz",
        "message_id": 44444,
        "is_stale": True,
    }
    ctx.channel.fetch_message = AsyncMock()

    with (
        patch(
            "core.runtime.panel_manager.message_anchor_manager.get",
            new_callable=AsyncMock,
            return_value=anchor,
        ),
        patch(
            "core.runtime.panel_manager.message_anchor_manager.mark_stale",
            new_callable=AsyncMock,
        ) as mark_stale,
        patch(
            "core.runtime.panel_manager.message_anchor_manager.upsert",
            new_callable=AsyncMock,
        ) as upsert,
    ):
        await panel_manager.get_or_render_panel(ctx, "role", embed, view)

    ctx.channel.fetch_message.assert_not_awaited()
    mark_stale.assert_not_awaited()
    ctx.send.assert_awaited_once_with(embed=embed, view=view)
    upsert.assert_awaited_once_with(111, 222, 333, "role", 88888)


@pytest.mark.asyncio
async def test_old_message_already_gone_still_sends_fresh():
    ctx = _make_ctx()
    embed = MagicMock()
    view = MagicMock()

    ctx.channel.fetch_message = AsyncMock(
        side_effect=discord.NotFound(MagicMock(status=404), "gone")
    )

    anchor = {
        "anchor_id": "anchor-old",
        "message_id": 33333,
        "is_stale": False,
    }

    with (
        patch(
            "core.runtime.panel_manager.message_anchor_manager.get",
            new_callable=AsyncMock,
            return_value=anchor,
        ),
        patch(
            "core.runtime.panel_manager.message_anchor_manager.mark_stale",
            new_callable=AsyncMock,
        ) as mark_stale,
        patch(
            "core.runtime.panel_manager.message_anchor_manager.upsert",
            new_callable=AsyncMock,
        ) as upsert,
    ):
        await panel_manager.get_or_render_panel(ctx, "moderation", embed, view)

    mark_stale.assert_awaited_once_with("anchor-old")
    ctx.send.assert_awaited_once_with(embed=embed, view=view)
    upsert.assert_awaited_once_with(111, 222, 333, "moderation", 88888)


@pytest.mark.asyncio
async def test_re_invocation_produces_new_message_id_each_time():
    """Two consecutive invocations must end up with the second (newer) anchor id."""
    ctx = _make_ctx()
    embed = MagicMock()
    view = MagicMock()

    # First call: no prior anchor.
    # Second call: anchor exists pointing at the first message.
    ctx.send.side_effect = [MagicMock(id=1001), MagicMock(id=1002)]
    old_msg = MagicMock()
    old_msg.delete = AsyncMock()
    ctx.channel.fetch_message = AsyncMock(return_value=old_msg)

    get_mock = AsyncMock(
        side_effect=[
            None,
            {"anchor_id": "a1", "message_id": 1001, "is_stale": False},
        ]
    )

    with (
        patch("core.runtime.panel_manager.message_anchor_manager.get", get_mock),
        patch(
            "core.runtime.panel_manager.message_anchor_manager.mark_stale",
            new_callable=AsyncMock,
        ),
        patch(
            "core.runtime.panel_manager.message_anchor_manager.upsert",
            new_callable=AsyncMock,
        ) as upsert,
    ):
        await panel_manager.get_or_render_panel(ctx, "economy", embed, view)
        await panel_manager.get_or_render_panel(ctx, "economy", embed, view)

    assert upsert.await_args_list[0].args == (111, 222, 333, "economy", 1001)
    assert upsert.await_args_list[1].args == (111, 222, 333, "economy", 1002)
    old_msg.delete.assert_awaited_once()
