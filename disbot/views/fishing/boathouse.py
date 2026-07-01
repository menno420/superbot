"""Fishing Boathouse panel — the energy-regen coral structure (third structure, 2026-07-01).

The Boathouse is the **third** coral structure (after the Tide Pool and the Dock). It
gives coral a distinct *third* payoff — faster **fishing energy regen** (endurance),
where the Tide Pool is quality (rarer fish) and the Dock is per-cast throughput (faster
bites). Each level shortens the passive energy-refill interval via a ``regen``
multiplier ≤ 1.0 folded into :func:`services.fishing_workflow.begin_cast` /
:func:`services.fishing_workflow.get_energy` — so a heavy fisher spends less time waiting
for the line to rest.

Every build runs through :mod:`services.mining_workflow` (one audited transaction —
coin debit + material consume + level raise); this view is only the button that calls
it. Structurally a twin of ``views/fishing/dock.py``.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db
from utils.mining import structures, workshop
from utils.ui_constants import ERROR_COLOR, SUCCESS_COLOR
from views.base import HubView

_BOATHOUSE_COLOR = discord.Color.dark_teal()


def _bonus_text(level: int) -> str:
    """The energy-regen bonus a Boathouse at *level* grants, as a ``N% faster`` label."""
    pct = round((1.0 - structures.boathouse_regen_mult(level)) * 100)
    return f"{pct}% faster energy regen" if pct else "no bonus yet"


async def build_boathouse_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str = "",
) -> discord.Embed:
    """The Boathouse embed: built level, current regen bonus, and the next cost."""
    built = await db.get_structures(user_id, guild_id)
    level = built.get(structures.BOATHOUSE, 0)

    embed = discord.Embed(title="🛖 Boathouse", color=_BOATHOUSE_COLOR)
    embed.description = note or (
        "Build a boathouse with **coral** and **wood** so your fishing energy refills "
        "faster — less waiting when the line needs to rest. Coral drops on a "
        "**deepwater** reel (`!sail`); wood you already mine. More fishing (Boathouse) "
        "vs. rarer fish (Tide Pool) vs. faster bites (Dock) — spend your coral where you like."
    )
    embed.add_field(
        name="Level",
        value=(
            f"**{structures.level_name(structures.BOATHOUSE, level)}** "
            f"({level}/{structures.MAX_BOATHOUSE_LEVEL})"
        ),
        inline=False,
    )
    embed.add_field(name="Current bonus", value=_bonus_text(level), inline=False)
    cost = structures.build_cost(structures.BOATHOUSE, level)
    if cost is None:
        embed.add_field(
            name="Maxed",
            value="Your Boathouse is at its highest level — energy refills as fast as it gets.",
            inline=False,
        )
        embed.set_footer(text="↩ Structures")
    else:
        nxt = structures.level_name(structures.BOATHOUSE, level + 1)
        embed.add_field(
            name=f"Next: {nxt} → {_bonus_text(level + 1)}",
            value=f"{workshop.describe_materials(cost.materials)} + **{cost.coins}** 🪙",
            inline=False,
        )
        embed.set_footer(text="🛖 Build  •  ↩ Structures")
    return embed


class BoathouseView(HubView):
    """Build/upgrade-the-Boathouse panel; a child of the fishing menu."""

    SUBSYSTEM = "fishing"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(label="🛖 Build", style=discord.ButtonStyle.success, row=0)
    async def build_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.build_structure(
            self._author.id,
            self.guild_id,
            structures.BOATHOUSE,
        )
        embed = await build_boathouse_embed(
            self._author.id,
            self.guild_id,
            note=("✅ " if result.ok else "❌ ") + result.message,
        )
        embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="↩ Structures",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def back_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # The structures sub-hub self.stop()s when it opens this panel, so rebuild
        # it in place. Lazy import to respect the sub-hub → panel direction.
        from views.fishing.structures_hub import open_structures_hub

        self.stop()
        await open_structures_hub(interaction, self._author, self.guild_id)


__all__ = ["BoathouseView", "build_boathouse_embed"]
