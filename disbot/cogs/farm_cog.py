"""Idle egg/chicken farm — Discord plumbing only.

Owner-directed task "Idle egg/chicken farm": the bot's first **idle**
(accrue-over-time) activity, alongside the active games (mining grid, fishing,
creatures). Hens lay eggs over time, you collect them for coins + game XP, and
you spend coins on more hens (faster lay rate) and a bigger coop (larger egg cap).

Domain logic, the audited write boundary, and the data live in their own modules
(mirrors the fishing decomposition):

    utils/farm/                 — pure idle domain (accrual, capacity, pricing)
    services/farm_workflow.py   — the audited write boundary (collect/buy/upgrade)
    utils/db/games/farm.py      — the chicken_farm CRUD (migration 090)

This file hosts only commands, the cog lifecycle, the Help-menu hook, and the
Explore-world registration.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from views.farm import open_farm_panel

logger = logging.getLogger("bot.cogs.farm")


class FarmCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        _register_farm_world()

    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    # ------------------------------------------------------------------ commands

    @commands.command(name="farm", aliases=["chickenfarm", "coop"])
    async def farm(self, ctx):
        """Open your idle chicken farm — collect eggs, grow your flock and coop."""
        embed, view = await open_farm_panel(ctx.author, ctx.guild.id)
        view.message = await ctx.send(embed=embed, view=view)

    # ------------------------------------------------------------------ help hook

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — the interactive farm panel."""
        return await open_farm_panel(interaction.user, interaction.guild.id)


def _register_farm_world() -> None:
    """Dock the Farm into the federated Explore world hub (idempotent).

    The opener closure lives here in the cog (it may import a view) and is passed
    to the registry as an opaque callable, so the ``services`` registry never
    gains a ``services → views`` edge (the layer's hardest rule).
    """
    from core.runtime.interaction_helpers import safe_edit
    from services.world_registry import WorldEntry, register_world_entry

    async def _open_farm_world(
        interaction: discord.Interaction,
        view: discord.ui.View,
    ) -> None:
        guild_id = interaction.guild_id
        if guild_id is None:
            await safe_edit(
                interaction,
                content="🐔 The farm is guild-only — run `!farm` in a server.",
                view=view,
            )
            return
        embed, farm_view = await open_farm_panel(interaction.user, guild_id)
        await safe_edit(
            interaction,
            embed=embed,
            view=farm_view,
            attachments=[],
        )
        farm_view.message = interaction.message

    register_world_entry(
        WorldEntry(
            key="farm",
            label="Farm",
            emoji="🐔",
            description="Raise hens that lay eggs around the clock — an idle game.",
            opener=_open_farm_world,
            order=30,
        ),
    )


async def setup(bot):
    await bot.add_cog(FarmCog(bot))
