"""Pro stats drill-down for a tower — a two-step tier/crosspath picker that
renders the full per-tier breakdown.

Reached from the tower detail's ``🔬 Pro stats`` button
(:func:`attach_pro_stats_button`). Extends :class:`HubView` for the shared
timeout / invoker-only / error handling, like the rest of ``views/btd6/``.

The picker is two-step because a tower now carries up to ~64 crosspath tiers,
far past Discord's 25-option select cap: row 0 picks a single-path tier (≤16);
selecting one that has crosspaths reveals a second select (row 1) with just that
tier's handful of crosspaths. Everything is ephemeral / invoker-scoped, so
browsing never mutates a shared panel.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import btd6_stats_service
from utils.btd6 import tier_codes
from utils.btd6.stats_embed import build_pro_tier_embed, tier_label
from views.base import HubView
from views.navigation import attach_back_button

DetailRebuilder = Callable[
    [discord.Interaction],
    Awaitable[tuple[discord.Embed, discord.ui.View]],
]


class _CrosspathSelect(discord.ui.Select):
    """Second-step select: the crosspaths built on a chosen single-path tier."""

    def __init__(
        self,
        stats: btd6_stats_service.TowerStats,
        single_code: str,
        codes: tuple[str, ...],
    ) -> None:
        options = [
            discord.SelectOption(label=tier_label(stats, code)[:100], value=code)
            for code in codes[:25]
        ]
        super().__init__(
            placeholder=f"{tier_codes.format_code(single_code)} crosspaths…",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
        )
        self._stats = stats

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        await safe_edit(
            interaction,
            embed=build_pro_tier_embed(self._stats, self.values[0]),
            view=self.view,
        )


class _TierSelect(discord.ui.Select):
    """First-step select: base + the 16 single-path tiers (always ≤25 options)."""

    def __init__(self, stats: btd6_stats_service.TowerStats) -> None:
        codes = [c for c in stats.tier_codes() if c in tier_codes.SINGLE_PATH_CODES]
        options = [
            discord.SelectOption(label=tier_label(stats, code)[:100], value=code)
            for code in codes
        ]
        super().__init__(
            placeholder="Pick a tier…",
            min_values=1,
            max_values=1,
            options=options[:25],
            row=0,
        )
        self._stats = stats

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        code = self.values[0]
        view = self.view
        if isinstance(view, TowerStatsView):
            view.show_crosspaths_for(code)
        await safe_edit(
            interaction,
            embed=build_pro_tier_embed(self._stats, code),
            view=view,
        )


class TowerStatsView(HubView):
    """Pro stats view: single-path tier picker, then a crosspath sub-picker."""

    def __init__(
        self,
        author: discord.User | discord.Member,
        stats: btd6_stats_service.TowerStats,
    ) -> None:
        super().__init__(author)
        self._stats = stats
        self._crosspath_select: _CrosspathSelect | None = None
        self.add_item(_TierSelect(stats))

    def show_crosspaths_for(self, single_code: str) -> None:
        """Reveal (or clear) the crosspath sub-picker for a single-path tier."""
        if self._crosspath_select is not None:
            self.remove_item(self._crosspath_select)
            self._crosspath_select = None
        codes = self._stats.crosspaths_for(single_code)
        if codes:
            self._crosspath_select = _CrosspathSelect(self._stats, single_code, codes)
            self.add_item(self._crosspath_select)


class _ProStatsButton(discord.ui.Button):
    """Opens :class:`TowerStatsView`; its back button rebuilds the detail."""

    def __init__(
        self,
        stats: btd6_stats_service.TowerStats,
        detail_rebuilder: DetailRebuilder,
    ) -> None:
        super().__init__(label="🔬 Pro stats", style=discord.ButtonStyle.primary, row=2)
        self._stats = stats
        self._detail_rebuilder = detail_rebuilder

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        view = TowerStatsView(interaction.user, self._stats)
        attach_back_button(
            view,
            label="↩ Back to tower",
            custom_id=f"btd6_pro:back:{self._stats.tower_id}",
            parent_builder=self._detail_rebuilder,
        )
        await safe_edit(
            interaction,
            embed=build_pro_tier_embed(self._stats, "000"),
            view=view,
        )


def attach_pro_stats_button(
    detail_view: discord.ui.View,
    tower_id: str,
    detail_rebuilder: DetailRebuilder,
) -> None:
    """Add a ``🔬 Pro stats`` button to a tower-detail view when it has combat
    stats. ``detail_rebuilder`` rebuilds the detail for the Pro view's back.
    """
    stats = btd6_stats_service.get_tower_stats(tower_id)
    if stats is None or not stats.has_combat_stats:
        return
    detail_view.add_item(_ProStatsButton(stats, detail_rebuilder))


__all__ = ["TowerStatsView", "attach_pro_stats_button"]
