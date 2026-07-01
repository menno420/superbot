"""Phase 9b — LoggingPanelView Routes subpage.

Adds a dense routes view showing all seven logging channel routes
(``mod`` / ``cleanup`` / ``debug`` / ``info`` / ``warning`` / ``error``
/ ``audit``), their current binding state, and per-route Set / Create
controls. Reuses the existing :class:`cogs.logging.select_view.
LogChannelSelectView` and :class:`cogs.logging.provision_view.
LogChannelProvisionView` — those views already accept arbitrary ``kind``
tokens after the Phase 9b table extension.

The view itself contains zero mutation logic. Set routes through
``BindingMutationPipeline`` via the existing select-view; Create
routes through ``ResourceProvisioningPipeline`` via the existing
provision-view. No counter buckets are added in this PR — that waits
until Phase 9c when actual severity events flow.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from utils.ui_constants import ADMIN_COLOR
from views.base import HubView

if TYPE_CHECKING:
    pass

logger = logging.getLogger("bot.cogs.logging.routes_panel")


# Display order for the routes embed + select — **roots-first**
# (tools/sim/settings_order_sim.py, 2026-07-01). The two fallback roots lead so
# the operator sees the minimum coverage set immediately: set ``mod`` + those
# two and every route is delivered *somewhere*; everything below refines one of
# them. This cut scroll-to-full-coverage from 7 → 1 vs the old category-first
# order (pinned to the sim by tests/unit/invariants/test_settings_order.py).
_ROUTE_DISPLAY_ORDER: tuple[str, ...] = (
    # Roots — set these two and everything is covered by fallback.
    "mod",  # ROOT: severity / audit / cleanup fall back here
    "events",  # ROOT: message / member / role fall back here
    # ``mod`` overrides (moderation sources + severity + audit):
    "cleanup",
    "debug",
    "info",
    "warning",
    "error",
    "audit",
    # ``events`` overrides (per-category server events, Q-0109):
    "message_log",
    "member_log",
    "role_log",
)


async def _resolve_route_state(
    guild: discord.Guild,
    kind: str,
) -> dict[str, object]:
    """Resolve the current binding state for a route, without raising.

    Returns a dict with:

    * ``kind`` — the route token.
    * ``binding_name`` — the underlying ``logging.<x>_channel`` name.
    * ``channel`` — the resolved :class:`discord.TextChannel` or ``None``.
    * ``source`` — ``"binding"`` if the route's own binding resolved,
      ``"fallback"`` if it walked the fallback chain to mod, or
      ``"unset"`` if nothing resolved.
    """
    from services.server_logging import (
        _ROUTE_FALLBACK,
        _ROUTE_TO_BINDING,
        resolve_log_channel,
    )

    binding_name = _ROUTE_TO_BINDING.get(kind, "?")

    # Try the route's own binding directly via the resolver. If it
    # resolves to a channel, the source depends on whether the fallback
    # chain kicked in. The cheapest accurate read: try the route, then
    # try mod (the fallback target); if they match, it's a fallback.
    try:
        ch = await resolve_log_channel(guild, kind)
    except Exception as exc:  # noqa: BLE001 — diagnostics must not raise
        logger.warning("Routes panel: resolve_log_channel(%r) failed: %s", kind, exc)
        return {
            "kind": kind,
            "binding_name": binding_name,
            "channel": None,
            "source": "error",
        }
    if ch is None:
        return {
            "kind": kind,
            "binding_name": binding_name,
            "channel": None,
            "source": "unset",
        }

    fallback = _ROUTE_FALLBACK.get(kind)
    if fallback is None or kind == "mod":
        # No fallback for ``mod`` — if it resolved, it came from its own
        # binding (or legacy scalar; we treat both as "binding" for the
        # operator-facing display).
        return {
            "kind": kind,
            "binding_name": binding_name,
            "channel": ch,
            "source": "binding",
        }
    try:
        fallback_ch = await resolve_log_channel(guild, fallback)
    except Exception:  # noqa: BLE001 — diagnostic only
        fallback_ch = None
    source = "fallback" if fallback_ch is ch else "binding"
    return {
        "kind": kind,
        "binding_name": binding_name,
        "channel": ch,
        "source": source,
    }


async def build_routes_embed(guild: discord.Guild | None) -> discord.Embed:
    """Build the read-only Routes overview embed."""
    embed = discord.Embed(
        title="🗺️ Logging Routes",
        description=(
            "**Quick start:** set the top two — **`mod`** and **`events`** — "
            "and every route is delivered somewhere (the rest fall back to "
            "them). Split out any route below only when you want it in its own "
            "channel.\n\n"
            "Each row shows a route, its binding, and where it resolves today. "
            "Pick one, then **Set Channel** (bind an existing channel) or "
            "**Create Channel** — both route through `BindingMutationPipeline` "
            "/ `ResourceProvisioningPipeline` and record an audit row."
        ),
        color=ADMIN_COLOR,
    )
    if guild is None:
        embed.add_field(
            name="No guild context",
            value="This view requires a guild context to resolve channels.",
            inline=False,
        )
        return embed

    from services.server_logging import _ROUTE_FALLBACK

    lines: list[str] = []
    for kind in _ROUTE_DISPLAY_ORDER:
        state = await _resolve_route_state(guild, kind)
        ch = state["channel"]
        source = state["source"]
        binding = state["binding_name"]
        mention = getattr(ch, "mention", None) if ch is not None else None
        if source == "binding" and mention is not None:
            marker = f"→ {mention}"
        elif source == "fallback" and mention is not None:
            # Name the actual fallback target — event routes fall back to
            # the combined `events` channel, not `mod`.
            target = _ROUTE_FALLBACK.get(kind) or "mod"
            marker = f"↪ {mention} *(via {target} fallback)*"
        elif source == "error":
            marker = "⚠️ *(resolution error — see logs)*"
        else:
            marker = "*(unset)*"
        lines.append(f"**`{kind}`** ・ `logging.{binding}` {marker}")
    embed.add_field(
        name="Routes",
        value="\n".join(lines),
        inline=False,
    )
    embed.set_footer(
        text=(
            "Pick a route below, then Set Channel or Create Channel. "
            "Routes without their own binding fall back along their "
            "fallback chain (severity/audit → mod; event routes → events)."
        ),
    )
    return embed


class _RouteSelect(discord.ui.Select):
    """Single-select listing all seven routes."""

    def __init__(self, selected: str | None) -> None:
        options: list[discord.SelectOption] = []
        for kind in _ROUTE_DISPLAY_ORDER:
            options.append(
                discord.SelectOption(
                    label=kind,
                    value=kind,
                    default=(kind == selected),
                ),
            )
        super().__init__(
            placeholder="Choose a route…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="logging_routes.select",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, LoggingRoutesView):
            return
        view.selected_kind = self.values[0]
        # Rebuild the select so ``default=`` tracks current state.
        view._rebuild_select()
        if not await safe_defer(interaction):
            return
        embed = await build_routes_embed(interaction.guild)
        await safe_edit(interaction, embed=embed, view=view)


class LoggingRoutesView(HubView):
    """Phase 9b — Routes subpage on top of LoggingPanelView."""

    SUBSYSTEM = "logging"

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)
        self.selected_kind: str | None = None
        self.add_item(_RouteSelect(self.selected_kind))

    def _rebuild_select(self) -> None:
        """Re-add the select so its ``default=`` tracks current state."""
        for child in list(self.children):
            if isinstance(child, discord.ui.Select) and child.custom_id == (
                "logging_routes.select"
            ):
                self.remove_item(child)
        self.add_item(_RouteSelect(self.selected_kind))

    async def _require_route(
        self,
        interaction: discord.Interaction,
    ) -> str | None:
        if self.selected_kind is None:
            await interaction.response.send_message(
                "Pick a route from the dropdown first.",
                ephemeral=True,
            )
            return None
        return self.selected_kind

    @discord.ui.button(
        label="🔗 Set Channel",
        style=discord.ButtonStyle.blurple,
        row=1,
        custom_id="logging_routes.set",
    )
    async def btn_set(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        kind = await self._require_route(interaction)
        if kind is None:
            return
        # Local import — keeps the heavy view module out of import time.
        from cogs.logging.panel import _open_select

        await _open_select(interaction, kind=kind)

    @discord.ui.button(
        label="🆕 Create Channel",
        style=discord.ButtonStyle.success,
        row=1,
        custom_id="logging_routes.create",
    )
    async def btn_create(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        kind = await self._require_route(interaction)
        if kind is None:
            return
        from cogs.logging.panel import _open_provision

        await _open_provision(interaction, kind=kind)

    @discord.ui.button(
        label="🔄 Refresh",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="logging_routes.refresh",
    )
    async def btn_refresh(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        embed = await build_routes_embed(interaction.guild)
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="↩ Back to Logging",
        style=discord.ButtonStyle.secondary,
        row=4,
        custom_id="logging_routes.back",
    )
    async def btn_back(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        # Phase 3.5 — share the defer + edit + error-handling flow with
        # every other back-button in the codebase via views.navigation.
        from views.navigation import carry_back, transition_to

        async def _build_logging_parent(
            interaction: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            from cogs.logging.panel import LoggingPanelView, build_panel_embed

            view = LoggingPanelView(self._author)
            # Carry the externally-attached back (↩ Back to Settings / Help)
            # forward onto the rebuilt panel so returning from Routes does not
            # strand the operator one level up from where they entered.
            carry_back(self, view)
            embed = await build_panel_embed(interaction.guild)
            return embed, view

        await transition_to(
            interaction,
            builder=_build_logging_parent,
            error_message="Couldn't open the logging panel — see bot logs.",
        )


__all__ = ["LoggingRoutesView", "build_routes_embed"]
