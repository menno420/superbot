"""Entry-point chooser for the Tools & Workflows admin UI (Phase 3).

Reached from the main :class:`views.ai.panel.AIPanelView` ``Tools`` button. The
chooser is a **page of the one AI anchor message** (AI nav plan PR 2) with one
button per scope (Guild / Channel / Category) plus a dry-run Preview. Each button
``edit_message``-es the anchor to that scope's picker with a Back button, instead
of opening a new ephemeral; writes flow through
:mod:`services.ai_orchestration_mutation`.

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


def build_tools_chooser_page() -> tuple[discord.Embed, ToolsChooserView]:
    """Return the chooser ``(embed, view)`` — the Back target for its pages.

    The static intro embed (no snapshot) is used for Back navigation; the
    live "Current" decoration is only rendered on the first entry from the
    AI panel, where the snapshot is read best-effort.
    """
    return build_tools_embed(None), ToolsChooserView()


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
        from views.ai._nav import add_back_button, ai_home_page

        add_back_button(self, label="↩ AI home", builder=ai_home_page)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Canonical admin gate — honours the platform owner (config.BOT_OWNER_USER_ID).
        from views.base import interaction_is_admin

        if not interaction_is_admin(interaction):
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

        view = GuildToolsProfileView()
        _add_back_to_tools(view)
        await interaction.response.edit_message(
            embed=_tools_page_embed(
                "Tools · guild default",
                "Pick the guild-default orchestration profile.",
            ),
            view=view,
        )

    @discord.ui.button(label="Channel", style=discord.ButtonStyle.primary, row=0)
    async def channel_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.tools.scope_view import ChannelToolsSelectView

        view = ChannelToolsSelectView()
        _add_back_to_tools(view)
        await interaction.response.edit_message(
            embed=_tools_page_embed(
                "Tools · channel",
                "Pick a channel — the next step lists the orchestration profiles.",
            ),
            view=view,
        )

    @discord.ui.button(label="Category", style=discord.ButtonStyle.primary, row=0)
    async def category_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.tools.scope_view import CategoryToolsSelectView

        view = CategoryToolsSelectView()
        _add_back_to_tools(view)
        await interaction.response.edit_message(
            embed=_tools_page_embed(
                "Tools · category",
                "Pick a category — the next step lists the orchestration profiles.",
            ),
            view=view,
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

        view = ToolsPreviewChannelSelectView()
        _add_back_to_tools(view)
        await interaction.response.edit_message(
            embed=_tools_page_embed(
                "Tools · preview (dry-run)",
                "Pick a channel to preview the resolved AI tool orchestration.",
            ),
            view=view,
        )


def _tools_page_embed(title: str, instruction: str) -> discord.Embed:
    """A focused page embed for a Tools sub-page rendered on the anchor."""
    return discord.Embed(
        title=title,
        description=instruction,
        color=_PANEL_COLOR,
    ).set_footer(text="Administrator-only · in-place navigation.")


def _add_back_to_tools(view: discord.ui.View) -> None:
    """Attach a Back button that returns the anchor to the Tools chooser."""
    from views.ai._nav import add_back_button

    add_back_button(view, label="↩ AI Tools", builder=build_tools_chooser_page)


__all__ = [
    "ToolsChooserView",
    "build_tools_chooser_page",
    "build_tools_embed",
]
