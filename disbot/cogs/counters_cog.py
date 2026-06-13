"""Counters cog — the periodic server-counter rename loop + operator status.

Server counters v1 (owner decision Q-0110): keep designated channel names
showing a live server stat.  This cog is glue only — the count/rename logic
lives in :mod:`services.counter_service` and the config read model in
:mod:`services.counter_config`.  It registers its :class:`SubsystemSchema` in
``cog_load`` so the bindings are operator-editable through the existing
``!settings`` widget, and drives :func:`services.counter_service.sync_guild`
from a slow ``tasks.loop`` (never per join — Discord rate-limits channel renames
to ~2 / 10 min per channel; the loop + change-detection stay well under it).

Config: ``!settings`` → Counters.  ``!counters`` shows the current bindings +
live counts.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands, tasks

from core.runtime import resources
from services import counter_config, counter_service

logger = logging.getLogger("bot.cogs.counters")

# Slow cadence: member counts move slowly and Discord caps channel renames at
# ~2 / 10 min per channel, so a 10-minute loop renames each counter at most
# once per window — comfortably under the limit.
_COUNTER_LOOP_MINUTES = 10


class CountersCog(commands.Cog):
    """Live server-stat channels (total · humans · bots)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        from cogs.counters.schemas import register_schemas

        register_schemas()  # declares the Counters settings group.
        self._counter_sync_loop.start()

    async def cog_unload(self) -> None:
        self._counter_sync_loop.cancel()

    # -- the rename loop ------------------------------------------------------

    @tasks.loop(minutes=_COUNTER_LOOP_MINUTES)
    async def _counter_sync_loop(self) -> None:
        """Sync every guild's bound counter channels (fail-safe per guild)."""
        for guild in list(self.bot.guilds):
            try:
                await counter_service.sync_guild(guild)
            except Exception:  # noqa: BLE001 — one guild's fault must not stop the loop
                logger.exception(
                    "counters: sync_guild failed for guild=%s",
                    getattr(guild, "id", "?"),
                )

    @_counter_sync_loop.before_loop
    async def _before_counter_sync_loop(self) -> None:
        await self.bot.wait_until_ready()

    # -- status surface -------------------------------------------------------

    @staticmethod
    def _policy_embed(
        guild: discord.Guild,
        policy: counter_config.CounterPolicy,
    ) -> discord.Embed:
        """Render the effective counter policy + live values as a summary embed."""
        counts = counter_service.compute_counts(guild)
        flag = "🟢 on" if policy.enabled else "⚫ off"
        lines = [f"**Master:** {flag}", ""]
        rows = (
            (counter_config.KIND_TOTAL, policy.total_channel_id, policy.total_template),
            (
                counter_config.KIND_HUMANS,
                policy.humans_channel_id,
                policy.humans_template,
            ),
            (counter_config.KIND_BOTS, policy.bots_channel_id, policy.bots_template),
        )
        for kind, channel_id, template in rows:
            channel = (
                resources.resolve_channel(guild, channel_id=channel_id)
                if channel_id
                else None
            )
            target = channel.mention if channel else "*(unbound)*"
            rendered = counter_config.render_counter_name(
                template,
                counts.for_kind(kind),
            )
            lines.append(f"**{kind.capitalize()}** → {target}\n-# → `{rendered}`")
        embed = discord.Embed(
            title="📊 Server counters",
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )
        embed.set_footer(
            text="Configure in !settings → Counters. Channels refresh every "
            f"~{_COUNTER_LOOP_MINUTES} min (Discord rename rate limit).",
        )
        return embed

    @commands.command(
        name="counters",
        help="Show the current server-counter channels for this server.",
        extras={"classification": "primary_entrypoint"},
    )
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def counters_status(self, ctx: commands.Context) -> None:
        """Render the effective counter policy (admin/manage-guild only)."""
        policy = await counter_config.load_policy(ctx.guild.id)
        await ctx.send(embed=self._policy_embed(ctx.guild, policy))

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — the counter policy summary."""
        from views.base import HubView

        if interaction.guild is None:
            return (
                discord.Embed(description="Counters are only available in a server."),
                discord.ui.View(),
            )
        policy = await counter_config.load_policy(interaction.guild.id)
        return self._policy_embed(interaction.guild, policy), HubView(interaction.user)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CountersCog(bot))
