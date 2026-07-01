"""Server treasury — Discord plumbing only.

The bot's first **server-owned** (collective) coin pool, the seam between the
economy (per-user coins) and governance (who may spend them). Members contribute
their own coins into the pool; server managers disburse from it.

Domain logic, the audited write boundary, and the data live in their own modules
(mirrors the farm/fishing decomposition):

    services/treasury_service.py  — the audited write boundary (contribute/disburse)
    utils/db/treasury.py          — the guild_treasury CRUD (migration 092)
    views/treasury/               — the interactive panel + Contribute modal

This file hosts only commands, the cog lifecycle, and the Help-menu hook.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime.permission_checks import perms_or_owner
from services import treasury_service
from views.treasury import open_treasury_panel

logger = logging.getLogger("bot.cogs.treasury")


class TreasuryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    # ------------------------------------------------------------------ commands

    @commands.group(
        name="treasury",
        aliases=["bank", "pool"],
        invoke_without_command=True,
    )
    async def treasury(self, ctx: commands.Context) -> None:
        """Open the server treasury — view the pool and contribute coins."""
        embed, view = await open_treasury_panel(ctx.author, ctx.guild.id)
        view.message = await ctx.send(embed=embed, view=view)

    @treasury.command(name="contribute", aliases=["donate", "deposit"])  # type: ignore[arg-type]
    async def contribute(self, ctx: commands.Context, amount: int) -> None:
        """Donate *amount* of your own coins into the server treasury."""
        if amount <= 0:
            await ctx.send("➕ Contribute a positive number of coins.")
            return
        result = await treasury_service.contribute(ctx.guild.id, ctx.author.id, amount)
        await ctx.send(result.message)

    @treasury.command(name="grant", aliases=["disburse", "payout"])  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def grant(
        self,
        ctx: commands.Context,
        member: discord.Member,
        amount: int,
    ) -> None:
        """Disburse *amount* from the treasury to *member* (managers only)."""
        if amount <= 0:
            await ctx.send("🏛️ Disburse a positive number of coins.")
            return
        result = await treasury_service.disburse(
            ctx.guild.id,
            ctx.author.id,
            member.id,
            amount,
        )
        prefix = f"{member.mention} — " if result.success else ""
        await ctx.send(f"{prefix}{result.message}")

    # ------------------------------------------------------------------ help hook

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — the interactive treasury panel."""
        return await open_treasury_panel(interaction.user, interaction.guild.id)


async def setup(bot):
    await bot.add_cog(TreasuryCog(bot))
