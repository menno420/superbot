"""AI Platform persistent panel — Module 2 of the AI/BTD6 plan.

Pattern B placement per ``docs/architecture.md`` §"PersistentView
placement": the view lives in ``views/ai/`` so the cog file stays
small. Importing this module triggers the ``@register`` decorator
on :class:`AIPanelView` so the persistent-view registry sees the
``ai`` subsystem before ``on_ready`` runs ``restore_anchors``.

Custom_ids use the ``ai:<action>`` prefix. The cog wires a single
interaction-router handler for prefix ``ai`` that dispatches to
embed-building helpers in :mod:`services.ai_diagnostics_service` —
no provider logic ever runs from a button.
"""

from __future__ import annotations

import discord

from core.runtime.persistent_views import PersistentView, register
from services import ai_diagnostics_service

_PANEL_COLOR = discord.Color.blurple()


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
        await interaction.response.edit_message(embed=build_ai_panel_embed(), view=self)

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
        from cogs.ai_cog import build_diagnostics_embed

        await interaction.response.edit_message(
            embed=build_diagnostics_embed(),
            view=self,
        )

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
        from cogs.ai_cog import build_providers_embed

        await interaction.response.edit_message(
            embed=build_providers_embed(),
            view=self,
        )

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
        from cogs.ai_cog import build_routing_embed

        await interaction.response.edit_message(
            embed=build_routing_embed(),
            view=self,
        )
