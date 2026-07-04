"""Entry-point chooser for the AI policy admin UI (PR4A).

Reached from the main :class:`views.ai.panel.AIPanelView` ``Policy``
button. The chooser is a **page of the one anchor message** (AI nav
plan PR 2): the Policy button ``edit_message``-es the anchor to this
chooser, and each scope button (Channel / Category / Role / Effective
policy / List) ``edit_message``-es the anchor to that scope's picker —
navigation happens in place on the same message, with a Back button
unwinding the page stack. Ephemerals are reserved for the modal
confirmations / errors the scope pickers raise.

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


def build_policy_chooser_page() -> tuple[discord.Embed, PolicyChooserView]:
    """Return the chooser ``(embed, view)`` — the Back target for scope pages."""
    return build_chooser_embed(), PolicyChooserView()


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
        from views.ai._nav import add_back_button, ai_home_page

        add_back_button(self, label="↩ AI home", builder=ai_home_page)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Canonical admin gate — honours the platform owner (Q-0212).
        from views.base import interaction_is_admin

        if not interaction_is_admin(interaction):
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

        view = ChannelPolicySelectView()
        _add_back_to_policy(view)
        await interaction.response.edit_message(
            embed=_scope_page_embed(
                "Channel AI policy",
                "Pick a channel to set its AI policy.",
            ),
            view=view,
        )

    @discord.ui.button(label="Category", style=discord.ButtonStyle.primary, row=0)
    async def category_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.policy.category_view import CategoryPolicySelectView

        view = CategoryPolicySelectView()
        _add_back_to_policy(view)
        await interaction.response.edit_message(
            embed=_scope_page_embed(
                "Category AI policy",
                "Pick a category to set its AI policy.",
            ),
            view=view,
        )

    @discord.ui.button(label="Role", style=discord.ButtonStyle.primary, row=0)
    async def role_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.policy.role_view import RolePolicySelectView

        view = RolePolicySelectView()
        _add_back_to_policy(view)
        await interaction.response.edit_message(
            embed=_scope_page_embed(
                "Role AI policy",
                "Pick a role to set its AI policy.",
            ),
            view=view,
        )

    @discord.ui.button(
        label="Effective policy",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def preview_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # PR-2: open the dry-run preview channel picker. The resolver
        # runs in dry_run mode so cooldown / audit are untouched. Same
        # underlying view as before — only the button label changed; the
        # callback name (preview_btn) is its custom_id contract.
        from views.ai.policy.preview_view import PreviewChannelSelectView

        view = PreviewChannelSelectView()
        _add_back_to_policy(view)
        await interaction.response.edit_message(
            embed=_scope_page_embed(
                "Effective AI policy (dry-run)",
                "Pick a channel to see the effective AI policy as your user.",
            ),
            view=view,
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
            # Genuine validation error → ephemeral toast (reserved use).
            await interaction.response.send_message(
                "❌ Listing overrides requires a guild context.",
                ephemeral=True,
            )
            return
        entries = await collect_entries(interaction.guild.id)
        embed, _total = build_list_embed(entries, page=1)
        view = PolicyListView(entries, page=1)
        _add_back_to_policy(view)
        await interaction.response.edit_message(embed=embed, view=view)


def _scope_page_embed(title: str, instruction: str) -> discord.Embed:
    """A focused page embed for a policy scope picker rendered on the anchor."""
    return discord.Embed(
        title=title,
        description=instruction,
        color=_PANEL_COLOR,
    ).set_footer(text="Administrator-only · in-place navigation.")


def _add_back_to_policy(view: discord.ui.View) -> None:
    """Attach a Back button that returns the anchor to the policy chooser."""
    from views.ai._nav import add_back_button

    add_back_button(view, label="↩ AI Policy", builder=build_policy_chooser_page)


__all__ = ["PolicyChooserView", "build_chooser_embed", "build_policy_chooser_page"]
