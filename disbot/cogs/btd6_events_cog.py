"""BTD6 live events + data sources — hidden ``!btd6events`` alias of ``!btd6``.

Live Ninja Kiwi data — races/bosses/CT/odyssey events, leaderboards, event
detail lookups, source-registry freshness, and AI grounding inspection. All
embed formatting lives in ``cogs.btd6._builders`` / ``cogs.btd6._event_helpers``;
this cog never writes to the source registry directly (``refresh-source`` runs
through the ingestion helpers, which own the writes).

The canonical surface is the unified ``/btd6`` tree (:mod:`cogs.btd6._unified`,
which carries the slash side); this cog keeps the ``!btd6events`` **prefix**
group as a *hidden* alias so existing muscle-memory still works.
"""

from __future__ import annotations

import logging

from discord.ext import commands

from cogs.btd6 import _builders, _event_helpers
from core.runtime.permission_checks import perms_or_owner

logger = logging.getLogger("bot.cogs.btd6_events")


class BTD6EventsCog(commands.Cog):
    """BTD6 live events, leaderboards, and source diagnostics. User-tier."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # Prefix surface — !btd6events ...
    # ------------------------------------------------------------------

    # Hidden alias of the unified `/btd6 events …` (cogs.btd6._unified). Kept
    # (hidden) so existing `!btd6events …` muscle-memory still works.
    @commands.group(
        name="btd6events",
        hidden=True,
        extras={"classification": "legacy_duplicate"},
        invoke_without_command=True,
    )
    async def btd6events_group(self, ctx: commands.Context) -> None:
        """BTD6 live events — hidden alias of `!btd6 events`."""
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
    @perms_or_owner(manage_guild=True)
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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BTD6EventsCog(bot))
