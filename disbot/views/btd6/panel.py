"""BTD6 persistent panel — Module 4 of the AI/BTD6 plan.

The view lives under ``views/btd6/`` (Pattern B) so the cog file
stays small. Importing this module triggers the ``@register``
decorator side-effect on :class:`BTD6PanelView`; the persistent
view registry then resolves the ``btd6`` subsystem when
``on_ready`` restores anchors.

The panel is read-only and entirely deterministic: every button
renders an embed built from the validated fixtures in
:mod:`services.btd6_data_service`. No provider, no network, no AI.
Module 5 will add an optional augmentation toggle gated by guild
config.
"""

from __future__ import annotations

import discord

from core.runtime.persistent_views import PersistentView, register
from services import btd6_ai_service, btd6_knowledge_service

_PANEL_COLOR = discord.Color.green()


class BTD6AskModal(discord.ui.Modal, title="Ask BTD6 Assistant"):
    """Modal that takes a free-form BTD6 question and renders a deterministic answer."""

    question: discord.ui.TextInput = discord.ui.TextInput(
        label="Your question",
        placeholder="e.g. how do I survive round 63?",
        max_length=300,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        from cogs.btd6_cog import _response_to_embed

        response = await btd6_ai_service.answer_question(str(self.question.value))
        await interaction.response.send_message(
            embed=_response_to_embed(response),
            ephemeral=True,
        )


def build_btd6_panel_embed() -> discord.Embed:
    """Deterministic BTD6 panel embed.

    Pulls the dataset version + game version so operators can see at
    a glance which patch the assistant is pinned to.
    """
    embed = discord.Embed(
        title="🐵 BTD6 Assistant",
        description=(
            "Ask deterministic BTD6 questions. The buttons below render "
            "tower / round / mode lookups from the pinned fixtures."
        ),
        color=_PANEL_COLOR,
    )
    embed.add_field(
        name="Data version",
        value=btd6_knowledge_service.data_version(),
        inline=True,
    )
    embed.add_field(
        name="Game version",
        value=btd6_knowledge_service.game_version(),
        inline=True,
    )
    embed.add_field(
        name="Entities",
        value=(
            f"{len(btd6_knowledge_service.list_towers())} towers • "
            f"{len(btd6_knowledge_service.list_heroes())} heroes • "
            f"{len(btd6_knowledge_service.list_maps())} maps • "
            f"{len(btd6_knowledge_service.list_modes())} modes • "
            f"{len(btd6_knowledge_service.list_rounds())} rounds"
        ),
        inline=False,
    )
    embed.set_footer(
        text="!btd6 ask <q> / !btd6 tower <n> / !btd6 round <N> / !btd6 status",
    )
    return embed


@register
class BTD6PanelView(PersistentView):
    """BTD6 Assistant panel. Anyone can interact."""

    SUBSYSTEM = "btd6"

    @discord.ui.button(
        label="Ask",
        style=discord.ButtonStyle.success,
        row=0,
        custom_id="btd6:ask",
    )
    async def ask_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        """Open the Ask modal — the actionable entry point for the panel."""
        await interaction.response.send_modal(BTD6AskModal())

    @discord.ui.button(
        label="Refresh",
        style=discord.ButtonStyle.secondary,
        row=0,
        custom_id="btd6:refresh",
    )
    async def refresh_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=build_btd6_panel_embed(),
            view=self,
        )

    @discord.ui.button(
        label="Towers",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="btd6:towers",
    )
    async def towers_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from cogs.btd6_cog import build_towers_embed

        await interaction.response.edit_message(
            embed=build_towers_embed(),
            view=self,
        )

    @discord.ui.button(
        label="Modes",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="btd6:modes",
    )
    async def modes_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from cogs.btd6_cog import build_modes_embed

        await interaction.response.edit_message(
            embed=build_modes_embed(),
            view=self,
        )

    @discord.ui.button(
        label="Status",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="btd6:status",
    )
    async def status_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from cogs.btd6_cog import build_status_embed

        await interaction.response.edit_message(
            embed=build_status_embed(),
            view=self,
        )
