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


@pytest.fixture(autouse=True)
def _isolate_back_to_help_attacher():
    """Keep the module-global attacher from leaking across tests/modules."""
    saved = panel_manager._back_to_help_attacher
    panel_manager._back_to_help_attacher = None
    try:
        yield
    finally:
        panel_manager._back_to_help_attacher = saved


def _anchor_patches():
    return (
        patch(
            "core.runtime.panel_manager.message_anchor_manager.get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "core.runtime.panel_manager.message_anchor_manager.mark_stale",
            new_callable=AsyncMock,
        ),
        patch(
            "core.runtime.panel_manager.message_anchor_manager.upsert",
            new_callable=AsyncMock,
        ),
    )


@pytest.mark.asyncio
async def test_back_to_help_attacher_is_invoked_when_registered():
    """A registered hook is applied to the hub view before it's sent
    (directly-invoked hubs get "↩ Back to Help")."""
    ctx = _make_ctx()
    embed, view = MagicMock(), MagicMock()
    attacher = MagicMock()
    panel_manager.register_back_to_help_attacher(attacher)

    get_p, stale_p, upsert_p = _anchor_patches()
    with get_p, stale_p, upsert_p:
        await panel_manager.get_or_render_panel(ctx, "economy", embed, view)

    attacher.assert_called_once_with(view)
    ctx.send.assert_awaited_once_with(embed=embed, view=view)


@pytest.mark.asyncio
async def test_back_to_help_attacher_failure_never_breaks_render():
    """A hook that raises is logged + swallowed — the panel still renders."""
    ctx = _make_ctx()
    embed, view = MagicMock(), MagicMock()
    panel_manager.register_back_to_help_attacher(
        MagicMock(side_effect=RuntimeError("boom")),
    )

    get_p, stale_p, upsert_p = _anchor_patches()
    with get_p, stale_p, upsert_p:
        await panel_manager.get_or_render_panel(ctx, "role", embed, view)

    ctx.send.assert_awaited_once_with(embed=embed, view=view)


@pytest.mark.asyncio
async def test_no_attacher_registered_is_a_noop():
    ctx = _make_ctx()
    embed, view = MagicMock(), MagicMock()
    assert panel_manager._back_to_help_attacher is None
    get_p, stale_p, upsert_p = _anchor_patches()
    with get_p, stale_p, upsert_p:
        await panel_manager.get_or_render_panel(ctx, "mining", embed, view)
    ctx.send.assert_awaited_once_with(embed=embed, view=view)


def test_back_to_help_attacher_is_registerable():
    """help_cog's back-to-help helper is the registerable hook — the call the
    bot1 composition root makes at startup."""
    from cogs.help_cog import _attach_back_to_help_button

    panel_manager.register_back_to_help_attacher(_attach_back_to_help_button)
    assert panel_manager._back_to_help_attacher is _attach_back_to_help_button


def test_bot1_wires_back_to_help_at_startup():
    """The composition root (bot1) registers the hook so directly-invoked
    hubs get back-navigation."""
    from pathlib import Path

    bot1_src = (Path(__file__).resolve().parents[3] / "disbot" / "bot1.py").read_text()
    assert "register_back_to_help_attacher" in bot1_src
    assert "_attach_back_to_help_button" in bot1_src
