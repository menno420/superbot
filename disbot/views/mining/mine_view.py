"""!mine button view — extracted from ``cogs/mining_cog.py`` (S4.1).

A 30-second ephemeral view with three Mine Left/Right/Down buttons.
On click, rolls loot via ``cogs.mining.rewards.roll_mine_loot`` and
updates the user's mining inventory via the shared DB helper.

Decoupled from the cog: the previous nested ``MiningCog.MineView``
called ``self.cog.update_inventory(...)`` which routed to
``db.update_mining_item``.  The extracted view skips the cog round-
trip and calls the DB primitive directly so it has no cog dependency
and can be unit-tested without a Discord mock.
"""

from __future__ import annotations

import discord

from cogs.mining.rewards import roll_mine_loot
from core.runtime.interaction_helpers import safe_defer
from utils import db


class MineView(discord.ui.View):
    """Mine Left / Mine Right / Mine Down buttons (30-second timeout)."""

    def __init__(self, user_id: int, guild_id: int) -> None:
        super().__init__(timeout=30)
        self.user_id = user_id
        self.guild_id = guild_id
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Mine Left", style=discord.ButtonStyle.primary)
    async def mine_left(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self._handle_mine(interaction, "left")

    @discord.ui.button(label="Mine Right", style=discord.ButtonStyle.primary)
    async def mine_right(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self._handle_mine(interaction, "right")

    @discord.ui.button(label="Mine Down", style=discord.ButtonStyle.primary)
    async def mine_down(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self._handle_mine(interaction, "down")

    async def _handle_mine(
        self,
        interaction: discord.Interaction,
        direction: str,
    ) -> None:
        if not await safe_defer(interaction):
            return

        user_id = str(self.user_id)
        inventory = await db.get_mining_inventory(user_id, self.guild_id)
        has_pickaxe = inventory.get("pickaxe", 0) > 0
        found, amount = roll_mine_loot(has_pickaxe=has_pickaxe)

        await db.update_mining_item(user_id, self.guild_id, found, amount)

        new_content = (
            f"{interaction.user.mention} mined {amount}x **{found}** "
            f"by going {direction}!"
        )
        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            content=new_content,
            embed=None,
            view=None,
        )
        self.stop()
