"""Ephemeral move-picker for PvP matches.

Sent only to the picker so the opponent doesn't see the move until
resolution.  Records the pick back on the parent ``_RpsPvpPlayView``.
"""

from __future__ import annotations

import discord


class _RpsMovePickerView(discord.ui.View):
    """Ephemeral view for picking a move in PvP."""

    def __init__(self, user_id: int, parent) -> None:
        super().__init__(timeout=55)
        self.user_id = user_id
        self.parent = parent

    @discord.ui.button(label="Rock", emoji="🪨", style=discord.ButtonStyle.grey)
    async def rock(self, i: discord.Interaction, _):
        await self._pick(i, "rock")

    @discord.ui.button(label="Paper", emoji="📄", style=discord.ButtonStyle.grey)
    async def paper(self, i: discord.Interaction, _):
        await self._pick(i, "paper")

    @discord.ui.button(label="Scissors", emoji="✂️", style=discord.ButtonStyle.grey)
    async def scissors(self, i: discord.Interaction, _):
        await self._pick(i, "scissors")

    async def _pick(self, interaction: discord.Interaction, move: str):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content=f"You chose **{move}** — waiting for opponent…",
            view=self,
        )
        self.stop()
        await self.parent.record_choice(self.user_id, move)
