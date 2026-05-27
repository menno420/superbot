"""Leaderboard browser — race / boss drill-down.

Three-step flow:

1. :class:`LeaderboardBrowserView` — pick race or boss.
2. :class:`LeaderboardKindListView` — pick a specific event.
3. :class:`LeaderboardDetailView` — top-N rows.

Detail back returns to the per-kind list (NOT directly to the kind
picker) so the user can compare neighbouring events without
re-selecting the kind.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from services.btd6_view_model_service import (
    LeaderboardDetailViewModel,
    LeaderboardListViewModel,
    build_leaderboard_detail_view_model,
    build_leaderboard_list_view_model,
)
from utils.btd6.freshness_render import BUCKET_BADGE, render_freshness_warning
from views.base import HubView
from views.navigation import attach_back_button

logger = logging.getLogger("bot.views.btd6.leaderboard_browser")


# ---------------------------------------------------------------------------
# Embeds
# ---------------------------------------------------------------------------


def build_kind_picker_embed() -> discord.Embed:
    return discord.Embed(
        title="🐵 BTD6 — Leaderboards",
        description=(
            "Pick **race** or **boss** to browse stored leaderboards. "
            "Boss leaderboards show standard solo only."
        ),
        color=discord.Color.gold(),
    )


def build_event_list_embed(vm: LeaderboardListViewModel) -> discord.Embed:
    embed = discord.Embed(
        title=f"🐵 BTD6 — {vm.event_kind.title()} leaderboards",
        description=(
            f"Showing {len(vm.items)} of {vm.total_count} events. Pick one "
            "to view top-10 rows."
        ),
        color=discord.Color.gold(),
    )
    warning = render_freshness_warning(vm.freshness.state)
    if warning:
        embed.add_field(name="⚠️ Data freshness", value=warning, inline=False)
    for item in vm.items[:10]:
        embed.add_field(
            name=item.event_name[:256],
            value=f"id=`{item.event_id}` · {item.window.human}",
            inline=False,
        )
    return embed


def build_leaderboard_detail_embed(vm: LeaderboardDetailViewModel) -> discord.Embed:
    label = vm.event_name or vm.event_id
    embed = discord.Embed(
        title=f"🐵 BTD6 — {vm.event_kind.title()} leaderboard — {label}",
        color=discord.Color.gold(),
    )
    if not vm.rows:
        embed.description = (
            f"No leaderboard rows stored for `{vm.event_id}` yet. "
            f"Try `!btd6 refresh-source {vm.freshness.source_key}`."
        )
    else:
        lines: list[str] = []
        for row in vm.rows:
            if row.score is not None:
                score_render = f"score=`{row.score}`"
            elif row.score_parts:
                score_render = "score=" + "/".join(str(p) for p in row.score_parts)
            else:
                score_render = ""
            lines.append(
                f"#{row.rank} **{row.display_name or '—'}** · {score_render}".rstrip(
                    " ·",
                ),
            )
        embed.description = "\n".join(lines)

    parts: list[str] = []
    if vm.footer_hint:
        parts.append(vm.footer_hint)
    if vm.freshness.state in ("aging", "stale"):
        parts.append(f"Data: {BUCKET_BADGE[vm.freshness.state]}")
    warning = render_freshness_warning(vm.freshness.state)
    if warning:
        embed.add_field(name="⚠️ Data freshness", value=warning, inline=False)
    if parts:
        embed.set_footer(text=" · ".join(parts))
    return embed


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


class _KindSelect(discord.ui.Select):
    """Step 1: pick race or boss."""

    def __init__(self) -> None:
        options = [
            discord.SelectOption(label="🏁 Race", value="race"),
            discord.SelectOption(label="👑 Boss", value="boss"),
        ]
        super().__init__(
            placeholder="Pick a leaderboard kind…",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        kind = self.values[0]
        if not await safe_defer(interaction, ephemeral=True):
            return
        vm = await build_leaderboard_list_view_model(kind)
        view = LeaderboardKindListView(interaction.user)
        view.set_vm(kind, vm)
        await safe_edit(interaction, embed=build_event_list_embed(vm), view=view)


class _EventSelect(discord.ui.Select):
    """Step 2: pick a specific race/boss event."""

    def __init__(self, vm: LeaderboardListViewModel) -> None:
        options = [
            discord.SelectOption(
                label=item.event_name[:100],
                value=item.event_id,
                description=f"{item.window.state} · {item.window.human}"[:100],
            )
            for item in vm.items
        ]
        if not options:
            options = [
                discord.SelectOption(label="(no events)", value="__none__"),
            ]
        super().__init__(
            placeholder=f"Pick a {vm.event_kind} to view leaderboard…",
            min_values=1,
            max_values=1,
            options=options[:25],
            row=1,
        )
        self._kind = vm.event_kind

    async def callback(self, interaction: discord.Interaction) -> None:
        choice = self.values[0]
        if choice == "__none__":
            await safe_defer(interaction, ephemeral=True)
            return
        if not await safe_defer(interaction, ephemeral=True):
            return
        kind = self._kind
        detail_vm = await build_leaderboard_detail_view_model(kind, choice)

        async def _rebuild_list(
            _i: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            list_vm = await build_leaderboard_list_view_model(kind)
            parent = LeaderboardKindListView(interaction.user)
            parent.set_vm(kind, list_vm)
            return build_event_list_embed(list_vm), parent

        detail_view = LeaderboardDetailView(interaction.user)
        detail_view.set_vm(detail_vm)
        attach_back_button(
            detail_view,
            label="↩ Back to list",
            custom_id=f"btd6_lb_detail:back:{kind}:{choice}",
            parent_builder=_rebuild_list,
        )
        await safe_edit(
            interaction,
            embed=build_leaderboard_detail_embed(detail_vm),
            view=detail_view,
        )


class LeaderboardBrowserView(HubView):
    """Step 1 view: pick race or boss."""

    def __init__(self, author: discord.User | discord.Member) -> None:
        super().__init__(author)
        self.add_item(_KindSelect())


class LeaderboardKindListView(HubView):
    """Step 2 view: pick a specific race/boss event."""

    def __init__(self, author: discord.User | discord.Member) -> None:
        super().__init__(author)
        self._kind: str | None = None
        self._vm: LeaderboardListViewModel | None = None
        self.add_item(_KindSelect())

    def set_vm(self, kind: str, vm: LeaderboardListViewModel) -> None:
        for child in list(self.children):
            self.remove_item(child)
        self.add_item(_KindSelect())
        self._kind = kind
        self._vm = vm
        self.add_item(_EventSelect(vm))


class LeaderboardDetailView(HubView):
    """Step 3 view: top-N rows of one leaderboard."""

    def __init__(self, author: discord.User | discord.Member) -> None:
        super().__init__(author)
        self._vm: LeaderboardDetailViewModel | None = None

    def set_vm(self, vm: LeaderboardDetailViewModel) -> None:
        self._vm = vm


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------


async def open_leaderboard_browser(interaction: discord.Interaction) -> None:
    if not await safe_defer(interaction, ephemeral=True):
        return
    view = LeaderboardBrowserView(interaction.user)
    await safe_followup(
        interaction,
        embed=build_kind_picker_embed(),
        view=view,
        ephemeral=True,
    )


__all__ = [
    "LeaderboardBrowserView",
    "LeaderboardDetailView",
    "LeaderboardKindListView",
    "build_event_list_embed",
    "build_kind_picker_embed",
    "build_leaderboard_detail_embed",
    "open_leaderboard_browser",
]
