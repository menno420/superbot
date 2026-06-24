"""BTD6 ingestion operations — hidden ``!btd6ops`` alias of ``/btd6 ops …``.

The canonical surface is the unified ``/btd6 ops …`` / ``!btd6 ops …`` tree
(:mod:`cogs.btd6._unified`); this cog keeps the legacy ``!btd6ops`` **prefix**
group as a *hidden* alias so existing operator muscle-memory still works. The
shared readiness / runs / source-toggle / seed / announce helpers live in
:mod:`cogs.btd6._ops_helpers` and are called by both surfaces — every write
still funnels through ``services.btd6_source_mutation`` /
``services.btd6_data_service``.

Gating is intentionally mixed and enforced inline (friendly denial message)
*and* re-checked server-side by the mutation service (defense in depth):

* ``readiness`` / ``runs``  — staff  (``is_staff_member``: admin OR manage_guild)
* ``source_enable`` / ``source_disable`` — admin (``is_administrator_member``)
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from cogs.btd6 import _ops_helpers
from utils.discord_permissions import is_administrator_member, is_staff_member

logger = logging.getLogger("bot.cogs.btd6_ops")


class BTD6OpsCog(commands.Cog):
    """Operator surface for BTD6 ingestion readiness + source control."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # Prefix surface — !btd6ops ... (hidden alias of !btd6 ops ...)
    # ------------------------------------------------------------------

    @commands.group(
        name="btd6ops",
        hidden=True,
        extras={"classification": "legacy_duplicate"},
        invoke_without_command=True,
    )
    @commands.guild_only()
    async def btd6ops(self, ctx: commands.Context) -> None:
        """BTD6 ingestion operations — hidden alias of `!btd6 ops`."""
        await ctx.send_help(ctx.command)

    @btd6ops.command(name="readiness")  # type: ignore[arg-type]
    async def readiness_prefix(self, ctx: commands.Context) -> None:
        if not is_staff_member(ctx.author):
            await ctx.send(_ops_helpers.STAFF_DENIED)
            return
        await ctx.send(embed=await _ops_helpers.readiness_embed())

    @btd6ops.command(name="runs")  # type: ignore[arg-type]
    async def runs_prefix(
        self,
        ctx: commands.Context,
        source_key: str | None = None,
        limit: int = _ops_helpers.RUNS_DEFAULT_LIMIT,
    ) -> None:
        if not is_staff_member(ctx.author):
            await ctx.send(_ops_helpers.STAFF_DENIED)
            return
        await ctx.send(embed=await _ops_helpers.runs_embed(source_key, limit))

    @btd6ops.command(name="source_enable")  # type: ignore[arg-type]
    async def source_enable_prefix(
        self,
        ctx: commands.Context,
        source_key: str,
    ) -> None:
        if not is_administrator_member(ctx.author):
            await ctx.send(_ops_helpers.ADMIN_DENIED)
            return
        await ctx.send(
            await _ops_helpers.toggle_source(ctx.author, source_key, enabled=True),
        )

    @btd6ops.command(name="source_disable")  # type: ignore[arg-type]
    async def source_disable_prefix(
        self,
        ctx: commands.Context,
        source_key: str,
    ) -> None:
        if not is_administrator_member(ctx.author):
            await ctx.send(_ops_helpers.ADMIN_DENIED)
            return
        await ctx.send(
            await _ops_helpers.toggle_source(ctx.author, source_key, enabled=False),
        )

    @btd6ops.command(name="seed-data")  # type: ignore[arg-type]
    async def seed_data_prefix(self, ctx: commands.Context) -> None:
        """Seed the Postgres data store from the bundled files (administrator)."""
        if not is_administrator_member(ctx.author):
            await ctx.send(_ops_helpers.ADMIN_DENIED)
            return
        await ctx.send(embed=await _ops_helpers.seed_embed())

    @btd6ops.command(name="announcechannel")  # type: ignore[arg-type]
    async def announce_channel_prefix(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel | None = None,
    ) -> None:
        """Set/clear the BTD6 new-version announcement channel (administrator).

        ``!btd6ops announcechannel #updates`` routes new-version
        announcements there; with no channel it clears (disables) them.
        """
        if not is_administrator_member(ctx.author):
            await ctx.send(_ops_helpers.ADMIN_DENIED)
            return
        if ctx.guild is None:
            return
        await ctx.send(await _ops_helpers.set_announce_channel(ctx.guild.id, channel))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BTD6OpsCog(bot))
