"""Entry-point chooser for the Tools & Workflows admin UI (Phase 3).

Reached from the main :class:`views.ai.panel.AIPanelView` ``Tools`` button. The
chooser is an ephemeral follow-up with one button per scope (Guild / Channel /
Category) plus a dry-run Preview. Each opens its own ephemeral follow-up; writes
flow through :mod:`services.ai_orchestration_mutation`.

This is the "Tools & workflows" surface the orchestration plan §9.4 asks for —
an operator narrows toolsets / requires a grounding group for a channel without
editing instruction text. It is deliberately separate from the **Behavior**
chooser (tone / reply mode) and the **Policy** chooser (who may reply, when).
"""

from __future__ import annotations

import logging
from typing import Any

import discord

logger = logging.getLogger("bot.views.ai.tools.chooser")

_PANEL_COLOR = discord.Color.blurple()
_CHOOSER_TIMEOUT_SECONDS = 180


def build_tools_embed(snapshot: Any = None) -> discord.Embed:
    """Intro embed for the Tools & Workflows chooser.

    When ``snapshot`` (an :class:`AIConfigSnapshot`) is supplied, the current
    guild-default profile + override counts are shown so an operator sees the
    live state at a glance; without it the embed is the static introduction.
    """
    embed = discord.Embed(
        title="AI Tools & Workflows",
        description=(
            "Choose **which tools the AI may use** here, independently of its "
            "reply tone (Behavior) and who may talk to it (Policy). A profile "
            "narrows the offered toolset, sets the tool-choice requirement, and "
            "caps the tool/loop budget. Writes flow through "
            "`services.ai_orchestration_mutation`; the next message picks up the "
            "new profile. Safe default: every scope inherits today's behaviour "
            "until you set a profile."
        ),
        color=_PANEL_COLOR,
    )
    embed.add_field(
        name="Guild / Channel / Category",
        value=(
            "Bind a built-in orchestration profile at a scope. Channel wins "
            "over category, category over the guild default."
        ),
        inline=False,
    )
    embed.add_field(
        name="Preview (dry-run)",
        value=(
            "Pick a channel to see the resolved profile, the offered vs withheld "
            "tools (with reason codes), and the loop budget — no provider call."
        ),
        inline=False,
    )
    orchestration = getattr(snapshot, "orchestration", None)
    if orchestration is not None:
        key = orchestration.guild_profile_key or "compatible_default (today)"
        embed.add_field(
            name="Current",
            value=(
                f"guild default: `{key}`\n"
                f"overrides: {orchestration.channel_override_count} channel · "
                f"{orchestration.category_override_count} category"
            ),
            inline=False,
        )
    embed.set_footer(text="Administrator-only · ephemeral follow-up.")
    return embed


class ToolsChooserView(discord.ui.View):
    """Ephemeral workflow dispatcher for the Tools & Workflows UI."""

    def __init__(self) -> None:
        super().__init__(timeout=_CHOOSER_TIMEOUT_SECONDS)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        member = interaction.user
        perms = getattr(member, "guild_permissions", None)
        if perms is None or not getattr(perms, "administrator", False):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Guild", style=discord.ButtonStyle.primary, row=0)
    async def guild_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.tools.scope_view import GuildToolsProfileView

        await interaction.response.send_message(
            "Pick the guild-default orchestration profile.",
            view=GuildToolsProfileView(),
            ephemeral=True,
        )

    @discord.ui.button(label="Channel", style=discord.ButtonStyle.primary, row=0)
    async def channel_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.tools.scope_view import ChannelToolsSelectView

        await interaction.response.send_message(
            "Pick a channel — the next step lists the orchestration profiles.",
            view=ChannelToolsSelectView(),
            ephemeral=True,
        )

    @discord.ui.button(label="Category", style=discord.ButtonStyle.primary, row=0)
    async def category_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.tools.scope_view import CategoryToolsSelectView

        await interaction.response.send_message(
            "Pick a category — the next step lists the orchestration profiles.",
            view=CategoryToolsSelectView(),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Preview (dry-run)",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def preview_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.tools.preview_view import ToolsPreviewChannelSelectView

        await interaction.response.send_message(
            "Pick a channel to preview the resolved AI tool orchestration.",
            view=ToolsPreviewChannelSelectView(),
            ephemeral=True,
        )


__all__ = ["ToolsChooserView", "build_tools_embed"]
