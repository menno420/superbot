"""Behavior chooser — the entry view of the Behavior UI (PR-C).

Top-level workflow dispatcher. Rows:

* Row 0: scope buttons ``Channel`` and ``Category``.
* Row 1: ``Preview`` (reuses PR4B :class:`PreviewChannelSelectView`)
  and ``Advanced`` (opens the PR4A policy chooser for raw edits).

The chooser is a **page of the one AI anchor message** (AI nav plan
PR 2): each button ``edit_message``-es the anchor to the next page
(scope picker / preview / advanced) with a Back button, instead of
spawning a new ephemeral. The chooser carries no persistent state and
times out.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.views.ai.behavior.chooser")

_PANEL_COLOR = discord.Color.blurple()
_CHOOSER_TIMEOUT_SECONDS = 180


def build_behavior_chooser_page() -> tuple[discord.Embed, BehaviorChooserView]:
    """Return the chooser ``(embed, view)`` — the Back target for its pages."""
    return build_behavior_embed(), BehaviorChooserView()


def build_behavior_embed() -> discord.Embed:
    """Behavior intro embed.

    Behavior-oriented copy: tells the operator what each scope+preset
    combination achieves, without exposing the underlying mode /
    min_level / cooldown knobs (those still live behind ``Advanced``).
    """
    embed = discord.Embed(
        title="AI Behavior",
        description=(
            "Pick **what the AI should do here**, then choose a scope. "
            "Presets bind together a channel mode plus an instruction "
            "profile. Use **Preview** to dry-run the resolver against "
            "your own user before saving. **Advanced** opens the raw "
            "policy editor."
        ),
        color=_PANEL_COLOR,
    )
    embed.add_field(
        name="Channel",
        value="Bind a preset to a single text channel.",
        inline=False,
    )
    embed.add_field(
        name="Category",
        value="Bind a preset to a category (applies to its channels).",
        inline=False,
    )
    embed.add_field(
        name="Preview (dry-run)",
        value=(
            "See the precedence trace the resolver would produce for "
            "your own user in a channel — no audit, no cooldown."
        ),
        inline=False,
    )
    embed.add_field(
        name="Routing matrix",
        value=(
            "Read-only diagnostic showing the dry-run resolver "
            "outcome for a channel — useful when an operator asks "
            "*why* a channel allows or denies."
        ),
        inline=False,
    )
    embed.add_field(
        name="Advanced",
        value=(
            "Open the raw policy editor (mode / min_level / cooldown / "
            "profile). Sentinel-safe: untouched fields are preserved."
        ),
        inline=False,
    )
    embed.set_footer(text="Administrator-only · ephemeral follow-up.")
    return embed


class BehaviorChooserView(discord.ui.View):
    """Ephemeral workflow dispatcher for the Behavior UI."""

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

    @discord.ui.button(
        label="Channel",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def channel_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.behavior.scope_picker import BehaviorChannelSelectView

        view = BehaviorChannelSelectView()
        _add_back_to_behavior(view)
        await interaction.response.edit_message(
            embed=_behavior_page_embed(
                "Behavior · channel",
                "Pick a channel — the next step lists the available presets.",
            ),
            view=view,
        )

    @discord.ui.button(
        label="Category",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def category_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.ai.behavior.scope_picker import BehaviorCategorySelectView

        view = BehaviorCategorySelectView()
        _add_back_to_behavior(view)
        await interaction.response.edit_message(
            embed=_behavior_page_embed(
                "Behavior · category",
                "Pick a category — the next step lists the available presets.",
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
        # Reuse PR4B's preview view — never re-implement the dry-run
        # path.
        from views.ai.policy.preview_view import PreviewChannelSelectView

        view = PreviewChannelSelectView()
        _add_back_to_behavior(view)
        await interaction.response.edit_message(
            embed=_behavior_page_embed(
                "Behavior · preview (dry-run)",
                "Pick a channel to preview the effective AI policy as your user.",
            ),
            view=view,
        )

    @discord.ui.button(
        label="Routing matrix",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def matrix_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # PR-G: read-only routing matrix. Operator picks a channel,
        # the resolver runs in dry-run mode.
        from views.ai.routing import RoutingMatrixSelectView

        view = RoutingMatrixSelectView()
        _add_back_to_behavior(view)
        await interaction.response.edit_message(
            embed=_behavior_page_embed(
                "Behavior · routing matrix",
                "Pick a channel to dry-run the AI routing matrix.",
            ),
            view=view,
        )

    @discord.ui.button(
        label="Advanced",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def advanced_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # Punt to the existing raw policy chooser (PR4A); the sentinel
        # PR-C-pre landed means partial edits there are now safe. Swap
        # the anchor to the policy chooser page in place.
        from views.ai.policy.chooser import build_policy_chooser_page

        embed, view = build_policy_chooser_page()
        await interaction.response.edit_message(embed=embed, view=view)


def _behavior_page_embed(title: str, instruction: str) -> discord.Embed:
    """A focused page embed for a Behavior sub-page rendered on the anchor."""
    return discord.Embed(
        title=title,
        description=instruction,
        color=_PANEL_COLOR,
    ).set_footer(text="Administrator-only · in-place navigation.")


def _add_back_to_behavior(view: discord.ui.View) -> None:
    """Attach a Back button that returns the anchor to the Behavior chooser."""
    from views.ai._nav import add_back_button

    add_back_button(view, label="↩ AI Behavior", builder=build_behavior_chooser_page)


__all__ = [
    "BehaviorChooserView",
    "build_behavior_chooser_page",
    "build_behavior_embed",
]
