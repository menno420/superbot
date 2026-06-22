"""The treasury panel — the interactive server-pool hub.

One author-restricted :class:`HubView` (mirrors the farm hub,
``views/farm/menu.py``):

* **🏛️ Treasury panel** — shows the guild pool balance and the member's own
  wallet. **➕ Contribute** opens a one-field modal to donate coins into the
  pool; **🔄 Refresh** re-reads and redraws.

Disbursing *from* the pool is intentionally **not** a panel button — it is a
``manage_guild``-gated command (``!treasury grant``), so an ordinary member's
panel can only ever move their *own* coins in, never the server's coins out.

Reached from ``!treasury``, the Help hub (``TreasuryCog.build_help_menu_view``),
and the Economy hub. Each action re-reads the live state and redraws in place.
"""

from __future__ import annotations

import discord

from services import treasury_service
from utils import db
from utils.ui_constants import ECONOMY_COLOR
from views.base import HubView


def build_treasury_embed(treasury_balance: int, wallet: int) -> discord.Embed:
    """The treasury-panel embed — the shared pool plus the viewer's wallet."""
    embed = discord.Embed(
        title="🏛️ Server Treasury",
        description=(
            "The server's shared coin pool. Everyone can **Contribute** their "
            "own coins to grow it; server managers disburse from it with "
            "`!treasury grant @member <amount>`."
        ),
        color=ECONOMY_COLOR,
    )
    embed.add_field(
        name="Treasury",
        value=f"🏛️ **{treasury_balance}** 🪙 in the pool",
        inline=True,
    )
    embed.add_field(
        name="Your wallet",
        value=f"🪙 **{wallet}** 🪙",
        inline=True,
    )
    embed.set_footer(text="➕ Contribute · 🔄 Refresh")
    return embed


async def _panel_data(user_id: int, guild_id: int) -> tuple[int, int]:
    """Read ``(treasury_balance, wallet)`` for a draw/redraw."""
    treasury_balance = await treasury_service.get_balance(guild_id)
    wallet = await db.get_coins(user_id, guild_id)
    return treasury_balance, wallet


async def open_treasury_panel(
    user: discord.Member | discord.User,
    guild_id: int,
) -> tuple[discord.Embed, TreasuryView]:
    """Build the treasury panel ``(embed, view)`` for *user* in *guild_id*.

    The one entry point shared by ``!treasury``, the Help hook, and the Economy
    hub, so none of them duplicate the read-then-build sequence.
    """
    treasury_balance, wallet = await _panel_data(user.id, guild_id)
    return (
        build_treasury_embed(treasury_balance, wallet),
        TreasuryView(user, guild_id),
    )


class TreasuryView(HubView):
    """The treasury panel (Contribute · Refresh)."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
    ) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    async def _redraw(
        self,
        interaction: discord.Interaction,
        flash: str | None,
    ) -> None:
        treasury_balance, wallet = await _panel_data(self._author.id, self.guild_id)
        # Redraw onto a fresh view so the panel's timeout clock resets on every
        # interaction (mirrors the farm hub).
        view = TreasuryView(self._author, self.guild_id)
        embed = build_treasury_embed(treasury_balance, wallet)
        if flash:
            embed.description = f"{flash}\n\n{embed.description}"
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message

    @discord.ui.button(
        label="Contribute",
        emoji="➕",
        style=discord.ButtonStyle.success,
    )
    async def contribute_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(_ContributeModal(self))

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary)
    async def refresh_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._redraw(interaction, None)


class _ContributeModal(discord.ui.Modal, title="Contribute to the treasury"):
    """A single-field modal capturing how many coins to donate."""

    amount_input: discord.ui.TextInput = discord.ui.TextInput(
        label="Amount (coins)",
        placeholder="e.g. 100",
        required=True,
        max_length=12,
    )

    def __init__(self, panel: TreasuryView) -> None:
        super().__init__()
        self._panel = panel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw = (self.amount_input.value or "").strip()
        try:
            amount = int(raw)
        except ValueError:
            await interaction.response.send_message(
                f"❌ `{raw}` is not a whole number of coins.",
                ephemeral=True,
            )
            return
        if amount <= 0:
            await interaction.response.send_message(
                "❌ Contribute a positive number of coins.",
                ephemeral=True,
            )
            return
        result = await treasury_service.contribute(
            self._panel.guild_id,
            self._panel._author.id,
            amount,
        )
        await self._panel._redraw(interaction, result.message)
