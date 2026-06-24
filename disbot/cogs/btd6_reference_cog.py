"""BTD6 reference lookups — hidden ``!btd6ref`` alias of the unified ``!btd6``.

Static game-data lookups (towers, heroes, rounds, Contested Territory
relic/tile reference data) — all deterministic, sourced from
``services.btd6_knowledge_service`` via the shared ``cogs.btd6._builders``
embed builders. No provider calls, no writes.

The canonical surface is the unified ``/btd6`` tree (:mod:`cogs.btd6._unified`,
which carries the slash side); this cog keeps the ``!btd6ref`` **prefix** group
as a *hidden* alias so existing muscle-memory still works.
"""

from __future__ import annotations

import logging

from discord.ext import commands

from cogs.btd6 import _builders

logger = logging.getLogger("bot.cogs.btd6_reference")


class BTD6ReferenceCog(commands.Cog):
    """Deterministic BTD6 reference lookups. User-tier; no provider calls."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # Prefix surface — !btd6ref ...
    # ------------------------------------------------------------------

    # Hidden alias of the unified /btd6 lookups (cogs.btd6._unified). The
    # canonical surface is `!btd6 <action>` / `/btd6 <action>`; this prefix
    # group is kept (hidden) so existing `!btd6ref …` muscle-memory still works.
    @commands.group(
        name="btd6ref",
        hidden=True,
        extras={"classification": "legacy_duplicate"},
        invoke_without_command=True,
    )
    async def btd6ref_group(self, ctx: commands.Context) -> None:
        """BTD6 reference lookups — hidden alias of `!btd6` (towers/heroes/rounds/…)."""
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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BTD6ReferenceCog(bot))
