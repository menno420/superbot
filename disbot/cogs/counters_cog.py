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
from discord import app_commands
from discord.ext import commands, tasks

from core.runtime import resources
from core.runtime.permission_checks import app_perms_or_owner, perms_or_owner
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
        # Per-guild exponential backoff so a persistently-failing guild isn't
        # re-attempted every tick forever (counters completion cert punch #3).
        self._backoff = counter_service.GuildSyncBackoff()

    async def cog_load(self) -> None:
        from cogs.counters.schemas import register_schemas

        register_schemas()  # declares the Counters settings group.
        self._counter_sync_loop.start()

    async def cog_unload(self) -> None:
        self._counter_sync_loop.cancel()

    # -- the rename loop ------------------------------------------------------

    @tasks.loop(minutes=_COUNTER_LOOP_MINUTES)
    async def _counter_sync_loop(self) -> None:
        """Sync every guild's bound counter channels (fail-safe + backed-off).

        Each guild is fail-safe (one guild's fault never stops the loop) and
        rate-limited by per-guild exponential backoff: a guild that keeps
        failing is skipped for a growing number of ticks (capped, so it is
        never dropped forever), and one clean sync resets it.
        """
        for guild in list(self.bot.guilds):
            guild_id = getattr(guild, "id", 0)
            if not self._backoff.should_attempt(guild_id):
                continue
            try:
                await counter_service.sync_guild(guild)
            except Exception:  # noqa: BLE001 — one guild's fault must not stop the loop
                skip = self._backoff.record_failure(guild_id)
                logger.warning(
                    "counters: sync_guild failed for guild=%s (failure #%d) — "
                    "backing off %d loop tick(s)",
                    guild_id,
                    self._backoff.fail_streak(guild_id),
                    skip,
                    exc_info=True,
                )
            else:
                self._backoff.record_success(guild_id)

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

    @staticmethod
    def _presets_embed() -> discord.Embed:
        """List the curated template presets + how to apply one."""
        lines = []
        for preset in counter_config.TEMPLATE_PRESETS:
            sample = counter_config.render_counter_name(
                preset.template_for(counter_config.KIND_TOTAL),
                1234,
            )
            lines.append(f"**`{preset.key}`** — {preset.label}\n-# e.g. `{sample}`")
        embed = discord.Embed(
            title="🎨 Counter name presets",
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )
        embed.set_footer(
            text="Apply one with !counterpreset <name> "
            "(sets all three name templates; admin only).",
        )
        return embed

    @commands.command(
        name="counters",
        help="Show the current server-counter channels for this server.",
        extras={"classification": "primary_entrypoint"},
    )
    @commands.guild_only()
    @perms_or_owner(manage_guild=True)
    async def counters_status(self, ctx: commands.Context) -> None:
        """Render the effective counter policy (admin/manage-guild only)."""
        policy = await counter_config.load_policy(ctx.guild.id)
        await ctx.send(embed=self._policy_embed(ctx.guild, policy))

    @commands.command(
        name="counterpreset",
        help=(
            "Apply a curated counter name-template preset (sets all three "
            "templates at once). Run without a name to list the presets."
        ),
    )
    @commands.guild_only()
    @perms_or_owner(manage_guild=True)
    async def counter_preset(
        self,
        ctx: commands.Context,
        name: str | None = None,
    ) -> None:
        """Apply one of the curated template presets through the audited seam.

        With no ``name`` (or an unknown one) it lists the presets.  Applying a
        preset writes each kind's template through
        :class:`services.settings_mutation.SettingsMutationPipeline` — exactly
        as the per-template ``!settings`` widget does — so coercion, validation,
        audit, and the ``counters.settings.configure`` capability check all run.
        """
        if name is None:
            await ctx.send(embed=self._presets_embed())
            return

        preset = counter_config.get_preset(name)
        if preset is None:
            keys = ", ".join(f"`{p.key}`" for p in counter_config.TEMPLATE_PRESETS)
            await ctx.send(f"❌ Unknown preset `{name}`. Try one of: {keys}.")
            return

        from services.settings_mutation import (
            SettingsMutationError,
            SettingsMutationPipeline,
        )

        pipeline = SettingsMutationPipeline()
        try:
            for setting_name, template in counter_config.preset_setting_writes(preset):
                await pipeline.set_value(
                    ctx.guild,
                    counter_config.SUBSYSTEM,
                    setting_name,
                    template,
                    ctx.author,
                )
        except SettingsMutationError as exc:
            await ctx.send(f"❌ Could not apply preset: {type(exc).__name__}: {exc}")
            return

        await ctx.send(
            f"✅ Applied the **{preset.label}** preset to all three counter "
            "name templates. Bound channels refresh on the next sync "
            f"(~{_COUNTER_LOOP_MINUTES} min).",
        )

    @app_commands.command(
        name="counters",
        description="Show this server's live counter channels (members / humans / bots).",
    )
    @app_commands.guild_only()
    @app_perms_or_owner(manage_guild=True)
    async def counters_slash(self, interaction: discord.Interaction) -> None:
        """Slash front door for the counter status — ephemeral, manage-guild gated."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "Counters are only available in a server.",
                ephemeral=True,
            )
            return
        policy = await counter_config.load_policy(interaction.guild.id)
        await interaction.response.send_message(
            embed=self._policy_embed(interaction.guild, policy),
            ephemeral=True,
        )

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
