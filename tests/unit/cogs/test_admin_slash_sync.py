"""Unit tests for ``!syncslash`` and ``!slashes`` (PR E').

Operator tooling for the post-deploy slash-tree resync workflow.
Pins:

* ``!syncslash`` is owner-only.
* Default scope is ``guild`` — calls ``bot.tree.sync(guild=ctx.guild)``.
* Explicit ``guild`` scope behaves the same.
* ``global`` scope calls ``bot.tree.sync()`` without a guild kwarg.
* Invalid scope is rejected with an operator-readable error.
* Global sync rate-limit / HTTP failures surface as an ephemeral
  message rather than uncaught exceptions.
* ``!slashes`` reads from the in-memory tree (no Discord round-trip).
* ``!slashes`` is admin-gated (not owner-gated — it's read-only).
"""

# ruff: noqa: S101

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands

from cogs.admin_cog import AdminCog
from services.command_tree_sync import SyncOutcome


def _ctx(*, guild: bool = True) -> MagicMock:
    ctx = MagicMock(spec=commands.Context)
    if guild:
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.name = "TestGuild"
    else:
        ctx.guild = None
    ctx.send = AsyncMock()
    ctx.author = MagicMock(spec=discord.Member)
    ctx.author.id = 1
    return ctx


def _admin_cog() -> AdminCog:
    bot = MagicMock()
    bot.tree = MagicMock()
    bot.tree.sync = AsyncMock(return_value=[])
    bot.tree.copy_global_to = MagicMock()
    bot.tree.clear_commands = MagicMock()
    bot.tree.get_commands = MagicMock(return_value=[])
    bot.tree.fetch_commands = AsyncMock(return_value=[])
    return AdminCog(bot=bot)


def _fake_command(name: str, description: str = "") -> MagicMock:
    cmd = MagicMock()
    cmd.name = name
    cmd.description = description
    return cmd


# ---------------------------------------------------------------------------
# !syncslash registers + permission gating
# ---------------------------------------------------------------------------


def test_syncslash_command_is_registered():
    cog = _admin_cog()
    names = {cmd.name for cmd in cog.get_commands()}
    assert "syncslash" in names


def test_syncslash_has_owner_check():
    cog = _admin_cog()
    cmd = next(c for c in cog.get_commands() if c.name == "syncslash")
    # commands.is_owner() registers a check whose qualname contains
    # ``is_owner``.
    assert any(
        "is_owner" in getattr(check, "__qualname__", "") for check in cmd.checks
    ), "syncslash must be owner-only"


# ---------------------------------------------------------------------------
# !syncslash — guild scope (default + explicit)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_syncslash_default_scope_is_guild():
    cog = _admin_cog()
    cog.bot.tree.sync.return_value = [_fake_command("games"), _fake_command("help")]
    ctx = _ctx()

    await cog.sync_slash_commands.callback(cog, ctx)

    cog.bot.tree.copy_global_to.assert_called_once_with(guild=ctx.guild)
    cog.bot.tree.sync.assert_awaited_once_with(guild=ctx.guild)
    ctx.send.assert_awaited_once()
    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "synced" in msg.lower()
    assert "**2**" in msg
    assert "TestGuild" in msg


@pytest.mark.asyncio
async def test_syncslash_explicit_guild_scope():
    cog = _admin_cog()
    ctx = _ctx()

    await cog.sync_slash_commands.callback(cog, ctx, "guild")

    cog.bot.tree.copy_global_to.assert_called_once_with(guild=ctx.guild)
    cog.bot.tree.sync.assert_awaited_once_with(guild=ctx.guild)


# ---------------------------------------------------------------------------
# !syncslash — global scope (now diff-gated through auto_sync_if_changed)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_syncslash_global_default_goes_through_gated_helper():
    """Plain ``global`` routes through the diff-gated helper, not an
    unconditional ``tree.sync()``."""
    cog = _admin_cog()
    ctx = _ctx()
    outcome = SyncOutcome(
        synced=True,
        reason="synced",
        added=("btd6 round",),
        removed=("oldcmd",),
    )

    with patch(
        "cogs.admin._slash_sync.command_tree_sync.auto_sync_if_changed",
        AsyncMock(return_value=outcome),
    ) as helper:
        await cog.sync_slash_commands.callback(cog, ctx, "global")

    helper.assert_awaited_once_with(cog.bot, enabled=True)
    cog.bot.tree.copy_global_to.assert_not_called()
    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "Synced global" in msg
    assert "+1 added" in msg and "-1 removed" in msg
    assert "`btd6 round`" in msg
    assert "Propagation" in msg


