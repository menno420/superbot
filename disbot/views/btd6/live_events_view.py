"""Live Events browser — current-event-first.

Opened from the BTD6 hub's **Live Events** button. The landing is a
*live overview* (:class:`LiveOverviewView`): it shows what race / boss /
CT / odyssey / event is running **right now**, one line per kind, and a
select containing **only the currently-live events**. Picking one opens a
rich :class:`EventDetailView` with all the data stored about it (window,
rules, tower/hero restrictions, scores, coverage).

History is a deliberate second step: the **📜 Past events** button opens
:class:`LiveEventsBrowserView` — the by-kind list of recent (incl. ended)
events — which drills into the same detail view. A ``↩ Live now`` button
returns to the overview so nobody is stranded in history.

This replaces the previous flow, which dumped *every* stored fact (mostly
``ended``) into both the embed and a dropdown and never surfaced the
current event. It also fixes the drill-down crashing on every click — the
detail view-model used to call ``search_facts`` with an unsupported
``entity_key`` kwarg, so the ephemeral silently never updated ("the race
event button does nothing").
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from services.btd6_view_model_service import (
    EventDetailViewModel,
    EventListViewModel,
    LiveOverviewViewModel,
    build_event_detail_view_model,
    build_event_list_view_model,
    build_live_overview_view_model,
)
from utils.btd6.context_footer import append_context_footer
from utils.btd6.freshness_render import BUCKET_EMOJI, render_freshness_warning
from views.base import HubView
from views.navigation import attach_back_button

logger = logging.getLogger("bot.views.btd6.live_events")


_KIND_LABELS: tuple[tuple[str, str, str], ...] = (
    ("race", "🏁 Race", "Recent + active race events"),
    ("boss", "👑 Boss", "Recent + active boss events"),
    ("ct", "🗺️ CT", "Contested Territory events"),
    ("odyssey", "🌊 Odyssey", "Recent + active odysseys"),
    ("event", "🎪 Event", "Other recent events"),
)


# ---------------------------------------------------------------------------
# Embeds
# ---------------------------------------------------------------------------


def build_live_overview_embed(vm: LiveOverviewViewModel) -> discord.Embed:
    """Landing embed: what BTD6 events are live right now, one line per kind."""
    total = vm.total_live
    if total == 0:
        embed = discord.Embed(
            title="🐵 BTD6 — Live Events",
            description=(
                "**Nothing is running right now** — no race, boss, CT, odyssey, "
                "or other event is currently live.\n\n"
                "Tap **📜 Past events** to browse recent (ended) events, or check "
                "back when one starts."
            ),
            color=discord.Color.greyple(),
        )
    else:
        plural = "s" if total != 1 else ""
        embed = discord.Embed(
            title="🐵 BTD6 — Live Events",
            description=(
                f"**{total}** event{plural} live right now. Pick one below for full "
                "details — rules, tower/hero restrictions, and timing. Tap "
                "**📜 Past events** for recent history."
            ),
            color=discord.Color.green(),
        )

    for kind in vm.kinds:
        badge = BUCKET_EMOJI.get(kind.freshness.state, "⚪")
        if kind.live:
            lines = []
            for item in kind.live:
                ends = item.window.relative.removeprefix("·").strip()
                suffix = f" — {ends}" if ends else ""
                lines.append(f"**{item.name}**{suffix}")
            value = "\n".join(lines)
        else:
            value = "_nothing live_"
        embed.add_field(
            name=f"{kind.emoji} {kind.label} {badge}",
            value=value[:1024],
            inline=False,
        )

    warning = render_freshness_warning(vm.worst_freshness)
    if warning:
        embed.add_field(name="⚠️ Data freshness", value=warning, inline=False)
    return append_context_footer(embed, vm.context.context_id)


def build_kind_picker_embed() -> discord.Embed:
    """Past-events step: pick an event kind to browse recent history."""
    return discord.Embed(
        title="🐵 BTD6 — Past events",
        description=(
            "Browse **recent events by category** — this list includes past "
            "(ended) events, newest first. For what's live *right now*, use "
            "**↩ Live now**."
        ),
        color=discord.Color.gold(),
    )


def build_event_list_embed(vm: EventListViewModel) -> discord.Embed:
    embed = discord.Embed(
        title=f"🐵 BTD6 — Recent {vm.kind.title()} events",
        description=(
            f"Showing {len(vm.items)} of {vm.total_count} (newest first, "
            "includes ended). Pick an event for full detail / restrictions."
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
                f"No `{vm.kind}` events stored yet. "
                f"Try `!btd6 refresh-source {vm.freshness.source_key}`."
            ),
            inline=False,
        )
    for item in vm.items[:10]:
        embed.add_field(
            name=item.name[:256],
            value=f"{item.window.human} · id=`{item.entity_key}`",
            inline=False,
        )
    return embed


def build_event_detail_embed_from_vm(vm: EventDetailViewModel) -> discord.Embed:
    """Render the detail page for one event.

    Reuses the existing ``build_event_detail_embed`` for layout. The VM
    holds the index + metadata bodies; we forward them as row dicts so the
    builder renders window, rules, restrictions, scores, and coverage. The
    embed colour reflects the live/ended/upcoming state so the current
    event reads at a glance.
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
    # Colour-code by window state so "live" pops and "ended" reads as past.
    _STATE_COLOR = {
        "active": discord.Color.green(),
        "upcoming": discord.Color.blurple(),
        "ended": discord.Color.greyple(),
    }
    embed.color = _STATE_COLOR.get(vm.window.state, discord.Color.gold())
    warning = render_freshness_warning(vm.freshness.state)
    if warning:
        embed.add_field(name="⚠️ Data freshness", value=warning, inline=False)
    return embed


