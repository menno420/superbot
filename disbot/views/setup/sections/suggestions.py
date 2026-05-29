"""Smart-suggestions section — runs the deterministic advisor and shows recs.

Extracted from the previous `SetupHubView._suggestions` hardcoded button.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_session
from services.setup_sections import REGISTRY, SetupSection

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.suggestions")

SLUG = "suggestions"


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    del hub
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Smart suggestions require a guild context.",
            ephemeral=True,
        )
        return

    from services.guild_snapshot import collect as collect_snapshot
    from services.setup_plan import DeterministicAdvisor

    try:
        snapshot = await collect_snapshot(guild)
        draft = await DeterministicAdvisor().suggest(snapshot)
    except Exception:
        logger.exception("setup suggestions: advisor flow failed")
        await interaction.response.send_message(
            "Advisor failed. Try again later or run readiness for a "
            "deterministic baseline.",
            ephemeral=True,
        )
        return

    # Open the AI review panel so the operator can accept recommendations
    # and stage them into the draft via its "Stage & open Final review"
    # button — the section is no longer a read-only dead end.
    from views.setup.ai_review.main_panel import (
        AIReviewPanelView,
        build_ai_review_embed,
    )

    panel = AIReviewPanelView(interaction.user, draft=draft, snapshot=snapshot)
    await interaction.response.send_message(
        embed=build_ai_review_embed(draft),
        view=panel,
        ephemeral=True,
    )
    try:
        await setup_session.mark_in_progress(guild.id, step=SLUG)
    except Exception:
        logger.exception("setup suggestions: mark_in_progress failed")


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Smart suggestions",
        style=discord.ButtonStyle.success,
        run=run,
        order=20,
        depths=frozenset({"advanced"}),
    ),
)


__all__ = ["SLUG", "run"]