@pytest.mark.asyncio
async def test_syncslash_global_unchanged_skips_with_message():
    cog = _admin_cog()
    ctx = _ctx()
    outcome = SyncOutcome(synced=False, reason="unchanged")

    with patch(
        "cogs.admin._slash_sync.command_tree_sync.auto_sync_if_changed",
        AsyncMock(return_value=outcome),
    ):
        await cog.sync_slash_commands.callback(cog, ctx, "global")

    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "already in sync" in msg
    assert "force" in msg.lower()


@pytest.mark.asyncio
async def test_syncslash_global_fetch_failed_surfaces_message():
    cog = _admin_cog()
    ctx = _ctx()
    outcome = SyncOutcome(synced=False, reason="fetch_failed")

    with patch(
        "cogs.admin._slash_sync.command_tree_sync.auto_sync_if_changed",
        AsyncMock(return_value=outcome),
    ):
        await cog.sync_slash_commands.callback(cog, ctx, "global")

    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "Couldn't fetch" in msg
    assert "force" in msg.lower()


@pytest.mark.asyncio
async def test_syncslash_global_sync_failed_reports_diff_and_failure():
    cog = _admin_cog()
    ctx = _ctx()
    outcome = SyncOutcome(
        synced=False,
        reason="sync_failed",
        added=("new",),
        removed=(),
    )

    with patch(
        "cogs.admin._slash_sync.command_tree_sync.auto_sync_if_changed",
        AsyncMock(return_value=outcome),
    ):
        await cog.sync_slash_commands.callback(cog, ctx, "global")

    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "failed" in msg.lower()
    assert "+1 added" in msg


@pytest.mark.asyncio
async def test_syncslash_global_force_does_unconditional_sync():
    """``global force`` bypasses the diff gate and always calls tree.sync()."""
    cog = _admin_cog()
    cog.bot.tree.sync.return_value = [_fake_command("help")]
    ctx = _ctx()

    with patch(
        "cogs.admin._slash_sync.command_tree_sync.auto_sync_if_changed",
        AsyncMock(),
    ) as helper:
        await cog.sync_slash_commands.callback(cog, ctx, "global", "force")

    helper.assert_not_awaited()
    cog.bot.tree.sync.assert_awaited_once_with()
    cog.bot.tree.copy_global_to.assert_not_called()
    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "Force-synced" in msg
    assert "**1**" in msg
    assert "Propagation" in msg


@pytest.mark.asyncio
async def test_syncslash_global_force_handles_http_failure():
    cog = _admin_cog()
    cog.bot.tree.sync.side_effect = discord.HTTPException(
        response=MagicMock(),
        message="rate limited",
    )
    ctx = _ctx()

    await cog.sync_slash_commands.callback(cog, ctx, "global", "force")

    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "Global sync failed" in msg
    assert "HTTPException" in msg


# ---------------------------------------------------------------------------
# !syncslash — clear scope (fix the global+guild duplicate listing)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_syncslash_clear_scope_clears_guild_copies():
    cog = _admin_cog()
    ctx = _ctx()

    await cog.sync_slash_commands.callback(cog, ctx, "clear")

    cog.bot.tree.clear_commands.assert_called_once_with(guild=ctx.guild)
    cog.bot.tree.sync.assert_awaited_once_with(guild=ctx.guild)
    # clear must NOT re-copy the global commands (that would re-create the dupes).
    cog.bot.tree.copy_global_to.assert_not_called()
    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "Cleared" in msg
    assert "TestGuild" in msg


@pytest.mark.asyncio
async def test_syncslash_clear_in_dm_context_rejects():
    cog = _admin_cog()
    ctx = _ctx(guild=False)

    await cog.sync_slash_commands.callback(cog, ctx, "clear")

    cog.bot.tree.clear_commands.assert_not_called()
    cog.bot.tree.sync.assert_not_called()
    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "guild context" in msg


