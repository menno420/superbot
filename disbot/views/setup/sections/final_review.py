"""Final-review section — loads the per-guild draft and hands it
to :class:`views.setup.final_review.FinalReviewView` for apply.

The section is the sole apply gate for the wizard's draft-first
flow.  It reads :mod:`services.setup_draft` for the staged
SetupOperations and constructs the view in ``ops=`` mode; the view
applies in canonical phase order on click and clears the draft on
success.
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
    from services import setup_draft
    from views.setup.final_review import FinalReviewView, build_final_review_embed

    guild = interaction.guild
    ops: list = []
    if guild is not None:
        try:
            ops = await setup_draft.list_ops(guild.id)
        except Exception:
            logger.exception("final_review: setup_draft.list_ops failed")
            ops = []

    final = FinalReviewView(interaction.user, ops=ops)
    await interaction.response.send_message(
        embed=build_final_review_embed(final.ops),
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
