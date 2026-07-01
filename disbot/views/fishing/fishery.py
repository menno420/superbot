"""Fishing Fishery panel — the yield/abundance coral structure (fourth structure, 2026-07-01).

The Fishery is the **fourth** coral structure (after the Tide Pool, the Dock, and the
Boathouse). It gives coral a genuinely distinct *fourth* payoff — a higher **lucky
double-catch** chance (yield / abundance), where the Tide Pool is quality (rarer fish),
the Dock is per-cast throughput (faster bites), and the Boathouse is endurance (faster
energy regen). A well-stocked fishery keeps the waters plentiful, so a landed reel is
more likely to hook a *second* copy of the same fish — extra craft fodder / sell
material — folded into :func:`services.fishing_workflow.commit_catch`.

Every build runs through :mod:`services.mining_workflow` (one audited transaction —
coin debit + material consume + level raise); this view is only the button that calls
it. Structurally a twin of ``views/fishing/boathouse.py``.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db
from utils.mining import structures, workshop
from utils.ui_constants import ERROR_COLOR, SUCCESS_COLOR
from views.base import HubView

_FISHERY_COLOR = discord.Color.dark_teal()


def _bonus_text(level: int) -> str:
    """The double-catch bonus a Fishery at *level* grants, as a ``+N% double catch`` label."""
    pct = round(structures.fishery_bonus_chance(level) * 100)
    return f"+{pct}% double-catch chance" if pct else "no bonus yet"


async def build_fishery_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str = "",
) -> discord.Embed:
    """The Fishery embed: built level, current double-catch bonus, and the next cost."""
    built = await db.get_structures(user_id, guild_id)
    level = built.get(structures.FISHERY, 0)

    embed = discord.Embed(title="🐟 Fishery", color=_FISHERY_COLOR)
    embed.description = note or (
        "Build a fishery with **coral** and **wood** to keep the waters well-stocked — "
        "a landed reel is more likely to hook a **second** fish (extra craft fodder). "
        "Coral drops on a **deepwater** reel (`!sail`); wood you already mine. More fish "
        "per catch (Fishery) vs. rarer fish (Tide Pool) vs. faster bites (Dock) vs. "
        "faster energy (Boathouse) — spend your coral where you like."
    )
    embed.add_field(
        name="Level",
        value=(
            f"**{structures.level_name(structures.FISHERY, level)}** "
            f"({level}/{structures.MAX_FISHERY_LEVEL})"
        ),
        inline=False,
    )
    embed.add_field(name="Current bonus", value=_bonus_text(level), inline=False)
    cost = structures.build_cost(structures.FISHERY, level)
    if cost is None:
        embed.add_field(
            name="Maxed",
            value="Your Fishery is at its highest level — double catches as often as it gets.",
            inline=False,
        )
        embed.set_footer(text="↩ Structures")
    else:
        nxt = structures.level_name(structures.FISHERY, level + 1)
        embed.add_field(
            name=f"Next: {nxt} → {_bonus_text(level + 1)}",
            value=f"{workshop.describe_materials(cost.materials)} + **{cost.coins}** 🪙",
            inline=False,
        )
        embed.set_footer(text="🐟 Build  •  ↩ Structures")
    return embed


class FisheryView(HubView):
    """Build/upgrade-the-Fishery panel; a child of the fishing menu."""

    SUBSYSTEM = "fishing"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(label="🐟 Build", style=discord.ButtonStyle.success, row=0)
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
            structures.FISHERY,
        )
        embed = await build_fishery_embed(
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


__all__ = ["FisheryView", "build_fishery_embed"]
