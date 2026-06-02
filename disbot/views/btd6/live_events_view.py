"""Live Events browser — race / boss / CT / odyssey / event drill-down.

Opened from the BTD6 hub. Two selects:

1. Event kind (race / boss / ct / odyssey / event) — drives the list.
2. Event id — opens the detail view.

Detail view's "Back" rebuilds the list with the kind preserved via
the closure captured by :func:`views.navigation.attach_back_button`.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from services.btd6_view_model_service import (
    EventDetailViewModel,
    EventListViewModel,
    build_event_detail_view_model,
    build_event_list_view_model,
)
from utils.btd6.freshness_render import render_freshness_warning
from views.base import HubView
from views.navigation import attach_back_button

logger = logging.getLogger("bot.views.btd6.live_events")


_KIND_LABELS: tuple[tuple[str, str, str], ...] = (
    ("race", "🏁 Race", "Active + recent race events"),
    ("boss", "👑 Boss", "Active + recent boss events"),
    ("ct", "🗺️ CT", "Contested Territory events"),
    ("odyssey", "🌊 Odyssey", "Active + recent odysseys"),
    ("event", "🎪 Event", "Other live events"),
)


# ---------------------------------------------------------------------------
# Embeds
# ---------------------------------------------------------------------------


def build_kind_picker_embed() -> discord.Embed:
    """First-step embed: pick an event kind."""
    return discord.Embed(
        title="🐵 BTD6 — Live Events",
        description=(
            "Pick a category to browse the most-recent events. Use "
            "**↩ Close** to dismiss the panel."
        ),
        color=discord.Color.gold(),
    )


def build_event_list_embed(vm: EventListViewModel) -> discord.Embed:
    embed = discord.Embed(
        title=f"🐵 BTD6 — Live {vm.kind.title()} events",
        description=(
            f"Showing {len(vm.items)} of {vm.total_count}. Pick an event "
            "to view detail / restrictions."
        ),
        color=discord.Color.gold(),
    )
    warning = render_freshness_warning(vm.freshness.state)
    if warning:
        embed.add_field(name="⚠️ Data freshness", value=warning, inline=False)
    if not vm.items:
        embed.add_field(
            name="No events",
            value=(
                f"No active or recent `{vm.kind}` events stored yet. "
                f"Try `!btd6 refresh-source {vm.freshness.source_key}`."
            ),
            inline=False,
        )
    for item in vm.items[:10]:
        embed.add_field(
            name=item.name[:256],
            value=f"id=`{item.entity_key}` · {item.window.human}",
            inline=False,
        )
    return embed


def build_event_detail_embed_from_vm(vm: EventDetailViewModel) -> discord.Embed:
    """Render detail page for one event.

    Reuses the existing ``build_event_detail_embed`` for byte-identical
    layout. The VM holds the rows the legacy builder reads from, so we
    construct row dicts and forward them.
    """
    from cogs.btd6._builders import build_event_detail_embed

    primary_row: dict | None = None
    metadata_row: dict | None = None
    if vm.primary_body:
        primary_row = {
            "entity_kind": vm.entity_kind,
            "entity_key": vm.entity_key,
            "body_json": vm.primary_body,
            "fetched_at": vm.fetched_at,
        }
    if vm.metadata_body:
        metadata_row = {
            "entity_kind": vm.entity_kind,
            "entity_key": vm.entity_key,
            "body_json": vm.metadata_body,
            "fetched_at": vm.fetched_at,
        }
    embed = build_event_detail_embed(
        vm.entity_kind,
        vm.entity_key,
        primary_row,
        metadata_row=metadata_row,
    )
    warning = render_freshness_warning(vm.freshness.state)
    if warning:
        embed.add_field(name="⚠️ Data freshness", value=warning, inline=False)
    return embed


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


class _KindSelect(discord.ui.Select):
    """Picks the event kind; opens the per-kind list view."""

    def __init__(self) -> None:
        options = [
            discord.SelectOption(label=label, value=value, description=desc[:100])
            for value, label, desc in _KIND_LABELS
        ]
        super().__init__(
            placeholder="Pick an event kind…",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        kind = self.values[0]
        if not await safe_defer(interaction, ephemeral=True):
            return
        vm = await build_event_list_view_model(kind)
        view = LiveEventsBrowserView(interaction.user)
        view.set_kind(kind, vm)
        await safe_edit(interaction, embed=build_event_list_embed(vm), view=view)


class _EventSelect(discord.ui.Select):
    """Picks one specific event; opens the detail view."""

    def __init__(self, vm: EventListViewModel) -> None:
        options = [
            discord.SelectOption(
                label=item.name[:100],
                value=item.entity_key,
                description=(f"{item.window.state} · {item.window.human}")[:100],
            )
            for item in vm.items
        ]
        empty = not options
        if empty:
            # Disable rather than offer a dead "(no events)" option that
            # silently defers on click — that silent defer is what made the
            # control look broken ("the race button does nothing"). The list
            # embed already explains the empty state; a greyed-out select
            # reinforces "nothing to pick" instead of "broken".
            options = [
                discord.SelectOption(label="(no events)", value="__none__"),
            ]
        super().__init__(
            placeholder=(
                "No events to show — check back when one is live"
                if empty
                else "Pick an event to view…"
            ),
            min_values=1,
            max_values=1,
            options=options[:25],
            row=1,
            disabled=empty,
        )
        self._kind = vm.kind

    async def callback(self, interaction: discord.Interaction) -> None:
        choice = self.values[0]
        kind = self._kind
        if choice == "__none__":
            # Defensive: the select is disabled when empty, but if a stale
            # component fires, answer explicitly rather than silently defer.
            if not await safe_defer(interaction, ephemeral=True):
                return
            await safe_edit(
                interaction,
                embed=discord.Embed(
                    title=f"🐵 BTD6 — Live {kind.title()} events",
                    description=(
                        f"No active or recent `{kind}` events are stored right "
                        "now. Check back when one is live."
                    ),
                    color=discord.Color.gold(),
                ),
                view=None,
            )
            return
        if not await safe_defer(interaction, ephemeral=True):
            return
        detail_vm = await build_event_detail_view_model(kind, choice)
        if detail_vm is None:
            embed = discord.Embed(
                title="🐵 BTD6 — Event",
                description=f"No fact stored for `{kind}` event `{choice}`.",
                color=discord.Color.red(),
            )
            await safe_edit(interaction, embed=embed, view=None)
            return

        async def _rebuild_list(
            _i: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            list_vm = await build_event_list_view_model(kind)
            parent = LiveEventsBrowserView(interaction.user)
            parent.set_kind(kind, list_vm)
            return build_event_list_embed(list_vm), parent

        detail_view = EventDetailView(interaction.user)
        detail_view.set_vm(detail_vm)
        attach_back_button(
            detail_view,
            label="↩ Back to list",
            custom_id=f"btd6_event_detail:back:{kind}:{detail_vm.entity_key}",
            parent_builder=_rebuild_list,
        )
        await safe_edit(
            interaction,
            embed=build_event_detail_embed_from_vm(detail_vm),
            view=detail_view,
        )


class LiveEventsBrowserView(HubView):
    """List of events for a given kind. Top-level of the drill-down."""

    def __init__(self, author: discord.User | discord.Member) -> None:
        super().__init__(author)
        self._kind: str | None = None
        self._vm: EventListViewModel | None = None
        self.add_item(_KindSelect())

    def set_kind(self, kind: str, vm: EventListViewModel) -> None:
        """Populate the event select for the given kind."""
        for child in list(self.children):
            self.remove_item(child)
        self.add_item(_KindSelect())
        self._kind = kind
        self._vm = vm
        self.add_item(_EventSelect(vm))


class EventDetailView(HubView):
    """One specific event. Reached from :class:`LiveEventsBrowserView`."""

    def __init__(self, author: discord.User | discord.Member) -> None:
        super().__init__(author)
        self._vm: EventDetailViewModel | None = None

    def set_vm(self, vm: EventDetailViewModel) -> None:
        self._vm = vm


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------


async def open_live_events_browser(interaction: discord.Interaction) -> None:
    """Open the live-events browser as an ephemeral followup."""
    if not await safe_defer(interaction, ephemeral=True):
        return
    view = LiveEventsBrowserView(interaction.user)
    await safe_followup(
        interaction,
        embed=build_kind_picker_embed(),
        view=view,
        ephemeral=True,
    )


__all__ = [
    "EventDetailView",
    "LiveEventsBrowserView",
    "build_event_detail_embed_from_vm",
    "build_event_list_embed",
    "build_kind_picker_embed",
    "open_live_events_browser",
]