# ---------------------------------------------------------------------------
# Detail drill-down (shared by the overview select and the history list)
# ---------------------------------------------------------------------------


async def _open_event_detail(
    interaction: discord.Interaction,
    kind: str,
    entity_key: str,
    *,
    back_label: str,
    back_custom_id: str,
    parent_builder,
) -> None:
    """Build + render the event detail in place. Caller must have deferred."""
    detail_vm = await build_event_detail_view_model(kind, entity_key)
    if detail_vm is None:
        await safe_edit(
            interaction,
            embed=discord.Embed(
                title="🐵 BTD6 — Event",
                description=(
                    f"No data is stored for the `{kind}` event `{entity_key}`. "
                    "It may have rotated out — try **📜 Past events**."
                ),
                color=discord.Color.red(),
            ),
            view=None,
        )
        return
    detail_view = EventDetailView(interaction.user)
    detail_view.set_vm(detail_vm)
    attach_back_button(
        detail_view,
        label=back_label,
        custom_id=back_custom_id,
        parent_builder=parent_builder,
    )
    await safe_edit(
        interaction,
        embed=build_event_detail_embed_from_vm(detail_vm),
        view=detail_view,
    )


# ---------------------------------------------------------------------------
# Live overview (landing)
# ---------------------------------------------------------------------------


