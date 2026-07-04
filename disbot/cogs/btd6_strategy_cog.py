"""BTD6 strategy memory — hidden ``!btd6strat`` alias of ``!btd6``.

Strategy browse / submit / review. Browsing reads through
``views.btd6.strategy_browse``; pending review + submission funnel through
``services.btd6_strategy_mutation`` (the cog never writes directly).
``why-no-response`` reads the canonical ``ai_decision_audit`` table
(filtered to ``task='btd6.answer'``) to explain a missing passive reply.

The canonical surface is the unified ``/btd6`` tree (:mod:`cogs.btd6._unified`,
which carries the slash side); this cog keeps the ``!btd6strat`` **prefix**
group as a *hidden* alias so existing muscle-memory still works.
"""

from __future__ import annotations

import logging

from discord.ext import commands

from cogs.btd6 import _builders
from core.runtime.permission_checks import perms_or_owner
from views.btd6 import strategy_browse

logger = logging.getLogger("bot.cogs.btd6_strategy")


class BTD6StrategyCog(commands.Cog):
    """BTD6 strategy memory — browse, submit, review. User-tier."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # Prefix surface — !btd6strat ...
    # ------------------------------------------------------------------

    # Hidden alias of the unified `/btd6 strat …` (cogs.btd6._unified). Kept
    # (hidden) so existing `!btd6strat …` muscle-memory still works.
    @commands.group(
        name="btd6strat",
        hidden=True,
        extras={"classification": "legacy_duplicate"},
        invoke_without_command=True,
    )
    async def btd6strat_group(self, ctx: commands.Context) -> None:
        """BTD6 strategy memory — hidden alias of `!btd6 strat`."""
        await ctx.send_help(ctx.command)

    @btd6strat_group.command(name="browse")  # type: ignore[arg-type]
    async def btd6_browse(
        self,
        ctx: commands.Context,
        limit: int = 10,
    ) -> None:
        """Browse published BTD6 strategies (PR-F)."""
        await ctx.send(embed=await strategy_browse.build_browse_embed(limit=limit))

    @btd6strat_group.command(name="mine")  # type: ignore[arg-type]
    async def btd6_mine(self, ctx: commands.Context, limit: int = 10) -> None:
        """List my own strategy submissions in this guild (PR-F)."""
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return

        await ctx.send(
            embed=await strategy_browse.build_mine_embed(
                ctx.guild.id,
                ctx.author.id,
                limit=limit,
            ),
        )

    @btd6strat_group.command(name="strategy")  # type: ignore[arg-type]
    async def btd6_strategy_detail(
        self,
        ctx: commands.Context,
        strategy_id: int,
    ) -> None:
        """Show one strategy in detail (PR-F)."""
        viewer_guild = ctx.guild.id if ctx.guild else None
        payload = await strategy_browse.build_detail_embed(
            strategy_id,
            viewer_guild_id=viewer_guild,
        )
        if isinstance(payload, str):
            await ctx.send(payload)
        else:
            await ctx.send(embed=payload)

    @btd6strat_group.command(name="strategy-audit")  # type: ignore[arg-type]
    async def btd6_strategy_audit(
        self,
        ctx: commands.Context,
        strategy_id: int,
    ) -> None:
        """Show the per-strategy audit log (PR-F)."""
        await ctx.send(embed=await strategy_browse.build_audit_embed(strategy_id))

    @btd6strat_group.command(name="submit")  # type: ignore[arg-type]
    async def btd6_submit(self, ctx: commands.Context) -> None:
        """Open a strategy submission modal (slash-only on Discord).

        Discord modals are slash-only; the prefix command surfaces a
        friendly message redirecting to /btd6 strat submit.
        """
        await ctx.send(
            "Strategy submission opens a Discord modal — use `/btd6 strat submit` "
            "to fill it in.",
        )

    @btd6strat_group.command(name="pending")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def btd6_pending(self, ctx: commands.Context, limit: int = 5) -> None:
        """List pending strategy submissions with review buttons.

        Staff-only (manage_guild). Each pending strategy gets its own
        review embed + button row (Approve guild / Publish / Reject /
        Unpublish). All actions funnel through
        ``services.btd6_strategy_mutation``.
        """
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return

        payload = await _builders.build_pending_review_payload(
            ctx.guild.id,
            limit=limit,
        )
        if isinstance(payload, str):
            await ctx.send(payload)
            return
        for embed, view in payload:
            await ctx.send(embed=embed, view=view)

    @btd6strat_group.command(name="strategies")  # type: ignore[arg-type]
    async def btd6_strategies(self, ctx: commands.Context) -> None:
        """List strategy memory entries available in this guild."""
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return

        await ctx.send(await _builders.build_strategies_payload(ctx.guild.id))

    @btd6strat_group.command(name="why-no-response")  # type: ignore[arg-type]
    async def btd6_why_no_response(
        self,
        ctx: commands.Context,
        limit: int = 10,
    ) -> None:
        """Show the most recent BTD6 denials / skips for this guild.

        Reads the canonical ``ai_decision_audit`` table filtered to
        ``task='btd6.answer'`` — the legacy in-memory skip buffer of
        the retired passive stage is no longer consulted. The embed
        surfaces ``policy_snapshot_hash``, ``instruction_profile_ids``,
        ``route``, ``provider``, ``model`` and ``reason_code`` so
        operators can correlate a denial with the policy/profile state
        that produced it.
        """
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return

        payload = await _builders.build_why_no_response_payload(
            ctx.guild.id,
            limit=limit,
        )
        if isinstance(payload, str):
            await ctx.send(payload)
        else:
            await ctx.send(embed=payload)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BTD6StrategyCog(bot))
