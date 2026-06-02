"""BTD6 live events + data sources (``!btd6events`` / ``/btd6events``).

Live Ninja Kiwi data — races/bosses/CT/odyssey events, leaderboards, event
detail lookups, source-registry freshness, and AI grounding inspection —
split out of ``btd6_cog`` so the mother cog stays under the 800-LOC ceiling
(``tests/unit/invariants/test_cog_size.py``). All embed formatting lives in
``cogs.btd6._builders`` / ``cogs.btd6._event_helpers``; this cog never writes
to the source registry directly (``refresh-source`` runs through the
ingestion helpers, which own the writes).

Prefix and slash surfaces mirror each other through the shared ``build_*``
backbone; single-payload slash twins route through
``cogs.btd6._reply.reply_ephemeral``.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs.btd6 import _builders, _event_helpers
from cogs.btd6._reply import reply_ephemeral
from core.runtime.interaction_helpers import safe_defer, safe_followup

logger = logging.getLogger("bot.cogs.btd6_events")


class BTD6EventsCog(commands.Cog):
    """BTD6 live events, leaderboards, and source diagnostics. User-tier."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # Prefix surface — !btd6events ...
    # ------------------------------------------------------------------

    @commands.group(name="btd6events", invoke_without_command=True)
    async def btd6events_group(self, ctx: commands.Context) -> None:
        """BTD6 live events, leaderboards, and data-source diagnostics."""
        await ctx.send_help(ctx.command)

    @btd6events_group.command(name="live")  # type: ignore[arg-type]
    async def btd6_live(
        self,
        ctx: commands.Context,
        kind: str = "race",
        limit: int = 5,
    ) -> None:
        """Show recent live events for ``kind`` (race / boss / ct / odyssey / event)."""
        await ctx.send(embed=await _builders.build_live_events_embed(kind, limit=limit))

    @btd6events_group.command(name="event")  # type: ignore[arg-type]
    async def btd6_event(
        self,
        ctx: commands.Context,
        kind: str,
        entity_key: str,
    ) -> None:
        """Show one specific BTD6 event with its tower restrictions.

        ``kind`` is race / boss / ct / odyssey / event; ``entity_key`` is the
        event's API id (use ``!btd6events live <kind>`` to discover ids).
        """
        await ctx.send(embed=await _event_helpers.build_event_payload(kind, entity_key))

    @btd6events_group.command(name="leaderboard")  # type: ignore[arg-type]
    async def btd6_leaderboard(
        self,
        ctx: commands.Context,
        kind: str,
        event_id: str | None = None,
        limit: int = 10,
    ) -> None:
        """Top-N race or boss leaderboard. No event_id = newest active."""
        await ctx.send(
            embed=await _builders.build_leaderboard_embed(kind, event_id, limit=limit),
        )

    @btd6events_group.command(name="sources")  # type: ignore[arg-type]
    async def btd6_sources(self, ctx: commands.Context) -> None:
        """List BTD6 source registry rows."""
        await ctx.send(await _builders.build_sources_payload())

    @btd6events_group.command(name="source-health")  # type: ignore[arg-type]
    async def btd6_source_health(
        self,
        ctx: commands.Context,
        limit: int = 25,
    ) -> None:
        """Show source registry freshness (PR-D)."""
        await ctx.send(embed=await _builders.build_source_health_embed(limit=limit))

    @btd6events_group.command(name="latest-data")  # type: ignore[arg-type]
    async def btd6_latest_data(self, ctx: commands.Context) -> None:
        """Show newest fact envelope per entity_kind (PR-D)."""
        await ctx.send(embed=await _builders.build_latest_data_embed())

    @btd6events_group.command(name="refresh-source")  # type: ignore[arg-type]
    @commands.has_guild_permissions(manage_guild=True)
    async def btd6_refresh_source(
        self,
        ctx: commands.Context,
        source_key: str,
    ) -> None:
        """Manually refresh one Ninja Kiwi source (staff-only).

        Chains (``nk_btd6_ct``) expand into parent + children; single
        sources return one result.
        """
        embed = await _event_helpers.build_refresh_source_payload(
            source_key,
            started_by_user_id=ctx.author.id,
            include_exception_detail=False,
        )
        await ctx.send(embed=embed)

    @btd6events_group.command(name="grounding")  # type: ignore[arg-type]
    async def btd6_grounding(
        self,
        ctx: commands.Context,
        message_id: int,
    ) -> None:
        """Show the grounding facts that fed an AI response (PR-D)."""
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return

        payload = await _builders.build_grounding_embed(ctx.guild.id, message_id)
        if isinstance(payload, str):
            await ctx.send(payload)
        else:
            await ctx.send(embed=payload)

    # ------------------------------------------------------------------
    # Slash surface — /btd6events ... (mirrors the prefix surface)
    # ------------------------------------------------------------------

    btd6events_app_group = app_commands.Group(
        name="btd6events",
        description="BTD6 live events, leaderboards, and data sources.",
    )

    @btd6events_app_group.command(
        name="live",
        description="Show recent live events (race/boss/ct/odyssey/event).",
    )
    async def btd6_live_slash(
        self,
        interaction: discord.Interaction,
        kind: str = "race",
        limit: int = 5,
    ) -> None:
        await reply_ephemeral(
            interaction,
            _builders.build_live_events_embed(kind, limit=limit),
        )

    @btd6events_app_group.command(
        name="event",
        description="Show one specific BTD6 event with tower restrictions.",
    )
    async def btd6_event_slash(
        self,
        interaction: discord.Interaction,
        kind: str,
        entity_key: str,
    ) -> None:
        await reply_ephemeral(
            interaction,
            _event_helpers.build_event_payload(kind, entity_key),
        )

    @btd6events_app_group.command(
        name="leaderboard",
        description="Show race / boss leaderboard.",
    )
    async def btd6_leaderboard_slash(
        self,
        interaction: discord.Interaction,
        kind: str,
        event_id: str | None = None,
        limit: int = 10,
    ) -> None:
        await reply_ephemeral(
            interaction,
            _builders.build_leaderboard_embed(kind, event_id, limit=limit),
        )

    @btd6events_app_group.command(
        name="sources",
        description="List BTD6 source registry rows.",
    )
    async def btd6_sources_slash(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        payload = await _builders.build_sources_payload()
        await safe_followup(interaction, content=payload, ephemeral=True)

    @btd6events_app_group.command(
        name="source-health",
        description="BTD6 source registry freshness overview.",
    )
    async def btd6_source_health_slash(
        self,
        interaction: discord.Interaction,
        limit: int = 25,
    ) -> None:
        await reply_ephemeral(
            interaction,
            _builders.build_source_health_embed(limit=limit),
        )

    @btd6events_app_group.command(
        name="latest-data",
        description="Newest fact envelope per entity_kind.",
    )
    async def btd6_latest_data_slash(
        self,
        interaction: discord.Interaction,
    ) -> None:
        await reply_ephemeral(interaction, _builders.build_latest_data_embed())

    @btd6events_app_group.command(
        name="refresh-source",
        description="Manually refresh one Ninja Kiwi source (staff-only).",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def btd6_refresh_source_slash(
        self,
        interaction: discord.Interaction,
        source_key: str,
    ) -> None:
        await reply_ephemeral(
            interaction,
            _event_helpers.build_refresh_source_payload(
                source_key,
                started_by_user_id=interaction.user.id,
                include_exception_detail=True,
            ),
        )

    @btd6events_app_group.command(
        name="grounding",
        description="Grounding facts that fed an AI response.",
    )
    async def btd6_grounding_slash(
        self,
        interaction: discord.Interaction,
        message_id: str,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command requires a guild context.",
                ephemeral=True,
            )
            return
        try:
            mid = int(message_id)
        except ValueError:
            await interaction.response.send_message(
                f"❌ Invalid message_id: {message_id!r}",
                ephemeral=True,
            )
            return

        if not await safe_defer(interaction, ephemeral=True):
            return
        payload = await _builders.build_grounding_embed(interaction.guild.id, mid)
        if isinstance(payload, str):
            await safe_followup(interaction, content=payload, ephemeral=True)
        else:
            await safe_followup(interaction, embed=payload, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BTD6EventsCog(bot))
