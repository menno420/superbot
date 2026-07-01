"""Command-behaviour + authority tests for the Utility cog.

Completion-first deepening (Q-0209) — clears punch-list items **#2** (command-
behaviour coverage) and **#3** (authority enforcement) on the Utility completion
certificate (`docs/planning/feature-completion/units/utility.md`).  Before this
file the only Utility coverage was the *hub layer*
(`test_utility_hub_children.py`); the 16 member command paths (info / avatar /
poll / remind / invite / clear + the new ping / botinfo / membercount) were
untested.

The new **user-tier `!ping`** (registry capability `utility.tool.ping`) is
exercised here too — it was re-homed from the admin-tier diagnostic `!latency`
so ordinary members finally have a ping.
"""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands

from cogs.utility_cog import UtilityCog, _format_uptime


def _ctx(*, guild: MagicMock | None = None) -> MagicMock:
    ctx = MagicMock()
    ctx.author = MagicMock(spec=discord.Member)
    ctx.author.id = 1
    ctx.author.__str__ = lambda self: "Tester#0001"  # type: ignore[assignment]
    ctx.send = AsyncMock()
    ctx.guild = guild
    ctx.channel = MagicMock()
    return ctx


def _bot() -> MagicMock:
    bot = MagicMock()
    bot.latency = 0.042  # seconds → 42 ms
    bot.user = MagicMock()
    bot.user.name = "SuperBot"
    bot.user.display_avatar.url = "https://cdn/avatar.png"
    g1 = MagicMock()
    g1.member_count = 100
    g2 = MagicMock()
    g2.member_count = 50
    bot.guilds = [g1, g2]
    bot.walk_commands.return_value = [MagicMock(), MagicMock(), MagicMock()]
    bot.uptime = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
        hours=3,
        minutes=5,
    )
    return bot


def _predicate(command: commands.Command):
    """The single check predicate attached by ``perms_or_owner``."""
    assert command.checks, f"{command.name} has no checks"
    return command.checks[0]


def _member(**perms: bool) -> MagicMock:
    m = MagicMock(spec=discord.Member)
    m.id = 999
    gp = MagicMock()
    gp.configure_mock(**{k: v for k, v in perms.items()})
    # default any unqueried perm to False
    gp.manage_messages = perms.get("manage_messages", False)
    gp.create_instant_invite = perms.get("create_instant_invite", False)
    m.guild_permissions = gp
    return m


# --------------------------------------------------------------------------
# ping (the new user-tier command)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ping_reports_gateway_and_round_trip():
    cog = UtilityCog(_bot())
    ctx = _ctx()
    sent = MagicMock()
    sent.edit = AsyncMock()
    ctx.send.return_value = sent

    await cog.ping.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    sent.edit.assert_awaited_once()
    embed = sent.edit.await_args.kwargs["embed"]
    field_names = {f.name for f in embed.fields}
    assert "Gateway" in field_names and "Round-trip" in field_names
    gateway = next(f.value for f in embed.fields if f.name == "Gateway")
    assert gateway == "42 ms"


# --------------------------------------------------------------------------
# botinfo
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_botinfo_aggregates_servers_users_and_uptime():
    cog = UtilityCog(_bot())
    ctx = _ctx()

    await cog.botinfo.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    embed = ctx.send.await_args.kwargs["embed"]
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Servers"] == "2"
    assert fields["Users"] == "150"  # 100 + 50
    assert fields["Commands"] == "3"
    assert "Uptime" in fields
    assert fields["Gateway"] == "42 ms"


@pytest.mark.asyncio
async def test_botinfo_tolerates_missing_uptime_and_user():
    bot = _bot()
    bot.user = None
    del bot.uptime  # getattr(..., None) path
    cog = UtilityCog(bot)
    ctx = _ctx()

    await cog.botinfo.callback(cog, ctx)  # must not raise

    embed = ctx.send.await_args.kwargs["embed"]
    assert "Uptime" not in {f.name for f in embed.fields}


# --------------------------------------------------------------------------
# membercount
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_membercount_splits_humans_and_bots():
    guild = MagicMock()
    guild.name = "Guild"
    guild.member_count = 3
    human = MagicMock()
    human.bot = False
    a_bot = MagicMock()
    a_bot.bot = True
    guild.members = [human, human, a_bot]
    guild.icon = None
    cog = UtilityCog(_bot())
    ctx = _ctx(guild=guild)

    await cog.membercount.callback(cog, ctx)

    embed = ctx.send.await_args.kwargs["embed"]
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Total"] == "3"
    assert fields["Humans"] == "2"
    assert fields["Bots"] == "1"


@pytest.mark.asyncio
async def test_membercount_without_member_cache_shows_only_total():
    guild = MagicMock()
    guild.name = "Guild"
    guild.member_count = 42
    guild.members = []  # members intent off / not cached
    guild.icon = None
    cog = UtilityCog(_bot())
    ctx = _ctx(guild=guild)

    await cog.membercount.callback(cog, ctx)

    embed = ctx.send.await_args.kwargs["embed"]
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Total"] == "42"
    assert "Humans" not in fields and "Bots" not in fields


# --------------------------------------------------------------------------
# clear — validation + authority
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clear_rejects_non_positive_amount():
    cog = UtilityCog(_bot())
    ctx = _ctx()
    await cog.clear.callback(cog, ctx, 0)
    ctx.channel.purge.assert_not_called()


