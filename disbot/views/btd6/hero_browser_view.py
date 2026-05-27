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
    embed = discord.Embed(
        title="🐵 BTD6 — Heroes",
        description=(
            f"Showing {len(vm.items)} of {vm.total_count} heroes. Pick "
            "one to view the seed sheet + any active-event restrictions."
        ),
        color=discord.Color.green(),
    )
    if len(vm.items) < vm.total_count:
        embed.add_field(
            name="ℹ️ Pagination",
            value=(
                "Discord caps selects at 25 options; refine via "
                "`/btd6 hero <name>` for off-list heroes."
            ),
            inline=False,
        )
    for item in vm.items[:10]:
        embed.add_field(
            name=item.canonical,
            value=f"Cost: {item.base_cost} • {item.description[:80]}",
            inline=False,
        )
    return embed


def build_hero_detail_embed(vm: HeroDetailViewModel) -> discord.Embed:
    from services import btd6_ai_service
    from services.btd6_resolver_service import resolve
    from services.btd6_response_builder import for_hero

    intent = resolve(vm.hero_id)
    if not intent.heroes:
        return response_to_embed(btd6_ai_service.deterministic_answer(intent))
    hero = intent.heroes[0]
    return response_to_embed(for_hero(hero, restrictions=tuple(vm.restrictions)))


# ---------------------------------------------------------------------------
# Views
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

        async def _rebuild_list(
            _i: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            list_vm = await build_hero_list_view_model()
            parent = HeroBrowserView(interaction.user)
            parent.set_vm(list_vm)
            return build_hero_list_embed(list_vm), parent

        detail_view = HeroDetailView(interaction.user)
        detail_view.set_vm(detail_vm)
        attach_back_button(
            detail_view,
            label="↩ Back",
            custom_id=f"btd6_hero_detail:back:{detail_vm.hero_id}",
            parent_builder=_rebuild_list,
        )
        await safe_edit(
            interaction, embed=build_hero_detail_embed(detail_vm), view=detail_view,
        )


class HeroBrowserView(HubView):
    def __init__(self, author: discord.User | discord.Member) -> None:
        super().__init__(author)
        self._vm: HeroListViewModel | None = None

    def set_vm(self, vm: HeroListViewModel) -> None:
        for child in list(self.children):
            self.remove_item(child)
        self._vm = vm
        self.add_item(_HeroSelect(vm))


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
        interaction, embed=build_hero_list_embed(vm), view=view, ephemeral=True,
    )


__all__ = [
    "HeroBrowserView",
    "HeroDetailView",
    "build_hero_detail_embed",
    "build_hero_list_embed",
    "open_hero_browser",
]
