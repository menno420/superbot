"""Fishing structures sub-hub — the 🏗 Structures child of the fishing menu.

As coral gained more sinks the fishing menu grew a button per structure (🪸 Tide
Pool, ⚓ Dock, …). ``StructuresView`` folds them into one child panel so the menu
stays lean: the menu carries a single **🏗 Structures** button, and this sub-hub
routes into each individual structure panel. It is the canonical *parent* of the
per-structure panels — their ↩ back button returns here — so the nav is a clean
two levels (menu → structures → a structure).

Read-only; every actual build still runs through the audited
:func:`services.mining_workflow.build_structure` inside the per-structure panels.
This view only shows the fleet at a glance and routes to them.
"""

from __future__ import annotations

import discord

from utils import db
from utils.mining import structures
from utils.ui_constants import GAME_COLOR
from views.base import HubView

_STRUCTURES_COLOR = discord.Color.dark_teal()


def _tide_pool_line(level: int) -> str:
    """A one-line status for the Tide Pool at *level* (bonus + built name)."""
    pct = round((structures.tide_pool_pull_mult(level) - 1.0) * 100)
    bonus = f"+{pct}% pull toward rarer fish" if pct else "not built yet"
    name = structures.level_name(structures.TIDE_POOL, level)
    return f"**{name}** ({level}/{structures.MAX_TIDE_POOL_LEVEL}) — {bonus}"


def _dock_line(level: int) -> str:
    """A one-line status for the Dock at *level* (bonus + built name)."""
    pct = round((1.0 - structures.dock_bite_speed_mult(level)) * 100)
    bonus = f"{pct}% faster bites" if pct else "not built yet"
    name = structures.level_name(structures.DOCK, level)
    return f"**{name}** ({level}/{structures.MAX_DOCK_LEVEL}) — {bonus}"


def _boathouse_line(level: int) -> str:
    """A one-line status for the Boathouse at *level* (bonus + built name)."""
    pct = round((1.0 - structures.boathouse_regen_mult(level)) * 100)
    bonus = f"{pct}% faster energy regen" if pct else "not built yet"
    name = structures.level_name(structures.BOATHOUSE, level)
    return f"**{name}** ({level}/{structures.MAX_BOATHOUSE_LEVEL}) — {bonus}"


def _fishery_line(level: int) -> str:
    """A one-line status for the Fishery at *level* (bonus + built name)."""
    pct = round(structures.fishery_bonus_chance(level) * 100)
    bonus = f"+{pct}% double-catch chance" if pct else "not built yet"
    name = structures.level_name(structures.FISHERY, level)
    return f"**{name}** ({level}/{structures.MAX_FISHERY_LEVEL}) — {bonus}"


async def build_structures_embed(user_id: int, guild_id: int) -> discord.Embed:
    """The sub-hub landing embed — every coral structure's status at a glance."""
    built = await db.get_structures(user_id, guild_id)
    embed = discord.Embed(title="🏗 Fishing structures", color=GAME_COLOR)
    embed.description = (
        "Spend the **coral** you reel in out on the **deepwater** (`!sail`) on "
        "structures that make every cast better. Pick one to build or upgrade."
    )
    embed.add_field(
        name="🪸 Tide Pool",
        value=_tide_pool_line(built.get(structures.TIDE_POOL, 0)),
        inline=False,
    )
    embed.add_field(
        name="⚓ Dock",
        value=_dock_line(built.get(structures.DOCK, 0)),
        inline=False,
    )
    embed.add_field(
        name="🛖 Boathouse",
        value=_boathouse_line(built.get(structures.BOATHOUSE, 0)),
        inline=False,
    )
    embed.add_field(
        name="🐟 Fishery",
        value=_fishery_line(built.get(structures.FISHERY, 0)),
        inline=False,
    )
    embed.set_footer(
        text="🪸 Tide Pool  •  ⚓ Dock  •  🛖 Boathouse  •  🐟 Fishery  •  ↩ Fishing menu",
    )
    return embed


class StructuresView(HubView):
    """The fishing structures sub-hub; a child of the fishing menu."""

    SUBSYSTEM = "fishing"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(
        label="Tide Pool",
        emoji="🪸",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def tide_pool_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.fishing.tide_pool import TidePoolView, build_tide_pool_embed

        embed = await build_tide_pool_embed(self._author.id, self.guild_id)
        view = TidePoolView(self._author, self.guild_id)
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message
        self.stop()

    @discord.ui.button(
        label="Dock",
        emoji="⚓",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def dock_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.fishing.dock import DockView, build_dock_embed

        embed = await build_dock_embed(self._author.id, self.guild_id)
        view = DockView(self._author, self.guild_id)
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message
        self.stop()

    @discord.ui.button(
        label="Boathouse",
        emoji="🛖",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def boathouse_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.fishing.boathouse import BoathouseView, build_boathouse_embed

        embed = await build_boathouse_embed(self._author.id, self.guild_id)
        view = BoathouseView(self._author, self.guild_id)
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message
        self.stop()

    @discord.ui.button(
        label="Fishery",
        emoji="🐟",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def fishery_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.fishing.fishery import FisheryView, build_fishery_embed

        embed = await build_fishery_embed(self._author.id, self.guild_id)
        view = FisheryView(self._author, self.guild_id)
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message
        self.stop()

    @discord.ui.button(
        label="↩ Fishing menu",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def back_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # The menu self.stop()s when it opens this sub-hub, so rebuild the fully-
        # navigable menu in place. Lazy import to respect menu→child direction.
        from views.fishing.menu import open_fishing_menu

        self.stop()
        await open_fishing_menu(interaction, self._author, self.guild_id)


async def open_structures_hub(
    interaction: discord.Interaction,
    author: discord.Member | discord.User,
    guild_id: int,
) -> None:
    """Rebuild the structures sub-hub in place — the per-structure panels' back target.

    A structure panel ``self.stop()``s when it opens, so it can't re-show an old
    sub-hub instance; it calls this to mint a fresh, fully-navigable
    :class:`StructuresView` and edit it back onto the panel message. Lazy-imported
    by the panels to respect the sub-hub → panel import direction.
    """
    view = StructuresView(author, guild_id)
    await interaction.response.edit_message(
        embed=await build_structures_embed(author.id, guild_id),
        view=view,
    )
    view.message = interaction.message


__all__ = ["StructuresView", "build_structures_embed", "open_structures_hub"]
