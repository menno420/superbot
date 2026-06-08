"""Server Management Hub — the unified operator navigation surface (PR14).

One persistent panel (``!servermanagement`` + ``/server-management``) that gives
an operator a single entry point to every specialised manager — moderation,
channels, roles, cleanup, setup — with read-only health badges summarising what
needs attention.

**The hub holds zero domain logic.** It *composes* the existing manager panels
and the read-only :mod:`services.server_management_hub` badge model; it never
re-implements a manager. Each manager button routes into that manager's own
``build_help_menu_view`` hook (resolved at click time via
``interaction.client.get_cog`` — so this view needs **no module-level import of
any cog**, keeping the ``views → cogs`` arch boundary clean). The exception is
Setup, which owns its own session/depth lifecycle in a dedicated channel and is
opened through its reusable wizard entry.

**Authority (ADR-005 / ``docs/capability-authority.md`` §4).** Like
:class:`views.moderation.main_panel.ModPanelView`, the hub overrides
``interaction_check`` with an **authority** gate rather than anchor ownership:
the administrator floor is re-evaluated live on every interaction. Re-evaluating
``guild_permissions.administrator`` at click time also covers the restored-panel
case (a panel outliving the caller's admin role) and lets the same view back the
ephemeral ``/server-management`` slash, which has no anchor.

**Restoration.** ``ServerManagementHubView`` is ``@register``-ed with a no-arg
constructor and static ``servermanagement:*`` custom_ids, so
``message_anchor_manager.restore_anchors`` re-binds it across restarts for free
(the prefix command anchors the panel via ``panel_manager.get_or_render_panel``).
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from core.runtime.persistent_views import PersistentView, register
from services.server_management_hub import HubStatus, collect_hub_status
from utils.ui_constants import ADMIN_COLOR
from views.base import interaction_is_admin
from views.navigation import attach_back_button

logger = logging.getLogger("bot.views.server_management")

# Managers reachable by routing into another cog's ``build_help_menu_view``
# hook. Key (custom_id suffix) → (get_cog name, human label). Setup is handled
# separately (its own wizard entry), so it is not in this table.
_ROUTED_MANAGERS: dict[str, tuple[str, str]] = {
    "moderation": ("ModerationCog", "Moderation"),
    "channels": ("ChannelCog", "Channels"),
    "roles": ("RoleCog", "Roles"),
    "cleanup": ("Cleanup", "Cleanup"),
}

_BACK_CUSTOM_ID = "servermanagement:back"
_BACK_LABEL = "↩ Server Management"


def build_hub_embed(status: HubStatus) -> discord.Embed:
    """Render a :class:`HubStatus` into the hub embed (read-only badges)."""
    embed = discord.Embed(
        title="🧭 Server Management Hub",
        description=(
            "Your single entry point to the server's operator tools. "
            "Pick a manager below — the badges are a read-only health summary."
        ),
        color=ADMIN_COLOR,
    )
    lines = [
        f"{badge.glyph} {badge.emoji} **{badge.label}** — {badge.summary}"
        for badge in status.badges
    ]
    embed.add_field(name="Managers", value="\n".join(lines), inline=False)
    embed.add_field(
        name="Overall configuration health",
        value=f"{status.overall_glyph} {status.overall_summary}",
        inline=False,
    )
    embed.set_footer(text="Read-only summary · click a manager to open it")
    return embed


async def build_server_management_hub(
    guild: discord.Guild,
) -> tuple[discord.Embed, ServerManagementHubView]:
    """Single source of truth for opening the hub: compose status → (embed, view).

    Used by the ``!servermanagement`` prefix command, the ``/server-management``
    slash, and the per-manager "Back to Server Management" button.
    """
    status = await collect_hub_status(guild)
    return build_hub_embed(status), ServerManagementHubView()


def _attach_back_to_hub(view: discord.ui.View) -> None:
    """Append a "Back to Server Management" control to a routed manager panel."""

    async def _hub_parent(
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        guild = interaction.guild
        if guild is None:  # hub is guild-only; attach_back_button surfaces this
            raise RuntimeError("Server Management hub requires a guild")
        return await build_server_management_hub(guild)

    attach_back_button(
        view,
        label=_BACK_LABEL,
        custom_id=_BACK_CUSTOM_ID,
        parent_builder=_hub_parent,
        error_message="Couldn't reload the Server Management hub — see logs.",
    )


@register
class ServerManagementHubView(PersistentView):
    """Persistent operator hub routing to the specialised managers.

    Authority-gated (administrator floor), not ownership-gated — see the module
    docstring. Stateless: every callback recovers context from ``interaction``.
    """

    SUBSYSTEM = "servermanagement"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction_is_admin(interaction):
            return True
        await interaction.response.send_message(
            "❌ You need **Administrator** permission to use the Server "
            "Management hub.",
            ephemeral=True,
        )
        return False

    # ------------------------------------------------------------------ routing

    async def _open_manager(
        self,
        interaction: discord.Interaction,
        key: str,
    ) -> None:
        """Open a routed manager's panel in place via its help-menu hook."""
        cog_name, label = _ROUTED_MANAGERS[key]
        # interaction.client is the live commands.Bot at runtime; Interaction is
        # typed against discord.Client, which has no get_cog.
        cog = interaction.client.get_cog(cog_name)  # type: ignore[attr-defined]
        build = getattr(cog, "build_help_menu_view", None) if cog else None
        if not callable(build):
            await interaction.response.send_message(
                f"The {label} manager isn't available right now.",
                ephemeral=True,
            )
            return
        try:
            embed, sub_view = await build(interaction)
        except Exception as exc:  # noqa: BLE001 — navigation must not crash
            logger.warning(
                "server_management hub: build_help_menu_view failed for %s: %s",
                cog_name,
                exc,
                exc_info=True,
            )
            await interaction.response.send_message(
                f"Couldn't open the {label} manager — see bot logs.",
                ephemeral=True,
            )
            return
        _attach_back_to_hub(sub_view)
        await interaction.response.edit_message(embed=embed, view=sub_view)

    # ------------------------------------------------------------------ buttons

    @discord.ui.button(
        label="🛡️ Moderation",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="servermanagement:moderation",
    )
    async def moderation_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._open_manager(interaction, "moderation")

    @discord.ui.button(
        label="📺 Channels",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="servermanagement:channels",
    )
    async def channels_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._open_manager(interaction, "channels")

    @discord.ui.button(
        label="🎭 Roles",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="servermanagement:roles",
    )
    async def roles_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._open_manager(interaction, "roles")

    @discord.ui.button(
        label="🧹 Cleanup",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="servermanagement:cleanup",
    )
    async def cleanup_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._open_manager(interaction, "cleanup")

    @discord.ui.button(
        label="🧩 Setup",
        style=discord.ButtonStyle.success,
        row=1,
        custom_id="servermanagement:setup",
    )
    async def setup_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # Setup owns its own session/depth lifecycle in a dedicated channel, so
        # we hand off to its reusable wizard entry (it owns the response) rather
        # than editing a panel in place. Lazy import keeps the cogs layer out of
        # this view's module scope (arch boundary).
        from cogs.setup._wizard_entry import open_wizard_from_slash

        await open_wizard_from_slash(interaction)

    @discord.ui.button(
        label="🔄 Refresh",
        style=discord.ButtonStyle.secondary,
        row=2,
        custom_id="servermanagement:refresh",
    )
    async def refresh_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "The hub is only available inside a server.",
                ephemeral=True,
            )
            return
        # Recomposing the badges touches read-only detectors — defer so a slow
        # guild can't blow the 3s response window, then edit in place.
        if not await safe_defer(interaction):
            return
        status = await collect_hub_status(interaction.guild)
        await safe_edit(interaction, embed=build_hub_embed(status), view=self)
