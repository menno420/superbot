"""Paragon calculator command surface (``!paragon``).

Thin front door for the BTD6 Paragon degree calculator. The panel, modals, and
math live in ``views/btd6/paragon_view.py`` + ``services/paragon_service.py``;
this cog only opens the panel. The BTD6 hub (``!btd6``) also links to it via its
🔮 Paragon button, and the AI cog answers paragon questions through the
``btd6_paragon_calculate`` / ``btd6_paragon_requirements`` tools.

Kept as its own small cog (rather than a ``btd6_cog`` subcommand) so the BTD6
cog stays under the 800-LOC ceiling (``tests/unit/invariants/test_cog_size.py``).
"""

from __future__ import annotations

from discord.ext import commands

from views.btd6.paragon_view import ParagonCalculatorView, build_calculator_embed


class ParagonCog(commands.Cog):
    """User-tier BTD6 Paragon degree calculator front door."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="paragon")
    async def paragon(self, ctx: commands.Context) -> None:
        """Open the BTD6 Paragon degree calculator."""
        view = ParagonCalculatorView(ctx.author)
        await ctx.send(embed=build_calculator_embed(view), view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ParagonCog(bot))
