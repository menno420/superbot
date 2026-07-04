"""Fishing Tide Pool panel — the coral structure-target sink (2026-07-01).

The Tide Pool is coral's first **functional** sink: a built structure (on the
generic ``mining_structures`` table, no migration) whose rarity-pull bonus is
folded into :func:`services.fishing_workflow.begin_cast` as the cast's 5th
"how-well" knob.  This panel shows the built level, the bonus it grants, and the
next build cost (coins + coral), with a 🪸 Build button.

Every build runs through :mod:`services.mining_workflow` (one transaction per
op — coin debit + coral consume + level raise commit together, audited via the
economy log); this view is only the button that calls it.  Structurally it is a
sibling of ``views/mining/forge_panel.py`` but themed for — and reachable from —
the fishing menu.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db
from utils.mining import structures, workshop
from utils.ui_constants import ERROR_COLOR, SUCCESS_COLOR
from views.base import HubView

_TIDE_POOL_COLOR = discord.Color.teal()


def _bonus_text(level: int) -> str:
    """The rarity-pull bonus a Tide Pool at *level* grants, as a ``+N%`` label."""
    pct = round((structures.tide_pool_pull_mult(level) - 1.0) * 100)
    return f"+{pct}% pull toward rarer fish" if pct else "no bonus yet"


async def build_tide_pool_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str = "",
) -> discord.Embed:
    """The Tide Pool embed: built level, current bonus, and the next build cost."""
    built = await db.get_structures(user_id, guild_id)
    level = built.get(structures.TIDE_POOL, 0)

    embed = discord.Embed(title="🪸 Tide Pool", color=_TIDE_POOL_COLOR)
    embed.description = note or (
        "Stock a reef pool with **coral** to nudge your casts toward rarer "
        "fish. Coral drops on a **deepwater** reel (`!sail`) — the same coral "
        "you can carve into curios, now with a second, *useful* home."
    )
    embed.add_field(
        name="Level",
        value=(
            f"**{structures.level_name(structures.TIDE_POOL, level)}** "
            f"({level}/{structures.MAX_TIDE_POOL_LEVEL})"
        ),
        inline=False,
    )
    embed.add_field(
        name="Current bonus",
        value=_bonus_text(level),
        inline=False,
    )
    cost = structures.build_cost(structures.TIDE_POOL, level)
    if cost is None:
        embed.add_field(
            name="Maxed",
            value="Your Tide Pool is at its highest level — casts pull their best.",
            inline=False,
        )
        embed.set_footer(text="↩ Structures")
    else:
        nxt = structures.level_name(structures.TIDE_POOL, level + 1)
        embed.add_field(
            name=f"Next: {nxt} → {_bonus_text(level + 1)}",
            value=f"{workshop.describe_materials(cost.materials)} + **{cost.coins}** 🪙",
            inline=False,
        )
        embed.set_footer(text="🪸 Build  •  ↩ Structures")
    return embed


class TidePoolView(HubView):
    """Build/upgrade-the-Tide-Pool panel; a child of the fishing menu."""

    SUBSYSTEM = "fishing"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(label="🪸 Build", style=discord.ButtonStyle.success, row=0)
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
            structures.TIDE_POOL,
        )
        embed = await build_tide_pool_embed(
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


__all__ = ["TidePoolView", "build_tide_pool_embed"]
