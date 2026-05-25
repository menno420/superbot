"""Strategy submission modal (PR-F).

A minimal modal that captures the three required fields (title,
summary, optional map/mode) and forwards to
``services.btd6_strategy_mutation.submit_strategy``. The full
strategy payload (towers / upgrade paths / steps / round_range /
failures / source links / origin metadata) is intentionally NOT in
the modal — Discord modals cap at 5 text inputs and the heavier
fields belong on a follow-up form. PR-F ships the minimum
operator-viable path; richer authoring can come later.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

logger = logging.getLogger("bot.views.btd6.strategy_submit")


class StrategySubmitModal(discord.ui.Modal, title="Submit BTD6 strategy"):
    title_input: discord.ui.TextInput = discord.ui.TextInput(
        label="Title",
        placeholder="e.g. CHIMPS Bloody Puddles 4-2-0 Super Monkey",
        required=True,
        max_length=100,
    )
    summary_input: discord.ui.TextInput = discord.ui.TextInput(
        label="Summary",
        placeholder="Short pitch — when and why this strategy works.",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=500,
    )
    map_input: discord.ui.TextInput = discord.ui.TextInput(
        label="Map (optional)",
        placeholder="e.g. Bloody Puddles",
        required=False,
        max_length=80,
    )
    mode_input: discord.ui.TextInput = discord.ui.TextInput(
        label="Mode (optional)",
        placeholder="e.g. CHIMPS",
        required=False,
        max_length=40,
    )
    hero_input: discord.ui.TextInput = discord.ui.TextInput(
        label="Hero (optional)",
        placeholder="e.g. Geraldo",
        required=False,
        max_length=40,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        from services.btd6_strategy_mutation import (
            InvalidStrategyValueError,
            submit_strategy,
        )

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Submitting a strategy requires a guild context.",
                ephemeral=True,
            )
            return
        title = (self.title_input.value or "").strip()
        summary = (self.summary_input.value or "").strip()
        map_name = (self.map_input.value or "").strip() or None
        mode = (self.mode_input.value or "").strip() or None
        hero = (self.hero_input.value or "").strip() or None

        try:
            result = await submit_strategy(
                origin_guild_id=interaction.guild.id,
                submitter=interaction.user,
                title=title,
                summary=summary,
                map_name=map_name,
                mode=mode,
                hero=hero,
            )
        except InvalidStrategyValueError as exc:
            await interaction.response.send_message(
                f"❌ {exc}",
                ephemeral=True,
            )
            return
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.exception(
                "StrategySubmitModal: submission failed for guild=%s",
                interaction.guild.id,
            )
            await interaction.response.send_message(
                f"❌ Unexpected error: {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ Submitted as strategy `#{result.strategy_id}` "
            f"(`{result.action}`). Staff can review with `!btd6 pending`.",
            ephemeral=True,
        )


__all__ = ["StrategySubmitModal"]


# ``submitted_by`` is set on the strategy row via submit_strategy's
# inspection of ``submitter.id`` — that already happens inside the
# mutation chokepoint, so no extra wiring is needed here.

def _has_user_id(actor: Any) -> bool:  # pragma: no cover - tiny shim
    return getattr(actor, "id", None) is not None
