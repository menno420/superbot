"""Paragon stats drill-down — a degree picker (1..100) over a paragon's full
combat stats.

The paragon analogue of :mod:`views.btd6.tower_stats_view` /
:mod:`views.btd6.hero_stats_view`. Opens on the degree-independent base stats
(the infobox), then a degree Select (milestones) + an "Enter degree" modal swap
in any degree's scaled stats. Reached from two places:

* the **📊 Stats** button on the Paragon Calculator (:mod:`views.btd6.paragon_view`);
* the **👑 Paragon stats** button on a tower detail
  (:func:`attach_paragon_stats_button`), shown only when the tower's paragon has
  a stats module.

Extends :class:`HubView` for the shared timeout / invoker-only / error handling.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import btd6_stats_service
from utils.btd6.stats_embed import (
    build_paragon_base_embed,
    build_paragon_degree_embed,
    paragon_degree_label,
)
from views.base import HubView
from views.navigation import attach_back_button

DetailRebuilder = Callable[
    [discord.Interaction],
    Awaitable[tuple[discord.Embed, discord.ui.View]],
]

# Degrees offered in the Select (Discord caps options at 25). The "Enter degree"
# modal covers any 1..100 in between.
_DEGREE_MILESTONES: tuple[int, ...] = (1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)


class _DegreeSelect(discord.ui.Select):
    """Pick a milestone degree; swaps the embed to that degree's scaled stats."""

    def __init__(self, stats: btd6_stats_service.ParagonStats) -> None:
        options = [
            discord.SelectOption(label=paragon_degree_label(d), value=str(d))
            for d in _DEGREE_MILESTONES
        ]
        super().__init__(
            placeholder="Pick a degree…",
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
            embed=build_paragon_degree_embed(self._stats, int(self.values[0])),
            view=self.view,
        )


class _BaseStatsButton(discord.ui.Button):
    """Swap back to the degree-independent base (infobox) stats."""

    def __init__(self, stats: btd6_stats_service.ParagonStats) -> None:
        super().__init__(
            label="📊 Base stats",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        self._stats = stats

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        await safe_edit(
            interaction,
            embed=build_paragon_base_embed(self._stats),
            view=self.view,
        )


class _DegreeModal(discord.ui.Modal, title="Paragon degree (1–100)"):
    """Enter any degree; shows that degree's scaled stats."""

    degree: discord.ui.TextInput = discord.ui.TextInput(
        label="Degree",
        placeholder="1–100",
        max_length=3,
        required=True,
    )

    def __init__(
        self,
        view: ParagonStatsView,
        stats: btd6_stats_service.ParagonStats,
    ) -> None:
        super().__init__()
        self._view = view
        self._stats = stats

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        raw = str(self.degree.value).strip()
        try:
            degree = int(raw)
        except ValueError:
            degree = 1
        # degree_row clamps to 1..100, so out-of-range input is handled safely.
        await safe_edit(
            interaction,
            embed=build_paragon_degree_embed(self._stats, degree),
            view=self._view,
        )


class _EnterDegreeButton(discord.ui.Button):
    def __init__(
        self,
        view: ParagonStatsView,
        stats: btd6_stats_service.ParagonStats,
    ) -> None:
        super().__init__(
            label="🔢 Enter degree",
            style=discord.ButtonStyle.primary,
            row=1,
        )
        self._view = view
        self._stats = stats

    async def callback(self, interaction: discord.Interaction) -> None:
        # send_modal must be the initial response — no safe_defer here.
        await interaction.response.send_modal(_DegreeModal(self._view, self._stats))


class ParagonStatsView(HubView):
    """Degree picker + base-stats toggle for one paragon's combat stats."""

    def __init__(
        self,
        author: discord.User | discord.Member,
        stats: btd6_stats_service.ParagonStats,
    ) -> None:
        super().__init__(author)
        self._stats = stats
        self.add_item(_DegreeSelect(stats))
        self.add_item(_BaseStatsButton(stats))
        self.add_item(_EnterDegreeButton(self, stats))


async def open_paragon_stats(
    interaction: discord.Interaction,
    stats: btd6_stats_service.ParagonStats,
    *,
    back_label: str,
    back_custom_id: str,
    back_builder: DetailRebuilder,
) -> None:
    """Swap the current ephemeral to the paragon stats view (base embed first).

    Caller must have already deferred. ``back_builder`` rebuilds the surface the
    paragon stats view returns to (the calculator or the tower detail).
    """
    view = ParagonStatsView(interaction.user, stats)
    attach_back_button(
        view,
        label=back_label,
        custom_id=back_custom_id,
        parent_builder=back_builder,
    )
    await safe_edit(
        interaction,
        embed=build_paragon_base_embed(stats),
        view=view,
    )


class _TowerParagonStatsButton(discord.ui.Button):
    """Opens :class:`ParagonStatsView`; its back button rebuilds the tower detail."""

    def __init__(
        self,
        stats: btd6_stats_service.ParagonStats,
        detail_rebuilder: DetailRebuilder,
    ) -> None:
        super().__init__(
            label="👑 Paragon stats",
            style=discord.ButtonStyle.primary,
            row=2,
        )
        self._stats = stats
        self._detail_rebuilder = detail_rebuilder

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        await open_paragon_stats(
            interaction,
            self._stats,
            back_label="↩ Back to tower",
            back_custom_id=f"btd6_paragon_stats:back:{self._stats.tower_id}",
            back_builder=self._detail_rebuilder,
        )


def attach_paragon_stats_button(
    detail_view: discord.ui.View,
    tower_id: str,
    detail_rebuilder: DetailRebuilder,
) -> None:
    """Add a ``👑 Paragon stats`` button to a tower-detail view when the tower's
    paragon has a stats module. ``detail_rebuilder`` rebuilds the detail for the
    paragon view's back button.
    """
    stats = btd6_stats_service.get_paragon_stats_by_tower(tower_id)
    if stats is None or not stats.has_combat_stats:
        return
    detail_view.add_item(_TowerParagonStatsButton(stats, detail_rebuilder))


__all__ = [
    "ParagonStatsView",
    "attach_paragon_stats_button",
    "open_paragon_stats",
]
