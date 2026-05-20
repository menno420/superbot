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

_REVIEW_HEADER = "Smart suggestions are recommendations. Review before applying."


def _build_suggestions_embed(draft) -> discord.Embed:
    if not getattr(draft, "recommendations", ()):
        return discord.Embed(
            title="🤖 Smart suggestions",
            description=(
                "The deterministic advisor produced no recommendations "
                "for this guild. Either every binding is already "
                "configured or the channel/category names did not "
                "match the rule table."
            ),
            color=discord.Color.dark_grey(),
        )
    embed = discord.Embed(
        title="🤖 Smart suggestions",
        description=(
            f"_{_REVIEW_HEADER}_\n\n"
            f"**{len(draft.recommendations)}** recommendation(s) — "
            "open **Final review** to apply the high-confidence ones."
        ),
        color=discord.Color.blurple(),
    )
    lines = [
        f"• `{rec.subsystem}.{rec.binding_name}` → "
        f"`{rec.target_name}` ({rec.confidence})"
        for rec in draft.recommendations
    ]
    value = "\n".join(lines)
    if len(value) > 1000:
        value = value[:997] + "..."
    embed.add_field(name="Recommendations", value=value, inline=False)
    return embed


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
        logger.exception("setup hub: advisor flow failed")
        await interaction.response.send_message(
            "Advisor failed. Try again later or run readiness for a "
            "deterministic baseline.",
            ephemeral=True,
        )
        return

    embed = _build_suggestions_embed(draft)
    await interaction.response.send_message(embed=embed, ephemeral=True)
    try:
        await setup_session.mark_in_progress(guild.id, step=SLUG)
    except Exception:
        logger.exception("setup hub: mark_in_progress failed")


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Smart suggestions",
        style=discord.ButtonStyle.success,
        run=run,
        order=20,
    ),
)


__all__ = ["SLUG", "run"]
