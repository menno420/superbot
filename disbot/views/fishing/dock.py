"""Fishing Dock panel — the bite-speed coral structure (Tide Pool's sibling, 2026-07-01).

The Dock is the *entry* coral structure: cheaper than the Tide Pool and it adds a
common material (wood), with a different payoff — it speeds up the **bite** (a
``bite_speed`` multiplier ≤ 1.0 folded into
:func:`services.fishing_workflow.begin_cast`) rather than pulling rarer fish. So a
coral investment is a real choice: faster fishing (Dock) vs. rarer catches (Tide
Pool).

Every build runs through :mod:`services.mining_workflow` (one audited transaction —
coin debit + material consume + level raise); this view is only the button that
calls it. Structurally a twin of ``views/fishing/tide_pool.py``.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db
from utils.mining import structures, workshop
from utils.ui_constants import ERROR_COLOR, SUCCESS_COLOR
from views.base import HubView

_DOCK_COLOR = discord.Color.dark_teal()


def _bonus_text(level: int) -> str:
    """The bite-speed bonus a Dock at *level* grants, as a ``N% faster`` label."""
    pct = round((1.0 - structures.dock_bite_speed_mult(level)) * 100)
    return f"{pct}% faster bites" if pct else "no bonus yet"


async def build_dock_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str = "",
) -> discord.Embed:
    """The Dock embed: built level, current bite-speed bonus, and the next cost."""
    built = await db.get_structures(user_id, guild_id)
    level = built.get(structures.DOCK, 0)

    embed = discord.Embed(title="⚓ Dock", color=_DOCK_COLOR)
    embed.description = note or (
        "Build a dock with **coral** and **wood** so the fish bite sooner — the "
        "cheap, early counterpart to the Tide Pool. Coral drops on a **deepwater** "
        "reel (`!sail`); wood you already mine. Faster bites vs. the Tide Pool's "
        "rarer fish — spend your coral where you like."
    )
    embed.add_field(
        name="Level",
        value=(
            f"**{structures.level_name(structures.DOCK, level)}** "
            f"({level}/{structures.MAX_DOCK_LEVEL})"
        ),
        inline=False,
    )
    embed.add_field(name="Current bonus", value=_bonus_text(level), inline=False)
    cost = structures.build_cost(structures.DOCK, level)
    if cost is None:
        embed.add_field(
            name="Maxed",
            value="Your Dock is at its highest level — the bite is as quick as it gets.",
            inline=False,
        )
        embed.set_footer(text="↩ Structures")
    else:
        nxt = structures.level_name(structures.DOCK, level + 1)
        embed.add_field(
            name=f"Next: {nxt} → {_bonus_text(level + 1)}",
            value=f"{workshop.describe_materials(cost.materials)} + **{cost.coins}** 🪙",
            inline=False,
        )
        embed.set_footer(text="⚓ Build  •  ↩ Structures")
    return embed


class DockView(HubView):
    """Build/upgrade-the-Dock panel; a child of the fishing menu."""

    SUBSYSTEM = "fishing"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(label="⚓ Build", style=discord.ButtonStyle.success, row=0)
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
            structures.DOCK,
        )
        embed = await build_dock_embed(
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


__all__ = ["DockView", "build_dock_embed"]
