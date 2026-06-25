"""Project Moon (Limbus) browse panel — embeds + an interactive view.

A read-only reference surface over :mod:`services.projmoon_data_service`: an
overview, one list per entity kind (Sinners / Sins / Damage types / E.G.O
grades / Statuses), and a per-entry detail card. The view is **public** (any
member can browse a shared reference) and inherits the universal Help/Back nav
from :class:`views.base.BaseView`.
"""

from __future__ import annotations

import discord

from services import projmoon_data_service as data
from utils.ui_constants import GAME_COLOR
from views.base import BaseView

_FOOTER = "Project Moon · Limbus Company — summarized facts (verify-at-ingest)"


def _provenance() -> str:
    return _FOOTER


def build_overview_embed() -> discord.Embed:
    """The browse landing card: what this domain knows, with counts."""
    embed = discord.Embed(
        title="🌑 Project Moon — Limbus knowledge",
        description=(
            "A browsable reference for *Limbus Company*. Pick a category below, "
            "or use `!pm <category> <name>` (e.g. `!pm status sinking`) or "
            "`!pm lookup <anything>`."
        ),
        color=GAME_COLOR,
    )
    for kind in data.entity_kinds():
        entries = data.get_entries(kind)
        names = ", ".join(e.canonical for e in entries[:6])
        if len(entries) > 6:
            names += ", …"
        embed.add_field(
            name=f"{data.KIND_LABELS[kind]} ({len(entries)})",
            value=names or "—",
            inline=False,
        )
    embed.set_footer(text=_provenance())
    return embed


def build_kind_embed(kind: str) -> discord.Embed:
    """List every entry of one entity kind."""
    entries = data.get_entries(kind)
    embed = discord.Embed(
        title=f"🌑 Limbus — {data.KIND_LABELS[kind]}",
        color=GAME_COLOR,
    )
    for entry in entries:
        suffix = ""
        if "color" in entry.extra:
            suffix = f" — {entry.extra['color']}"
        embed.add_field(
            name=f"{entry.canonical}{suffix}",
            value=entry.description,
            inline=False,
        )
    embed.set_footer(text=_provenance())
    return embed


def build_entry_embed(entry: data.LimbusEntry) -> discord.Embed:
    """A single Limbus fact, with its kind label + any extra fields."""
    embed = discord.Embed(
        title=f"🌑 {entry.canonical}",
        description=entry.description,
        color=GAME_COLOR,
    )
    embed.add_field(
        name="Category",
        value=data.KIND_LABELS[entry.entity_kind],
        inline=True,
    )
    if "color" in entry.extra:
        embed.add_field(
            name="Affinity colour",
            value=str(entry.extra["color"]),
            inline=True,
        )
    if "rank" in entry.extra:
        embed.add_field(
            name="Grade rank",
            value=f"{entry.extra['rank']} of 5",
            inline=True,
        )
    if entry.aliases:
        embed.add_field(
            name="Also known as",
            value=", ".join(entry.aliases),
            inline=False,
        )
    embed.set_footer(text=_provenance())
    return embed


class _KindButton(discord.ui.Button):
    def __init__(self, kind: str) -> None:
        super().__init__(
            label=data.KIND_LABELS[kind],
            style=discord.ButtonStyle.secondary,
        )
        self._kind = kind

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(
            embed=build_kind_embed(self._kind),
            view=self.view,
        )


class _OverviewButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Overview",
            emoji="🌑",
            style=discord.ButtonStyle.primary,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(
            embed=build_overview_embed(),
            view=self.view,
        )


class LimbusBrowseView(BaseView):
    """Public browse panel: one button per entity kind + an overview reset."""

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author, public=True, timeout=180)
        self.add_item(_OverviewButton())
        for kind in data.entity_kinds():
            self.add_item(_KindButton(kind))
