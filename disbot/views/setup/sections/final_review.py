"""Final-review section — opens the FinalReviewView to apply accepted ops.

Extracted from the previous `SetupHubView._final_review` hardcoded button.
The actual apply path still lives in `views.setup.final_review.FinalReviewView`,
which routes through `services.setup_operations.apply_operations`.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services.setup_sections import REGISTRY, SetupSection

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.final_review")

SLUG = "final_review"


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    del hub
    from views.setup.final_review import FinalReviewView, build_final_review_embed

    final = FinalReviewView(interaction.user, accepted=[])
    await interaction.response.send_message(
        embed=build_final_review_embed(final.accepted),
        view=final,
        ephemeral=True,
    )


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Final review",
        style=discord.ButtonStyle.secondary,
        run=run,
        order=90,
    ),
)


__all__ = ["SLUG", "run"]
