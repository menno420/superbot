"""BTD6 setup section — announce the BTD6 assistant during setup.

Read-only for Module 4: the assistant has no per-guild settings
yet, so this section simply confirms BTD6 is loaded and points the
operator at the panel command. Module 6 will extend this section
when guild settings (channels, mention behaviour, AI augmentation
toggle) come online.

The section registers itself at import time via
:data:`services.setup_sections.REGISTRY`, matching the convention
of every other section.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services.setup_sections import REGISTRY, SetupSection

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.btd6")

SLUG = "btd6"


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    del hub
    from services import btd6_knowledge_service

    embed = discord.Embed(
        title="🐵 BTD6 Assistant",
        description=(
            "BTD6 assistant is loaded and reachable via `!btd6` / `/btd6`. "
            "The assistant answers deterministic tower/round/hero/map/mode "
            "questions from the pinned game-data fixtures.\n\n"
            "Per-server settings (channel routing, mention behaviour, AI "
            "augmentation toggle) are not yet exposed in setup — they land "
            "with Module 6 of the AI/BTD6 plan."
        ),
        color=discord.Color.green(),
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
    embed.set_footer(text="!btd6 status / !btd6 ask <question> / !btd6menu")
    await interaction.response.send_message(embed=embed, ephemeral=True)


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="BTD6 Assistant",
        style=discord.ButtonStyle.secondary,
        run=run,
        order=80,
        # No SetupOperation kinds — the section is announcement-only in
        # Module 4. Module 6 swaps this for the real op-kind set when
        # per-guild BTD6 settings land.
        op_kinds=frozenset(),
        description_if_skipped="BTD6 commands remain available; defaults apply.",
        depths=frozenset({"standard", "advanced"}),
    ),
)


__all__ = ["SLUG", "run"]