@pytest.mark.asyncio
async def test_syncslash_clear_handles_http_failure():
    cog = _admin_cog()
    cog.bot.tree.sync.side_effect = discord.HTTPException(
        response=MagicMock(),
        message="boom",
    )
    ctx = _ctx()

    await cog.sync_slash_commands.callback(cog, ctx, "clear")

    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "Clear failed" in msg


@pytest.mark.asyncio
async def test_syncslash_guild_message_points_to_clear_for_duplicates():
    # The guild-sync message must tell the operator how to undo dupes.
    cog = _admin_cog()
    ctx = _ctx()

    await cog.sync_slash_commands.callback(cog, ctx, "guild")

    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "clear" in msg.lower()


# ---------------------------------------------------------------------------
# !syncslash — invalid scope / no guild
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_syncslash_rejects_unknown_scope():
    cog = _admin_cog()
    ctx = _ctx()

    await cog.sync_slash_commands.callback(cog, ctx, "everywhere")

    cog.bot.tree.sync.assert_not_called()
    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "Invalid scope" in msg


@pytest.mark.asyncio
async def test_syncslash_guild_scope_in_dm_context():
    """Guild-scope sync requires a guild — DM invocation must be
    rejected rather than calling tree.sync(guild=None) which would
    sync globally as an unintended side effect.
    """
    cog = _admin_cog()
    ctx = _ctx(guild=False)

    await cog.sync_slash_commands.callback(cog, ctx)

    cog.bot.tree.sync.assert_not_called()
    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "guild context" in msg


# ---------------------------------------------------------------------------
# !slashes — read-only listing
# ---------------------------------------------------------------------------


def test_slashes_command_is_registered():
    cog = _admin_cog()
    names = {cmd.name for cmd in cog.get_commands()}
    assert "slashes" in names


@pytest.mark.asyncio
async def test_slashes_lists_guild_commands_by_default():
    cog = _admin_cog()
    cog.bot.tree.get_commands.return_value = [
        _fake_command("games", "Open the Games hub"),
        _fake_command("help"),
    ]
    ctx = _ctx()

    await cog.list_slash_commands.callback(cog, ctx)

    cog.bot.tree.get_commands.assert_called_once_with(guild=ctx.guild)
    ctx.send.assert_awaited_once()
    _args, kwargs = ctx.send.call_args
    embed = kwargs["embed"]
    assert "Guild" in (embed.title or "")
    assert "`/games`" in (embed.description or "")
    assert "`/help`" in (embed.description or "")


@pytest.mark.asyncio
async def test_slashes_global_scope_lists_without_guild():
    cog = _admin_cog()
    cog.bot.tree.get_commands.return_value = [_fake_command("help", "Show help")]
    ctx = _ctx()

    await cog.list_slash_commands.callback(cog, ctx, "global")

    cog.bot.tree.get_commands.assert_called_once_with()
    _args, kwargs = ctx.send.call_args
    embed = kwargs["embed"]
    assert "Global" in (embed.title or "")


@pytest.mark.asyncio
async def test_slashes_empty_tree_surfaces_message():
    cog = _admin_cog()
    cog.bot.tree.get_commands.return_value = []
    ctx = _ctx()

    await cog.list_slash_commands.callback(cog, ctx)

    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "No guild-local slash commands registered" in msg
    assert "!syncslash guild" in msg


@pytest.mark.asyncio
async def test_slashes_lists_commands_sorted_by_name():
    cog = _admin_cog()
    cog.bot.tree.get_commands.return_value = [
        _fake_command("utility"),
        _fake_command("admin"),
        _fake_command("games"),
    ]
    ctx = _ctx()

    await cog.list_slash_commands.callback(cog, ctx)

    _args, kwargs = ctx.send.call_args
    description = kwargs["embed"].description or ""
    # Order in the rendered description must be alphabetical.
    admin_pos = description.find("/admin")
    games_pos = description.find("/games")
    utility_pos = description.find("/utility")
    assert 0 <= admin_pos < games_pos < utility_pos


@pytest.mark.asyncio
async def test_slashes_in_dm_context_rejects():
    cog = _admin_cog()
    ctx = _ctx(guild=False)

    await cog.list_slash_commands.callback(cog, ctx)

    cog.bot.tree.get_commands.assert_not_called()
    args, kwargs = ctx.send.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "guild context" in msg
