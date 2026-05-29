"""Pro stats drill-down for a hero — a level picker (1..20) that renders the
full per-level breakdown.

The hero analogue of :mod:`views.btd6.tower_stats_view`. Reached from the hero
detail's ``🔬 Pro stats`` button (:func:`attach_hero_pro_stats_button`), which
only appears for the ~6 heroes that have a bloonswiki stats module. Extends
:class:`HubView` for the shared timeout / invoker-only / error handling.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import btd6_stats_service
from utils.btd6.stats_embed import build_pro_hero_level_embed, hero_level_label
from views.base import HubView
from views.navigation import attach_back_button

DetailRebuilder = Callable[
    [discord.Interaction],
    Awaitable[tuple[discord.Embed, discord.ui.View]],
]


class _LevelSelect(discord.ui.Select):
    """Pick a hero level; swaps the embed to that level's full stats."""

    def __init__(self, stats: btd6_stats_service.HeroStats) -> None:
        options = [
            discord.SelectOption(label=hero_level_label(code)[:100], value=code)
            for code in stats.level_codes()
        ]
        super().__init__(
            placeholder="Pick a level…",
            min_values=1,
            max_values=1,
            options=options[:25],
            row=0,
        )
        self._stats = stats

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        await safe_edit(
            interaction,
            embed=build_pro_hero_level_embed(self._stats, self.values[0]),
            view=self.view,
        )


class HeroStatsView(HubView):
    """Pro stats view: level picker + (externally attached) back button."""

    def __init__(
        self,
        author: discord.User | discord.Member,
        stats: btd6_stats_service.HeroStats,
    ) -> None:
        super().__init__(author)
        self._stats = stats
        self.add_item(_LevelSelect(stats))


class _ProStatsButton(discord.ui.Button):
    """Opens :class:`HeroStatsView`; its back button rebuilds the detail."""

    def __init__(
        self,
        stats: btd6_stats_service.HeroStats,
        detail_rebuilder: DetailRebuilder,
    ) -> None:
        super().__init__(label="🔬 Pro stats", style=discord.ButtonStyle.primary, row=2)
        self._stats = stats
        self._detail_rebuilder = detail_rebuilder

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        view = HeroStatsView(interaction.user, self._stats)
        attach_back_button(
            view,
            label="↩ Back to hero",
            custom_id=f"btd6_hero_pro:back:{self._stats.hero_id}",
            parent_builder=self._detail_rebuilder,
        )
        # Open on level 1 (the start state players see first).
        await safe_edit(
            interaction,
            embed=build_pro_hero_level_embed(self._stats, "1"),
            view=view,
        )


def attach_hero_pro_stats_button(
    detail_view: discord.ui.View,
    hero_id: str,
    detail_rebuilder: DetailRebuilder,
) -> None:
    """Add a ``🔬 Pro stats`` button to a hero-detail view when the hero has a
    per-level stats module. ``detail_rebuilder`` rebuilds the detail for the
    Pro view's back button.
    """
    stats = btd6_stats_service.get_hero_stats(hero_id)
    if stats is None or not stats.has_combat_stats:
        return
    detail_view.add_item(_ProStatsButton(stats, detail_rebuilder))


__all__ = ["HeroStatsView", "attach_hero_pro_stats_button"]
