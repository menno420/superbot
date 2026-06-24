"""BTD6 reference lookups (``!btd6ref`` / ``/btd6ref``).

Static game-data lookups split out of ``btd6_cog`` so the mother cog stays
under the 800-LOC ceiling (``tests/unit/invariants/test_cog_size.py``).
Towers, heroes, rounds, and Contested Territory relic/tile reference data —
all deterministic, sourced from ``services.btd6_knowledge_service`` via the
shared ``cogs.btd6._builders`` embed builders. No provider calls, no writes.

Prefix and slash surfaces mirror each other through the shared ``build_*``
backbone; single-payload slash twins route through
``cogs.btd6._reply.reply_ephemeral`` for the ``safe_defer → build →
safe_followup`` ordering.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs.btd6 import _builders
from cogs.btd6._reply import reply_ephemeral
from core.runtime.interaction_helpers import safe_defer, safe_followup

logger = logging.getLogger("bot.cogs.btd6_reference")


class BTD6ReferenceCog(commands.Cog):
    """Deterministic BTD6 reference lookups. User-tier; no provider calls."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # Prefix surface — !btd6ref ...
    # ------------------------------------------------------------------

    @commands.group(name="btd6ref", invoke_without_command=True)
    async def btd6ref_group(self, ctx: commands.Context) -> None:
        """BTD6 reference lookups (towers / heroes / rounds / relics / CT)."""
        await ctx.send_help(ctx.command)

    @btd6ref_group.command(name="tower")  # type: ignore[arg-type]
    async def btd6_tower(self, ctx: commands.Context, *, name: str) -> None:
        await ctx.send(embed=await _builders.build_tower_embed(name))

    @btd6ref_group.command(name="hero")  # type: ignore[arg-type]
    async def btd6_hero(self, ctx: commands.Context, *, name: str) -> None:
        await ctx.send(embed=await _builders.build_hero_embed(name))

    @btd6ref_group.command(name="round")  # type: ignore[arg-type]
    async def btd6_round(
        self,
        ctx: commands.Context,
        number: int,
        end_round: int | None = None,
    ) -> None:
        """A single round's detail, or a values table across a round range."""
        await ctx.send(embed=await _builders.build_round_embed(number, end_round))

    @btd6ref_group.command(name="income")  # type: ignore[arg-type]
    async def btd6_income(
        self,
        ctx: commands.Context,
        start_round: int,
        end_round: int | None = None,
    ) -> None:
        """Verified cash per round — single round or an inclusive range."""
        await ctx.send(embed=await _builders.build_income_embed(start_round, end_round))

    @btd6ref_group.command(name="rbe")  # type: ignore[arg-type]
    async def btd6_rbe(
        self,
        ctx: commands.Context,
        start_round: int,
        end_round: int | None = None,
    ) -> None:
        """RBE per round (base + freeplay-scaled) — single round or a range."""
        await ctx.send(embed=await _builders.build_rbe_embed(start_round, end_round))

    @btd6ref_group.command(name="relic")  # type: ignore[arg-type]
    async def btd6_relic(self, ctx: commands.Context, *, name: str) -> None:
        """CT relic effect + current tile (by name / abbrev e.g. SMS / alias)."""
        await ctx.send(embed=await _builders.build_ct_relic_embed(name))

    @btd6ref_group.command(name="ct")  # type: ignore[arg-type]
    async def btd6_ct(self, ctx: commands.Context) -> None:
        """Browse active Contested Territory events and their relic tiles."""
        await ctx.send(embed=await _builders.build_ct_browser_embed())

    # ------------------------------------------------------------------
    # Slash surface — /btd6ref ... (mirrors the prefix surface)
    # ------------------------------------------------------------------

    btd6ref_app_group = app_commands.Group(
        name="btd6ref",
        description="BTD6 reference — tower/hero/round/relic/CT lookups.",
    )

    @btd6ref_app_group.command(name="tower", description="Look up a tower.")
    async def btd6_tower_slash(
        self,
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        await reply_ephemeral(interaction, _builders.build_tower_embed(name))

    @btd6ref_app_group.command(name="hero", description="Look up a hero.")
    async def btd6_hero_slash(
        self,
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        embed = await _builders.build_hero_embed(name)
        await safe_followup(interaction, embed=embed, ephemeral=True)

    @btd6ref_app_group.command(
        name="round",
        description="Look up a round, or a values table across a range of rounds.",
    )
    @app_commands.describe(
        number="The round (or first round of a range).",
        end_round="Last round of an inclusive range (omit for a single round).",
    )
    async def btd6_round_slash(
        self,
        interaction: discord.Interaction,
        number: int,
        end_round: int | None = None,
    ) -> None:
        embed = await _builders.build_round_embed(number, end_round)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @btd6ref_app_group.command(
        name="income",
        description="Verified cash earned per round (single round or a range).",
    )
    @app_commands.describe(
        start_round="The round (or first round of a range).",
        end_round="Last round of an inclusive range (omit for a single round).",
        roundset="Round set: 'default' (standard) or 'abr' (alternate).",
    )
    async def btd6_income_slash(
        self,
        interaction: discord.Interaction,
        start_round: int,
        end_round: int | None = None,
        roundset: str = "default",
    ) -> None:
        embed = await _builders.build_income_embed(start_round, end_round, roundset)
        await interaction.response.send_message(embed=embed)

    @btd6ref_app_group.command(
        name="rbe",
        description="RBE per round — base + freeplay-scaled (single round or a range).",
    )
    @app_commands.describe(
        start_round="The round (or first round of a range).",
        end_round="Last round of an inclusive range (omit for a single round).",
    )
    async def btd6_rbe_slash(
        self,
        interaction: discord.Interaction,
        start_round: int,
        end_round: int | None = None,
    ) -> None:
        embed = await _builders.build_rbe_embed(start_round, end_round)
        await interaction.response.send_message(embed=embed)

    @btd6ref_app_group.command(
        name="relic",
        description="Look up a Contested Territory relic's effect and tile.",
    )
    async def btd6_relic_slash(
        self,
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        await reply_ephemeral(interaction, _builders.build_ct_relic_embed(name))

    @btd6ref_app_group.command(
        name="ct",
        description="Browse active Contested Territory events and relic tiles.",
    )
    async def btd6_ct_slash(self, interaction: discord.Interaction) -> None:
        await reply_ephemeral(interaction, _builders.build_ct_browser_embed())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BTD6ReferenceCog(bot))
