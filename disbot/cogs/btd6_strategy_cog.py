"""BTD6 strategy memory (``!btd6strat`` / ``/btd6strat``).

Strategy browse / submit / review surface split out of ``btd6_cog`` so the
mother cog stays under the 800-LOC ceiling
(``tests/unit/invariants/test_cog_size.py``). Browsing reads through
``views.btd6.strategy_browse``; pending review + submission funnel through
``services.btd6_strategy_mutation`` (the cog never writes directly).
``why-no-response`` reads the canonical ``ai_decision_audit`` table
(filtered to ``task='btd6.answer'``) to explain a missing passive reply.

Prefix and slash surfaces mirror each other through the shared ``build_*``
backbone; single-payload slash twins route through
``cogs.btd6._reply.reply_ephemeral``. ``submit`` is intentionally
slash-divergent (a Discord modal can only open from a slash interaction;
the prefix form redirects), so it is exempt from twin-backbone parity.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs.btd6 import _builders
from cogs.btd6._reply import reply_ephemeral
from core.runtime.interaction_helpers import safe_defer, safe_followup
from views.btd6 import strategy_browse

logger = logging.getLogger("bot.cogs.btd6_strategy")


class BTD6StrategyCog(commands.Cog):
    """BTD6 strategy memory — browse, submit, review. User-tier."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # Prefix surface — !btd6strat ...
    # ------------------------------------------------------------------

    @commands.group(name="btd6strat", invoke_without_command=True)
    async def btd6strat_group(self, ctx: commands.Context) -> None:
        """BTD6 strategy memory (browse / submit / review)."""
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
        friendly message redirecting to /btd6strat submit.
        """
        await ctx.send(
            "Strategy submission opens a Discord modal — use `/btd6strat submit` "
            "to fill it in.",
        )

    @btd6strat_group.command(name="pending")  # type: ignore[arg-type]
    @commands.has_guild_permissions(manage_guild=True)
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

    # ------------------------------------------------------------------
    # Slash surface — /btd6strat ... (mirrors the prefix surface)
    # ------------------------------------------------------------------

    btd6strat_app_group = app_commands.Group(
        name="btd6strat",
        description="BTD6 strategy memory — browse, submit, review.",
    )

    @btd6strat_app_group.command(
        name="browse",
        description="Browse published BTD6 strategies.",
    )
    async def btd6_browse_slash(
        self,
        interaction: discord.Interaction,
        limit: int = 10,
    ) -> None:
        await reply_ephemeral(
            interaction,
            strategy_browse.build_browse_embed(limit=limit),
        )

    @btd6strat_app_group.command(
        name="mine",
        description="List my own strategy submissions in this guild.",
    )
    async def btd6_mine_slash(
        self,
        interaction: discord.Interaction,
        limit: int = 10,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command requires a guild context.",
                ephemeral=True,
            )
            return

        await reply_ephemeral(
            interaction,
            strategy_browse.build_mine_embed(
                interaction.guild.id,
                interaction.user.id,
                limit=limit,
            ),
        )

    @btd6strat_app_group.command(
        name="strategy",
        description="Show one strategy in detail.",
    )
    async def btd6_strategy_slash(
        self,
        interaction: discord.Interaction,
        strategy_id: int,
    ) -> None:
        viewer_guild = interaction.guild.id if interaction.guild else None
        await reply_ephemeral(
            interaction,
            strategy_browse.build_detail_embed(
                strategy_id,
                viewer_guild_id=viewer_guild,
            ),
        )

    @btd6strat_app_group.command(
        name="strategy-audit",
        description="Per-strategy audit log.",
    )
    async def btd6_strategy_audit_slash(
        self,
        interaction: discord.Interaction,
        strategy_id: int,
    ) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        embed = await strategy_browse.build_audit_embed(strategy_id)
        await safe_followup(interaction, embed=embed, ephemeral=True)

    @btd6strat_app_group.command(
        name="submit",
        description="Submit a BTD6 strategy.",
    )
    async def btd6_submit_slash(self, interaction: discord.Interaction) -> None:
        from views.btd6.strategy_submit import StrategySubmitModal

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Submitting a strategy requires a guild context.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(StrategySubmitModal())

    @btd6strat_app_group.command(
        name="pending",
        description="List pending strategy submissions (staff-only).",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def btd6_pending_slash(
        self,
        interaction: discord.Interaction,
        limit: int = 5,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command requires a guild context.",
                ephemeral=True,
            )
            return

        if not await safe_defer(interaction, ephemeral=True):
            return
        payload = await _builders.build_pending_review_payload(
            interaction.guild.id,
            limit=limit,
        )
        if isinstance(payload, str):
            await safe_followup(interaction, payload, ephemeral=True)
            return
        # Uniform: every page goes through safe_followup after one defer.
        for embed, view in payload:
            await safe_followup(
                interaction,
                embed=embed,
                view=view,
                ephemeral=True,
            )

    @btd6strat_app_group.command(
        name="strategies",
        description="List strategy memory entries available in this guild.",
    )
    async def btd6_strategies_slash(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command requires a guild context.",
                ephemeral=True,
            )
            return

        if not await safe_defer(interaction, ephemeral=True):
            return
        payload = await _builders.build_strategies_payload(interaction.guild.id)
        await safe_followup(interaction, content=payload, ephemeral=True)

    @btd6strat_app_group.command(
        name="why-no-response",
        description="Recent BTD6 denials/skips for this guild.",
    )
    async def btd6_why_no_response_slash(
        self,
        interaction: discord.Interaction,
        limit: int = 10,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command requires a guild context.",
                ephemeral=True,
            )
            return

        await reply_ephemeral(
            interaction,
            _builders.build_why_no_response_payload(interaction.guild.id, limit=limit),
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BTD6StrategyCog(bot))
