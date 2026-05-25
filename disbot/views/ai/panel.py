"""AI Platform persistent panel — Module 2 of the AI/BTD6 plan.

Pattern B placement per ``docs/architecture.md`` §"PersistentView
placement": the view lives in ``views/ai/`` so the cog file stays
small. Importing this module triggers the ``@register`` decorator
on :class:`AIPanelView` so the persistent-view registry sees the
``ai`` subsystem before ``on_ready`` runs ``restore_anchors``.

Custom_ids use the ``ai:<action>`` prefix. ``AICog.cog_load``
registers :func:`handle_ai_interaction` with
:mod:`core.runtime.interaction_router` so the router does not log
"Unhandled interaction prefix 'ai'" warnings when a button is
clicked. The View's own ``@discord.ui.button`` callbacks remain the
primary dispatcher for ``PersistentView`` buttons; the router
handler is a safety net that bails immediately when
``interaction.response.is_done()`` is true.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from core.runtime.persistent_views import PersistentView, register
from services import ai_diagnostics_service

logger = logging.getLogger("bot.views.ai.panel")

_PANEL_COLOR = discord.Color.blurple()

AI_ROUTER_PREFIX = "ai"


def build_ai_panel_embed() -> discord.Embed:
    """Build the read-only AI Platform overview embed.

    Reads ``ai_diagnostics_service.snapshot_for_cog()`` so the
    overview reflects the latest counters without invoking any
    provider.
    """
    snap = ai_diagnostics_service.snapshot_for_cog()
    enabled = snap["enabled"]
    degraded = snap["degraded"]
    status_emoji = "✅" if enabled and not degraded else ("⚠️" if degraded else "💤")

    embed = discord.Embed(
        title=f"{status_emoji} AI Platform",
        description=(
            "Read-only diagnostics for the AI gateway. The buttons "
            "below open the matching subcommands without making a "
            "provider call."
        ),
        color=_PANEL_COLOR,
    )
    embed.add_field(name="Enabled", value="yes" if enabled else "no", inline=True)
    embed.add_field(
        name="Default provider",
        value=str(snap["default_provider"]),
        inline=True,
    )
    embed.add_field(
        name="Setup advisor provider",
        value=str(snap["setup_advisor_provider"]),
        inline=True,
    )
    embed.add_field(
        name="Active provider (last call)",
        value=str(snap["provider_active"]),
        inline=True,
    )
    embed.add_field(
        name="Requests / failures",
        value=f"{snap['requests_observed']} / {snap['failures_observed']}",
        inline=True,
    )
    embed.add_field(
        name="Redaction",
        value="on" if snap["redaction_enabled"] else "off",
        inline=True,
    )
    if degraded:
        embed.add_field(
            name="Last fallback reason",
            value=str(snap["last_fallback_reason"] or "—"),
            inline=False,
        )
    embed.set_footer(text="!ai status / !ai diagnostics / !ai providers / !ai routing")
    return embed


@register
class AIPanelView(PersistentView):
    """Persistent AI Platform panel — administrator-only.

    The panel is intentionally read-only. Every button refreshes one
    of the existing diagnostic views; no button performs a provider
    call or any state mutation.
    """

    SUBSYSTEM = "ai"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        member = interaction.user
        if not getattr(member, "guild_permissions", None) or not (
            member.guild_permissions.administrator  # type: ignore[union-attr]
        ):
            await interaction.response.send_message(
                "❌ You need the Administrator permission to use the AI panel.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="Refresh",
        style=discord.ButtonStyle.secondary,
        row=0,
        custom_id="ai:refresh",
    )
    async def refresh_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = _embed_for_ai_panel_action("refresh")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Diagnostics",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="ai:diagnostics",
    )
    async def diagnostics_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = _embed_for_ai_panel_action("diagnostics")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Providers",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="ai:providers",
    )
    async def providers_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = _embed_for_ai_panel_action("providers")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Routing",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="ai:routing",
    )
    async def routing_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = _embed_for_ai_panel_action("routing")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Settings",
        style=discord.ButtonStyle.success,
        row=1,
        custom_id="ai:settings",
    )
    async def settings_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # M1: open the AI subsystem settings panel in place.
        # Settings is the only action that requires an async call —
        # _embed_for_ai_panel_action handles the four sync actions; this
        # branch is special-cased here and in handle_ai_interaction below.
        from cogs.ai_cog import _build_ai_settings_panel

        embed, view = await _build_ai_settings_panel(
            interaction.user,
            interaction.guild_id,
        )
        await interaction.response.edit_message(embed=embed, view=view)


# ---------------------------------------------------------------------------
# Shared dispatch + interaction-router handler
# ---------------------------------------------------------------------------


def _embed_for_ai_panel_action(action: str) -> discord.Embed | None:
    """Single source of truth for sync AI panel action → embed mapping.

    Returns the embed for refresh / diagnostics / providers / routing.
    Returns ``None`` for "settings" (async, special-cased by callers) and
    for unknown actions. Callers decide which ``view`` to attach (the
    View buttons reuse ``self``; the router handler creates a fresh
    ``AIPanelView()``).
    """
    if action == "refresh":
        return build_ai_panel_embed()
    # Lazy imports keep this module importable from cogs.ai_cog without
    # introducing a circular dependency at module load time.
    if action == "diagnostics":
        from cogs.ai_cog import build_diagnostics_embed

        return build_diagnostics_embed()
    if action == "providers":
        from cogs.ai_cog import build_providers_embed

        return build_providers_embed()
    if action == "routing":
        from cogs.ai_cog import build_routing_embed

        return build_routing_embed()
    return None


async def handle_ai_interaction(
    interaction: discord.Interaction,
    action: str,
    session: Any,
    request_id: str,
) -> None:
    """Interaction-router handler for prefix ``"ai"``.

    The View's own ``@discord.ui.button`` callbacks are the primary
    dispatcher for ``PersistentView`` button clicks — discord.py
    dispatches them in the connection layer before ``on_interaction``
    fires. This handler runs only after that path completes, so it
    bails immediately when the response has already been sent.
    """
    # PersistentView may already have handled this interaction.
    # Check is_done() BEFORE any permission check or action handling.
    if interaction.response.is_done():
        return

    # Admin gate — mirrors AIPanelView.interaction_check so the router
    # path enforces the same authorization as the View path.
    member = interaction.user
    if not getattr(member, "guild_permissions", None) or not (
        member.guild_permissions.administrator  # type: ignore[union-attr]
    ):
        await interaction.response.send_message(
            "❌ You need the Administrator permission to use the AI panel.",
            ephemeral=True,
        )
        return

    # Settings requires an async call to _build_ai_settings_panel; the
    # synchronous _embed_for_ai_panel_action helper cannot serve it.
    if action == "settings":
        from cogs.ai_cog import _build_ai_settings_panel

        embed, view = await _build_ai_settings_panel(
            interaction.user,
            interaction.guild_id,
        )
        await interaction.response.edit_message(embed=embed, view=view)
        return

    embed = _embed_for_ai_panel_action(action)
    if embed is None:
        await interaction.response.send_message(
            f"❌ Unknown AI panel action: {action!r}",
            ephemeral=True,
        )
        return
    await interaction.response.edit_message(embed=embed, view=AIPanelView())


__all__ = [
    "AI_ROUTER_PREFIX",
    "AIPanelView",
    "build_ai_panel_embed",
    "handle_ai_interaction",
]
