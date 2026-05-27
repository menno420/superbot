"""Tower browser — ephemeral drill-down opened from the BTD6 hub.

Lives in ``views/btd6/`` so the cog file stays small. Both
:class:`TowerBrowserView` (list) and :class:`TowerDetailView` (single
tower) extend :class:`HubView` so they share the standard
180-second timeout, invoker-only ``interaction_check``, and
``handle_view_error`` behaviour.

The list view is the ephemeral the panel button opens; the detail
view is reached via the Select. Detail's "Back" rebuilds the list
through :func:`views.navigation.attach_back_button`.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from services.btd6_view_model_service import (
    TowerDetailViewModel,
    TowerListViewModel,
    build_tower_detail_view_model,
    build_tower_list_view_model,
)
from utils.btd6.response_embed import response_to_embed
from views.base import HubView
from views.navigation import attach_back_button

logger = logging.getLogger("bot.views.btd6.tower_browser")


# ---------------------------------------------------------------------------
# Embeds
# ---------------------------------------------------------------------------


def build_tower_list_embed(vm: TowerListViewModel) -> discord.Embed:
    embed = discord.Embed(
        title="🐵 BTD6 — Towers",
        description=(
            f"Showing {len(vm.items)} of {vm.total_count} towers. Pick "
            "one to view the deterministic fact sheet + any active-event "
            "restrictions."
        ),
        color=discord.Color.green(),
    )
    if len(vm.items) < vm.total_count:
        embed.add_field(
            name="ℹ️ Pagination",
            value=(
                "Discord caps selects at 25 options; refine via "
                "`/btd6 tower <name>` for off-list towers."
            ),
            inline=False,
        )
    for item in vm.items[:10]:
        embed.add_field(
            name=item.canonical,
            value=f"Cost: {item.base_cost} • {item.category}",
            inline=True,
        )
    return embed


def build_tower_detail_embed(vm: TowerDetailViewModel) -> discord.Embed:
    """Render a tower detail.

    Uses ``btd6_response_builder.for_tower`` via the existing
    ``response_to_embed`` helper to keep the on-screen format identical
    to ``!btd6 tower <name>``.
    """
    from services import btd6_ai_service
    from services.btd6_resolver_service import resolve
    from services.btd6_response_builder import for_tower

    if vm.fact is None:
        return response_to_embed(
            btd6_ai_service.deterministic_answer(resolve(vm.tower_id)),
        )
    return response_to_embed(for_tower(vm.fact, restrictions=tuple(vm.restrictions)))


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


class _TowerSelect(discord.ui.Select):
    """The list select that opens TowerDetailView for the chosen tower."""

    def __init__(self, vm: TowerListViewModel) -> None:
        options = [
            discord.SelectOption(
                label=item.canonical[:100],
                value=item.tower_id,
                description=f"Cost: {item.base_cost} • {item.category}"[:100],
            )
            for item in vm.items
        ]
        if not options:
            # Discord requires at least one option; render a disabled placeholder.
            options = [
                discord.SelectOption(
                    label="(no towers available)",
                    value="__none__",
                ),
            ]
        super().__init__(
            placeholder="Pick a tower to view…",
            min_values=1,
            max_values=1,
            options=options[:25],
            row=0,
        )
        self._vm = vm

    async def callback(self, interaction: discord.Interaction) -> None:
        choice = self.values[0]
        if choice == "__none__":
            await safe_defer(interaction, ephemeral=True)
            return
        if not await safe_defer(interaction, ephemeral=True):
            return
        detail_vm = await build_tower_detail_view_model(choice)
        if detail_vm is None:
            embed = discord.Embed(
                title="🐵 BTD6 — Tower",
                description=f"No fact found for tower `{choice}`.",
                color=discord.Color.red(),
            )
            await safe_edit(interaction, embed=embed, view=None)
            return

        # Rebuild the list as the detail's parent so the Back button works.
        async def _rebuild_list(
            _i: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            list_vm = await build_tower_list_view_model()
            parent = TowerBrowserView(interaction.user)
            parent.set_vm(list_vm)
            return build_tower_list_embed(list_vm), parent

        detail_view = TowerDetailView(interaction.user)
        detail_view.set_vm(detail_vm)
        attach_back_button(
            detail_view,
            label="↩ Back",
            custom_id=f"btd6_tower_detail:back:{detail_vm.tower_id}",
            parent_builder=_rebuild_list,
        )
        await safe_edit(
            interaction,
            embed=build_tower_detail_embed(detail_vm),
            view=detail_view,
        )


class TowerBrowserView(HubView):
    """Ephemeral list of towers — opened from the BTD6 hub."""

    def __init__(self, author: discord.User | discord.Member) -> None:
        super().__init__(author)
        self._vm: TowerListViewModel | None = None

    def set_vm(self, vm: TowerListViewModel) -> None:
        # Reset items then re-add the select for the supplied VM.
        # Called after construction so the async builder doesn't block __init__.
        for child in list(self.children):
            self.remove_item(child)
        self._vm = vm
        self.add_item(_TowerSelect(vm))


class TowerDetailView(HubView):
    """Detail view for one tower. Reached from :class:`TowerBrowserView`."""

    def __init__(self, author: discord.User | discord.Member) -> None:
        super().__init__(author)
        self._vm: TowerDetailViewModel | None = None

    def set_vm(self, vm: TowerDetailViewModel) -> None:
        self._vm = vm


# ---------------------------------------------------------------------------
# Public entrypoint — called by the panel's Towers button
# ---------------------------------------------------------------------------


async def open_tower_browser(interaction: discord.Interaction) -> None:
    """Open the tower browser as an ephemeral followup."""
    if not await safe_defer(interaction, ephemeral=True):
        return
    vm = await build_tower_list_view_model()
    view = TowerBrowserView(interaction.user)
    view.set_vm(vm)
    embed = build_tower_list_embed(vm)
    # Freshness is N/A for the static tower catalog — no warning to render.
    await safe_followup(interaction, embed=embed, view=view, ephemeral=True)


__all__ = [
    "TowerBrowserView",
    "TowerDetailView",
    "build_tower_detail_embed",
    "build_tower_list_embed",
    "open_tower_browser",
]
