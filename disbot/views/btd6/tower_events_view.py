"""Event-restriction drill-down for a tower.

Reached from the tower detail's ``⚠️ Event status`` button
(:func:`attach_event_status_button`). Keeps the live race/boss/challenge
ban/limit data off the main overview (which was getting crowded) and in its
own view, mirroring the ``🔬 Pro stats`` drill-down.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from views.base import HubView
from views.navigation import attach_back_button

DetailRebuilder = Callable[
    [discord.Interaction],
    Awaitable[tuple[discord.Embed, discord.ui.View]],
]


def build_event_embed(canonical: str, restrictions: tuple[Any, ...]) -> discord.Embed:
    """Embed listing the current event restrictions affecting a tower."""
    from services.btd6_response_builder import format_restriction_lines

    lines = format_restriction_lines(restrictions)
    embed = discord.Embed(
        title=f"⚠️ {canonical} — event status",
        color=discord.Color.gold(),
    )
    embed.description = (
        "\n".join(f"• {line}" for line in lines)
        if lines
        else "No active event restrictions for this tower."
    )
    return embed


class TowerEventsView(HubView):
    """Holds the back button; the event data is in the embed."""


class _EventStatusButton(discord.ui.Button):
    def __init__(
        self,
        canonical: str,
        restrictions: tuple[Any, ...],
        count: int,
        detail_rebuilder: DetailRebuilder,
    ) -> None:
        super().__init__(
            label=f"⚠️ Event status ({count})",
            style=discord.ButtonStyle.secondary,
            row=2,
        )
        self._canonical = canonical
        self._restrictions = restrictions
        self._detail_rebuilder = detail_rebuilder

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        view = TowerEventsView(interaction.user)
        attach_back_button(
            view,
            label="↩ Back to tower",
            custom_id="btd6_events:back",
            parent_builder=self._detail_rebuilder,
        )
        await safe_edit(
            interaction,
            embed=build_event_embed(self._canonical, self._restrictions),
            view=view,
        )


def attach_event_status_button(
    detail_view: discord.ui.View,
    canonical: str,
    restrictions: tuple[Any, ...],
    detail_rebuilder: DetailRebuilder,
) -> None:
    """Add an ``⚠️ Event status`` button when the tower has active restrictions."""
    from services.btd6_response_builder import format_restriction_lines

    lines = format_restriction_lines(restrictions)
    if not lines:
        return
    detail_view.add_item(
        _EventStatusButton(canonical, restrictions, len(lines), detail_rebuilder),
    )


__all__ = ["TowerEventsView", "attach_event_status_button", "build_event_embed"]
