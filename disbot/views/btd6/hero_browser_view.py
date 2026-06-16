"""Hero browser — ephemeral drill-down opened from the BTD6 hub.

Mirrors :mod:`views.btd6.tower_browser_view` for heroes. Both list +
detail views extend :class:`HubView`.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from services.btd6_view_model_service import (
    HeroDetailViewModel,
    HeroListViewModel,
    build_hero_detail_view_model,
    build_hero_list_view_model,
)
from utils.btd6.response_embed import response_to_embed
from views.base import HubView
from views.navigation import attach_back_button

logger = logging.getLogger("bot.views.btd6.hero_browser")


# ---------------------------------------------------------------------------
# Embeds
# ---------------------------------------------------------------------------


def build_hero_list_embed(vm: HeroListViewModel) -> discord.Embed:
    page_info = f"Page {vm.page + 1}/{vm.total_pages}"
    embed = discord.Embed(
        title="🐵 BTD6 — Heroes",
        description=(
            f"Showing {len(vm.items)} of {vm.total_count} heroes "
            f"({page_info}). Select one for details."
        ),
        color=discord.Color.green(),
    )
    for item in vm.items:
        embed.add_field(
            name=item.canonical,
            value=f"Cost: {item.base_cost}",
            inline=True,
        )
    return embed


def build_hero_detail_embed(vm: HeroDetailViewModel) -> discord.Embed:
    from services import btd6_ai_service, btd6_stats_service
    from services.btd6_resolver_service import resolve
    from services.btd6_response_builder import for_hero
    from utils.btd6.stats_embed import format_normal_stats

    intent = resolve(vm.hero_id)
    if not intent.heroes:
        embed = response_to_embed(btd6_ai_service.deterministic_answer(intent))
    else:
        hero = intent.heroes[0]
        # Live event restrictions live in their own drill-down, not on the
        # overview — keep it uncluttered (mirrors the tower-browser detail).
        embed = response_to_embed(for_hero(hero, restrictions=()))

    # Heroes with a bloonswiki module get a glanceable Level-1 stats field
    # (the rest are prose-only — cost + abilities, no combat stats).
    stats = btd6_stats_service.get_hero_stats(vm.hero_id)
    if stats is not None and stats.has_combat_stats:
        base = stats.level("1")
        if base is not None:
            embed.add_field(
                name="📊 Level 1 stats",
                value=format_normal_stats(btd6_stats_service.normal_stats(base)),
                inline=False,
            )
    return embed


# ---------------------------------------------------------------------------
# Select
# ---------------------------------------------------------------------------


class _HeroSelect(discord.ui.Select):
    def __init__(self, vm: HeroListViewModel) -> None:
        options = [
            discord.SelectOption(
                label=item.canonical[:100],
                value=item.hero_id,
                description=f"Cost: {item.base_cost}"[:100],
            )
            for item in vm.items
        ]
        if not options:
            options = [
                discord.SelectOption(
                    label="(no heroes available)",
                    value="__none__",
                ),
            ]
        super().__init__(
            placeholder="Pick a hero to view…",
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
        detail_vm = await build_hero_detail_view_model(choice)
        if detail_vm is None:
            embed = discord.Embed(
                title="🐵 BTD6 — Hero",
                description=f"No fact found for hero `{choice}`.",
                color=discord.Color.red(),
            )
            await safe_edit(interaction, embed=embed, view=None)
            return

        _page = self._vm.page

        async def _rebuild_list(
            _i: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            list_vm = await build_hero_list_view_model(page=_page)
            parent = HeroBrowserView(interaction.user)
            parent.set_vm(list_vm)
            return build_hero_list_embed(list_vm), parent

        from views.btd6.hero_stats_view import attach_hero_pro_stats_button

        def _build_detail_view() -> HeroDetailView:
            view = HeroDetailView(interaction.user)
            view.set_vm(detail_vm)
            attach_back_button(
                view,
                label="↩ Back",
                custom_id=f"btd6_hero_detail:back:{detail_vm.hero_id}",
                parent_builder=_rebuild_list,
            )
            # Only present for heroes with a per-level stats module.
            attach_hero_pro_stats_button(view, detail_vm.hero_id, _rebuild_detail)
            return view

        async def _rebuild_detail(
            _i: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            return build_hero_detail_embed(detail_vm), _build_detail_view()

        await safe_edit(
            interaction,
            embed=build_hero_detail_embed(detail_vm),
            view=_build_detail_view(),
        )


# ---------------------------------------------------------------------------
# Navigation button
# ---------------------------------------------------------------------------


class _HeroNavButton(discord.ui.Button):
    """Previous / next page button for the hero browser."""

    def __init__(self, label: str, target_page: int, *, disabled: bool = False) -> None:
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
            row=1,
        )
        self._target_page = target_page

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        vm = await build_hero_list_view_model(page=self._target_page)
        view = HeroBrowserView(interaction.user)
        view.set_vm(vm)
        await safe_edit(interaction, embed=build_hero_list_embed(vm), view=view)


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


class HeroBrowserView(HubView):
    def __init__(self, author: discord.User | discord.Member) -> None:
        super().__init__(author)
        self._vm: HeroListViewModel | None = None

    def set_vm(self, vm: HeroListViewModel) -> None:
        for child in list(self.children):
            self.remove_item(child)
        self._vm = vm
        self.add_item(_HeroSelect(vm))

        prev_disabled = vm.page <= 0
        next_disabled = vm.page >= vm.total_pages - 1
        self.add_item(_HeroNavButton("◀ Prev", vm.page - 1, disabled=prev_disabled))
        self.add_item(_HeroNavButton("Next ▶", vm.page + 1, disabled=next_disabled))


class HeroDetailView(HubView):
    def __init__(self, author: discord.User | discord.Member) -> None:
        super().__init__(author)
        self._vm: HeroDetailViewModel | None = None

    def set_vm(self, vm: HeroDetailViewModel) -> None:
        self._vm = vm


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------


async def open_hero_browser(interaction: discord.Interaction) -> None:
    if not await safe_defer(interaction, ephemeral=True):
        return
    vm = await build_hero_list_view_model()
    view = HeroBrowserView(interaction.user)
    view.set_vm(vm)
    await safe_followup(
        interaction,
        embed=build_hero_list_embed(vm),
        view=view,
        ephemeral=True,
    )


__all__ = [
    "HeroBrowserView",
    "HeroDetailView",
    "build_hero_detail_embed",
    "build_hero_list_embed",
    "open_hero_browser",
]
