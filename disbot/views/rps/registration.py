"""Tournament-registration "Join" button view.

Sent into a channel by ``RPSTournamentCog.start_registration``.  The
view's lifetime is the registration window (timeout=None — the cog
disables it explicitly when the window closes).
"""

from __future__ import annotations

import discord

from utils import db as global_db


class _RpsRegistrationView(discord.ui.View):
    def __init__(self, cog) -> None:
        super().__init__(timeout=None)  # lives until tournament starts
        self.cog = cog

    @discord.ui.button(
        label="Join Tournament",
        style=discord.ButtonStyle.green,
        emoji="✅",
    )
    async def join_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        cog = self.cog
        if not cog.registration_active:
            await interaction.response.send_message(
                "Registration is no longer open.",
                ephemeral=True,
            )
            return
        guild_id = interaction.guild_id or 0
        ok = await cog.try_register_player(interaction.user, guild_id)
        if ok:
            await interaction.response.send_message(
                f"✅ Registered! ({len(cog.players)} player(s) so far)",
                ephemeral=True,
            )
        else:
            bal = await global_db.get_coins(interaction.user.id, guild_id)
            if cog.entry_fee > 0 and bal < cog.entry_fee:
                await interaction.response.send_message(
                    f"❌ Need **{cog.entry_fee}** 🪙 to enter (you have {bal}).",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "You're already registered!",
                    ephemeral=True,
                )
