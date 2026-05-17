"""Moderation panel PersistentView — extracted from ``cogs/moderation_cog.py``.

Pattern B placement per ``docs/architecture.md`` §"PersistentView
placement": the view lives in views/ and the cog re-exports for the
persistent-view registry side-effect.

Importing this module triggers the ``@register`` decorator on
``ModPanelView`` so the persistent-view registry is populated before
``on_ready`` runs ``restore_anchors``.  Custom_ids (``mod:warn``,
``mod:timeout``, …) are unchanged from the pre-extraction layout so
existing panel anchors keep dispatching correctly after restart.

ModPanelView has a deliberate ``interaction_check`` override: the
moderation dashboard is a collaborative staff tool, so any member with
Moderate Members permission may interact (not just the invoker).
"""

from __future__ import annotations

import discord

from core.runtime.persistent_views import PersistentView, register
from views.moderation.modals import (
    _BanModal,
    _ClearWarningsModal,
    _KickModal,
    _ModLogsModal,
    _TimeoutModal,
    _UnbanModal,
    _WarnModal,
)


@register
class ModPanelView(PersistentView):
    """Persistent moderation dashboard — any staff member with moderate_members can use it.

    Intentional exception to invoker-only ownership: moderation panels are
    collaborative staff tools.  Any moderator in the guild may interact.
    """

    SUBSYSTEM = "moderation"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.moderate_members:  # type: ignore[union-attr]
            await interaction.response.send_message(
                "❌ You need Moderate Members permission.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="⚠️ Warn",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="mod:warn",
    )
    async def warn_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_WarnModal())

    @discord.ui.button(
        label="⏳ Timeout",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="mod:timeout",
    )
    async def timeout_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_TimeoutModal())

    @discord.ui.button(
        label="👢 Kick",
        style=discord.ButtonStyle.danger,
        row=0,
        custom_id="mod:kick",
    )
    async def kick_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_KickModal())

    @discord.ui.button(
        label="🚫 Ban",
        style=discord.ButtonStyle.danger,
        row=1,
        custom_id="mod:ban",
    )
    async def ban_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_BanModal())

    @discord.ui.button(
        label="✅ Unban",
        style=discord.ButtonStyle.success,
        row=1,
        custom_id="mod:unban",
    )
    async def unban_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_UnbanModal())

    @discord.ui.button(
        label="📋 Mod Logs",
        style=discord.ButtonStyle.grey,
        row=1,
        custom_id="mod:logs",
    )
    async def modlogs_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_ModLogsModal())

    @discord.ui.button(
        label="⬛ Clear Warnings",
        style=discord.ButtonStyle.grey,
        row=2,
        custom_id="mod:clearwarn",
    )
    async def clearwarn_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await interaction.response.send_modal(_ClearWarningsModal())
