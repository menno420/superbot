from __future__ import annotations

import logging

import discord
from discord.ext import commands

from cogs.xp._helpers import _STAT_TYPES, _build_rank_embed
from core.runtime.interaction_helpers import help_ctx_shim
from services import xp_service
from utils import embeds as em
from views.base import send_panel
from views.xp.config_panel import XpConfigView
from views.xp.main_panel import _XpHubView
from views.xp.rank_view import _RankView

logger = logging.getLogger("bot")


class XpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        from cogs.xp.stage import XpStage
        from core.runtime import message_pipeline

        message_pipeline.register(XpStage())

    async def cog_unload(self) -> None:
        from cogs.xp.stage import XP_STAGE_NAME
        from core.runtime import message_pipeline

        message_pipeline.unregister(XP_STAGE_NAME)

    @commands.command(name="xpmenu")
    async def xp_menu(self, ctx: commands.Context):
        """Open the XP panel showing your rank and quick admin actions."""
        view = _XpHubView(ctx)
        embed = await view.build_embed()
        await send_panel(ctx, embed=embed, view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the XP hub panel)."""
        view = _XpHubView(help_ctx_shim(interaction))
        embed = await view.build_embed()
        return embed, view

    # ------------------------------------------------------------------ commands

    @commands.command(name="rank")
    async def rank(self, ctx: commands.Context, *args):
        """Show XP/coin rank.  !rank [user] [xp|coins|both]"""
        member: discord.Member = ctx.author  # type: ignore[assignment]
        stat: str = "both"
        for arg in args:
            if arg.lower() in _STAT_TYPES:
                stat = arg.lower()
            else:
                try:
                    member = await commands.MemberConverter().convert(ctx, arg)
                except commands.BadArgument:
                    pass

        embed = await _build_rank_embed(member, ctx.guild, stat)
        view = _RankView(member, ctx.guild, stat)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="givexp")
    @commands.has_permissions(administrator=True)
    async def givexp(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Give XP to a user (admin only)."""
        if amount <= 0:
            await ctx.send(embed=em.error("Amount must be positive."), delete_after=5)
            return
        result = await xp_service.award(
            guild_id=ctx.guild.id,
            user_id=member.id,
            amount=amount,
            source="admin:givexp",
        )
        await ctx.send(
            f"✅ Gave **{amount}** XP to {member.mention}. "
            f"They now have **{result.new_xp}** XP (Level **{result.new_level}**).",
        )

    @commands.command(name="resetxp")
    @commands.has_permissions(administrator=True)
    async def resetxp(self, ctx: commands.Context, member: discord.Member):
        """Reset a user's XP to zero (admin only)."""
        await xp_service.reset(
            guild_id=ctx.guild.id,
            user_id=member.id,
            source="admin:resetxp",
            actor_id=ctx.author.id,
        )
        await ctx.send(f"✅ Reset XP for {member.mention}.")

    @commands.command(name="xpconfig")
    @commands.has_permissions(administrator=True)
    async def xpconfig(self, ctx: commands.Context):
        """Open the XP configuration panel (admin only)."""
        view = XpConfigView(ctx)
        msg = await ctx.send(embed=await view.build_embed(), view=view)
        view.message = msg


async def setup(bot: commands.Bot):
    await bot.add_cog(XpCog(bot))
    logger.info("XpCog loaded.")