class _LiveOverviewSelect(discord.ui.Select):
    """Select of the currently-live events across all kinds."""

    def __init__(self, vm: LiveOverviewViewModel) -> None:
        live = vm.all_live
        empty = not live
        if empty:
            options = [discord.SelectOption(label="(nothing live)", value="__none__")]
        else:
            options = [
                discord.SelectOption(
                    label=f"{item.emoji} {item.name}"[:100],
                    value=f"{item.short_kind}:{item.entity_key}"[:100],
                    description=(
                        f"{item.label} · {item.window.relative.removeprefix('·').strip()}"
                    )[:100],
                )
                for item in live[:25]
            ]
        super().__init__(
            placeholder=(
                "Nothing live right now"
                if empty
                else "Pick a live event for full details…"
            ),
            min_values=1,
            max_values=1,
            options=options,
            row=0,
            disabled=empty,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        choice = self.values[0]
        if not await safe_defer(interaction, ephemeral=True):
            return
        if choice == "__none__":
            return
        kind, _, entity_key = choice.partition(":")
        author = interaction.user

        async def _rebuild_overview(
            _i: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            vm = await build_live_overview_view_model()
            return build_live_overview_embed(vm), LiveOverviewView(author, vm)

        await _open_event_detail(
            interaction,
            kind,
            entity_key,
            back_label="↩ Back to live",
            back_custom_id=f"btd6_live_overview:back:{kind}:{entity_key}"[:100],
            parent_builder=_rebuild_overview,
        )


class _PastEventsButton(discord.ui.Button):
    """Opens the by-kind history browser (recent + ended events)."""

    def __init__(self) -> None:
        super().__init__(
            label="📜 Past events",
            style=discord.ButtonStyle.secondary,
            row=1,
            custom_id="btd6_live:past",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        view = LiveEventsBrowserView(interaction.user)
        await safe_edit(
            interaction,
            embed=build_kind_picker_embed(),
            view=view,
        )


class LiveOverviewView(HubView):
    """Landing view: the currently-live events + a route into history."""

    def __init__(
        self,
        author: discord.User | discord.Member,
        vm: LiveOverviewViewModel,
    ) -> None:
        super().__init__(author)
        self._vm = vm
        self.add_item(_LiveOverviewSelect(vm))
        self.add_item(_PastEventsButton())


# ---------------------------------------------------------------------------
# Past-events history browser (by kind)
# ---------------------------------------------------------------------------


class _KindSelect(discord.ui.Select):
    """Picks the event kind; opens the per-kind history list."""

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
    """Picks one specific (recent/past) event; opens the detail view."""

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
            # silently defers on click. The list embed already explains the
            # empty state; a greyed-out select reinforces "nothing to pick".
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
        if not await safe_defer(interaction, ephemeral=True):
            return
        if choice == "__none__":
            # Defensive: the select is disabled when empty, but answer
            # explicitly rather than silently defer if a stale component fires.
            await safe_edit(
                interaction,
                embed=discord.Embed(
                    title=f"🐵 BTD6 — Recent {kind.title()} events",
                    description=(
                        f"No `{kind}` events are stored right now. Check back "
                        "when one is live."
                    ),
                    color=discord.Color.gold(),
                ),
                view=None,
            )
            return

        author = interaction.user

        async def _rebuild_list(
            _i: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            list_vm = await build_event_list_view_model(kind)
            parent = LiveEventsBrowserView(author)
            parent.set_kind(kind, list_vm)
            return build_event_list_embed(list_vm), parent

        await _open_event_detail(
            interaction,
            kind,
            choice,
            back_label="↩ Back to list",
            back_custom_id=f"btd6_event_detail:back:{kind}:{choice}"[:100],
            parent_builder=_rebuild_list,
        )


class LiveEventsBrowserView(HubView):
    """By-kind list of recent (incl. ended) events. The history path."""

    def __init__(self, author: discord.User | discord.Member) -> None:
        super().__init__(author)
        self._kind: str | None = None
        self._vm: EventListViewModel | None = None
        self._render()

    def _render(self) -> None:
        """(Re)build children: kind picker + (event select) + back-to-live."""
        self.clear_items()
        self.add_item(_KindSelect())
        if self._vm is not None:
            self.add_item(_EventSelect(self._vm))

        author = self._author

        async def _rebuild_overview(
            _i: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            vm = await build_live_overview_view_model()
            return build_live_overview_embed(vm), LiveOverviewView(author, vm)

        attach_back_button(
            self,
            label="↩ Live now",
            custom_id="btd6_live_browser:back",
            parent_builder=_rebuild_overview,
        )

    def set_kind(self, kind: str, vm: EventListViewModel) -> None:
        """Populate the event select for the given kind."""
        self._kind = kind
        self._vm = vm
        self._render()


class EventDetailView(HubView):
    """One specific event. Reached from the overview or the history list."""

    def __init__(self, author: discord.User | discord.Member) -> None:
        super().__init__(author)
        self._vm: EventDetailViewModel | None = None

    def set_vm(self, vm: EventDetailViewModel) -> None:
        self._vm = vm


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------


async def open_live_events_browser(interaction: discord.Interaction) -> None:
    """Open the live-events overview as an ephemeral followup."""
    if not await safe_defer(interaction, ephemeral=True):
        return
    vm = await build_live_overview_view_model()
    view = LiveOverviewView(interaction.user, vm)
    await safe_followup(
        interaction,
        embed=build_live_overview_embed(vm),
        view=view,
        ephemeral=True,
    )


__all__ = [
    "EventDetailView",
    "LiveEventsBrowserView",
    "LiveOverviewView",
    "build_event_detail_embed_from_vm",
    "build_event_list_embed",
    "build_kind_picker_embed",
    "build_live_overview_embed",
    "open_live_events_browser",
]
