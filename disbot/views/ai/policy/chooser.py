"""Entry-point chooser for the AI policy admin UI (PR4A).

Reached from the main :class:`views.ai.panel.AIPanelView` ``Policy``
button. The chooser is sent as an ephemeral follow-up so the operator
sees a private window with the four scope buttons (Channel / Category
/ Role / List). Each scope button opens its own ephemeral follow-up
in the same conversation.

The chooser View is transient — created per click, not persisted —
because the user is actively interacting and the timeout handles
abandoned sessions. The main panel itself stays persistent.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.views.ai.policy.chooser")

_PANEL_COLOR = discord.Color.blurple()
_CHOOSER_TIMEOUT_SECONDS = 180


def build_chooser_embed() -> discord.Embed:
    """Build the read-only embed that introduces the policy chooser."""
    embed = discord.Embed(
        title="AI Policy",
        description=(
            "Override the guild's AI policy for specific channels, "
            "categories, or roles. Writes flow through "
            "`services.ai_policy_mutation` and emit `ai.policy.*` "
            "events; the natural-language stage picks up the new "
            "rules on the next message."
        ),
        color=_PANEL_COLOR,
    )
    embed.add_field(
        name="Channel",
        value=(
            "Pick a channel and set its mode "
            "(`inherit` / `always_reply` / `mention_only` / `disabled`)."
        ),
        inline=False,
    )
    embed.add_field(
        name="Category",
        value="Same shape as channel; applies to every channel in the category.",
        inline=False,
    )
    embed.add_field(
        name="Role",
        value="Allow / deny / inherit and optional min-level override per role.",
        inline=False,
    )
    embed.add_field(
        name="List overrides",
        value="See every current override for this guild (paged).",
        inline=False,
    )
    embed.set_footer(text="Administrator-only · ephemeral follow-up.")
    return embed


class PolicyChooserView(discord.ui.View):
    """Ephemeral chooser with one button per scope.

    The View has no persistent custom_id prefix — it is created per
    interaction and times out after ``_CHOOSER_TIMEOUT_SECONDS``.
    Each scope button opens its own ephemeral follow-up; this View's
    job is dispatch, not state.
    """

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

    @discord.ui.button(label="Channel", style=discord.ButtonStyle.primary, row=0)
    async def channel_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.policy.channel_view import ChannelPolicySelectView

        await interaction.response.send_message(
            "Pick a channel to set its AI policy.",
            view=ChannelPolicySelectView(),
            ephemeral=True,
        )

    @discord.ui.button(label="Category", style=discord.ButtonStyle.primary, row=0)
    async def category_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.policy.category_view import CategoryPolicySelectView

        await interaction.response.send_message(
            "Pick a category to set its AI policy.",
            view=CategoryPolicySelectView(),
            ephemeral=True,
        )

    @discord.ui.button(label="Role", style=discord.ButtonStyle.primary, row=0)
    async def role_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.policy.role_view import RolePolicySelectView

        await interaction.response.send_message(
            "Pick a role to set its AI policy.",
            view=RolePolicySelectView(),
            ephemeral=True,
        )

    @discord.ui.button(
        label="List overrides",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def list_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.policy.list_view import (
            PolicyListView,
            build_list_embed,
            collect_entries,
        )

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Listing overrides requires a guild context.",
                ephemeral=True,
            )
            return
        entries = await collect_entries(interaction.guild.id)
        embed, _total = build_list_embed(entries, page=1)
        await interaction.response.send_message(
            embed=embed,
            view=PolicyListView(entries, page=1),
            ephemeral=True,
        )


__all__ = ["PolicyChooserView", "build_chooser_embed"]