@pytest.mark.asyncio
async def test_clear_rejects_over_100():
    cog = UtilityCog(_bot())
    ctx = _ctx()
    await cog.clear.callback(cog, ctx, 500)
    ctx.channel.purge.assert_not_called()


@pytest.mark.asyncio
async def test_clear_purges_within_bounds():
    cog = UtilityCog(_bot())
    ctx = _ctx()
    ctx.channel.purge = AsyncMock(return_value=[MagicMock(), MagicMock()])
    sent = MagicMock()
    sent.delete = AsyncMock()
    ctx.send.return_value = sent
    await cog.clear.callback(cog, ctx, 5)
    ctx.channel.purge.assert_awaited_once_with(limit=5)


@pytest.mark.asyncio
async def test_clear_denies_member_without_manage_messages():
    predicate = _predicate(UtilityCog.clear)
    ctx = MagicMock()
    ctx.author = _member(manage_messages=False)
    with pytest.raises(commands.MissingPermissions):
        await predicate(ctx)


@pytest.mark.asyncio
async def test_clear_allows_member_with_manage_messages():
    predicate = _predicate(UtilityCog.clear)
    ctx = MagicMock()
    ctx.author = _member(manage_messages=True)
    assert await predicate(ctx) is True


@pytest.mark.asyncio
async def test_clear_allows_platform_owner():
    predicate = _predicate(UtilityCog.clear)
    ctx = MagicMock()
    ctx.author = _member(manage_messages=False)
    with patch("core.runtime.permission_checks.is_platform_owner", return_value=True):
        assert await predicate(ctx) is True


# --------------------------------------------------------------------------
# invite — authority
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invite_denies_member_without_create_instant_invite():
    predicate = _predicate(UtilityCog.invite)
    ctx = MagicMock()
    ctx.author = _member(create_instant_invite=False)
    with pytest.raises(commands.MissingPermissions):
        await predicate(ctx)


@pytest.mark.asyncio
async def test_invite_allows_member_with_create_instant_invite():
    predicate = _predicate(UtilityCog.invite)
    ctx = MagicMock()
    ctx.author = _member(create_instant_invite=True)
    assert await predicate(ctx) is True


# --------------------------------------------------------------------------
# poll — validation
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_requires_at_least_two_options():
    cog = UtilityCog(_bot())
    ctx = _ctx()
    await cog.poll.callback(cog, ctx, "Q?", "only-one")
    # error embed sent; no poll message added reactions
    assert ctx.send.await_count == 1


@pytest.mark.asyncio
async def test_poll_rejects_more_than_ten_options():
    cog = UtilityCog(_bot())
    ctx = _ctx()
    await cog.poll.callback(cog, ctx, "Q?", *[f"o{i}" for i in range(11)])
    assert ctx.send.await_count == 1


@pytest.mark.asyncio
async def test_poll_creates_reaction_poll():
    cog = UtilityCog(_bot())
    ctx = _ctx()
    poll_msg = MagicMock()
    poll_msg.add_reaction = AsyncMock()
    ctx.send.return_value = poll_msg
    await cog.poll.callback(cog, ctx, "Q?", "a", "b", "c")
    assert poll_msg.add_reaction.await_count == 3


# --------------------------------------------------------------------------
# remind — validation + task spawn
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remind_rejects_non_positive_time():
    cog = UtilityCog(_bot())
    ctx = _ctx()
    with patch("cogs.utility_cog.tasks.spawn") as spawn:
        await cog.remind.callback(cog, ctx, 0, message="hi")
    spawn.assert_not_called()


@pytest.mark.asyncio
async def test_remind_spawns_a_reminder_task():
    cog = UtilityCog(_bot())
    ctx = _ctx()
    with patch("cogs.utility_cog.tasks.spawn") as spawn:
        await cog.remind.callback(cog, ctx, 5, message="stand up")
    spawn.assert_called_once()
    assert spawn.call_args.args[0].startswith("utility:remind:")
    # spawn is mocked, so close the un-awaited reminder coroutine it was handed.
    spawn.call_args.args[1].close()


# --------------------------------------------------------------------------
# info / avatar — read-only behaviour
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_info_server_default():
    guild = MagicMock()
    guild.name = "MyGuild"
    guild.owner.mention = "@owner"
    guild.member_count = 7
    guild.premium_tier = 2
    guild.created_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    guild.text_channels = [MagicMock()]
    guild.voice_channels = []
    guild.icon = None
    cog = UtilityCog(_bot())
    ctx = _ctx(guild=guild)
    await cog.info.callback(cog, ctx)
    embed = ctx.send.await_args.kwargs["embed"]
    assert embed.title == "MyGuild"


@pytest.mark.asyncio
async def test_avatar_shows_image():
    cog = UtilityCog(_bot())
    ctx = _ctx()
    member = MagicMock(spec=discord.Member)
    member.display_avatar.url = "https://cdn/a.png"
    member.__str__ = lambda self: "Someone"  # type: ignore[assignment]
    await cog.avatar.callback(cog, ctx, member)
    embed = ctx.send.await_args.kwargs["embed"]
    assert embed.image.url == "https://cdn/a.png"


# --------------------------------------------------------------------------
# _format_uptime helper
# --------------------------------------------------------------------------


def test_format_uptime_days_hours_minutes():
    assert _format_uptime(datetime.timedelta(days=2, hours=3, minutes=4)) == "2d 3h 4m"
    assert _format_uptime(datetime.timedelta(minutes=7)) == "7m"
    assert _format_uptime(datetime.timedelta(hours=1)) == "1h 0m"
