"""Modals for the Paragon calculator: forward inputs and target degree.

The forward modal stays within Discord's 5-text-input limit — paragon,
players, difficulty, and extra-T5 count are selects on the parent view, not
modal fields.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_followup
from services import paragon_service
from services.paragon_service import ParagonServiceError
from utils.btd6.paragon_math import ParagonInputs
from views.btd6.paragon_view import (
    ParagonCalculatorView,
    ParagonRequirementsView,
    build_error_embed,
    build_requirement_embed,
    build_result_embed,
)


def _parse_int(
    raw: str,
    *,
    field: str,
    minimum: int = 0,
    maximum: int | None = None,
) -> int:
    cleaned = raw.strip().replace(",", "").replace("$", "").replace(" ", "")
    if cleaned == "":
        if minimum > 0:
            raise ValueError(f"{field} is required.")
        return 0
    try:
        value = int(cleaned)
    except ValueError:
        raise ValueError(f"{field} must be a whole number.") from None
    if value < minimum:
        raise ValueError(f"{field} must be at least {minimum}.")
    if maximum is not None and value > maximum:
        raise ValueError(f"{field} must be at most {maximum}.")
    return value


class ParagonForwardModal(discord.ui.Modal, title="Paragon — enter your numbers"):
    """Collect the five numeric inputs for a forward calculation."""

    pops = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Pops (total damage)",
        placeholder="e.g. 8000000",
        required=False,
        max_length=15,
    )
    cash_spent = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Cash spent (non-T5 towers)",
        placeholder="e.g. 150000",
        required=False,
        max_length=12,
    )
    slider_cash = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Slider cash",
        placeholder="e.g. 0",
        required=False,
        max_length=12,
    )
    upgrade_count = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Upgrade tiers (a 0-2-4 tower = 6)",
        placeholder="e.g. 60",
        required=False,
        max_length=4,
    )
    geraldo_totems = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Geraldo totems",
        placeholder="e.g. 0",
        required=False,
        max_length=4,
    )

    def __init__(self, parent: ParagonCalculatorView) -> None:
        super().__init__()
        self._parent = parent

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            pops = _parse_int(self.pops.value, field="Pops")
            cash = _parse_int(self.cash_spent.value, field="Cash spent")
            slider = _parse_int(self.slider_cash.value, field="Slider cash")
            upgrades = _parse_int(self.upgrade_count.value, field="Upgrade tiers")
            totems = _parse_int(self.geraldo_totems.value, field="Geraldo totems")
        except ValueError as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return

        if not await safe_defer(interaction, ephemeral=True):
            return
        inputs = ParagonInputs(
            tower=self._parent.paragon_id,
            pops=pops,
            cash_spent=cash,
            slider_cash=slider,
            upgrade_count=upgrades,
            tier5_count=self._parent.tier5_count,
            geraldo_totems=totems,
            player_count=self._parent.player_count,
            difficulty=self._parent.difficulty,
        )
        try:
            result = await paragon_service.calculate(inputs)
        except ParagonServiceError as exc:
            await safe_followup(
                interaction,
                embed=build_error_embed(exc),
                ephemeral=True,
            )
            return
        await safe_followup(
            interaction,
            embed=build_result_embed(result),
            ephemeral=True,
        )


class ParagonTargetModal(discord.ui.Modal, title="Paragon — target degree"):
    """Collect the target degree for a reverse solve."""

    target = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Target degree (1-100)",
        placeholder="e.g. 90",
        max_length=3,
    )

    def __init__(self, parent: ParagonRequirementsView) -> None:
        super().__init__()
        self._parent = parent

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            target = _parse_int(
                self.target.value,
                field="Target degree",
                minimum=1,
                maximum=100,
            )
        except ValueError as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return

        if not await safe_defer(interaction, ephemeral=True):
            return
        try:
            req = await paragon_service.requirements(
                target,
                self._parent.paragon_id,
                strategy=self._parent.strategy,
                player_count=self._parent.player_count,
                difficulty=self._parent.difficulty,
            )
        except ParagonServiceError as exc:
            await safe_followup(
                interaction,
                embed=build_error_embed(exc),
                ephemeral=True,
            )
            return
        await safe_followup(
            interaction,
            embed=build_requirement_embed(req),
            ephemeral=True,
        )


__all__ = ["ParagonForwardModal", "ParagonTargetModal"]
