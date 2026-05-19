"""Ephemeral shop sub-panels.

``_ShopView``      — standalone (used by !shop prefix command).
``_ShopSubView``   — wrapped in the economy panel flow with a Back button.
``_ShopSelect`` / ``_ShopPanelSelect`` — the item-picker dropdowns
(one each for the two contexts; both perform an audited debit through
``services.economy_service`` and persist the inventory write).
"""

from __future__ import annotations

import discord

from cogs.economy._helpers import SHOP_ITEMS, _build_economy_embed
from services import economy_service
from utils import db
from utils.helpers import post_log_embed
from utils.ui_constants import SUCCESS_COLOR, WARNING_COLOR


class _ShopView(discord.ui.View):
    def __init__(self, user_id: int, guild_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.guild_id = guild_id
        self.message: discord.Message | None = None
        options = [
            discord.SelectOption(
                label=f"{d['emoji']} {name.replace('_', ' ').title()} — {d['price']:,} 🪙",
                value=name,
                description=d["desc"],
            )
            for name, d in SHOP_ITEMS.items()
        ]
        self.add_item(_ShopSelect(user_id, guild_id, options, self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This shop isn't for you.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass


class _ShopSelect(discord.ui.Select):
    def __init__(self, user_id: int, guild_id: int, options, view: _ShopView):
        self._user_id = user_id
        self._guild_id = guild_id
        self._shop_view = view
        super().__init__(
            placeholder="Select an item to buy…",
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        item_name = self.values[0]
        uid, gid = self._user_id, self._guild_id
        data = SHOP_ITEMS[item_name]

        if await db.has_item(uid, gid, item_name):
            await interaction.response.send_message(
                f"You already own a **{item_name}**!",
                ephemeral=True,
            )
            return

        bal = await db.get_coins(uid, gid)
        if bal < data["price"]:
            await interaction.response.send_message(
                f"❌ Need **{data['price']:,}** 🪙 — you only have **{bal:,}** 🪙.",
                ephemeral=True,
            )
            return

        new_bal = await economy_service.debit(
            gid,
            uid,
            data["price"],
            reason=f"shop:{item_name}",
            actor_id=uid,
        )
        await db.add_item(uid, gid, item_name)

        embed = discord.Embed(
            title=f"✅ Purchased: {data['emoji']} {item_name.replace('_', ' ').title()}",
            description=f"**-{data['price']:,}** 🪙  |  New balance: **{new_bal:,}** 🪙",
            color=SUCCESS_COLOR,
        )
        await interaction.response.send_message(embed=embed)

        log_embed = discord.Embed(
            title="🛒 Shop Purchase",
            description=(
                f"{interaction.user.mention} bought "
                f"**{data['emoji']} {item_name.replace('_', ' ').title()}** "
                f"for **{data['price']:,}** 🪙"
            ),
            color=WARNING_COLOR,
        )
        await post_log_embed(interaction.client, gid, log_embed)


class _ShopSubView(discord.ui.View):
    """Shop sub-panel that edits the economy panel message — includes Back."""

    def __init__(self, user_id: int, guild_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.guild_id = guild_id
        self.message: discord.Message | None = None
        options = [
            discord.SelectOption(
                label=f"{d['emoji']} {name.replace('_', ' ').title()} — {d['price']:,} 🪙",
                value=name,
                description=d["desc"],
            )
            for name, d in SHOP_ITEMS.items()
        ]
        self.add_item(_ShopPanelSelect(user_id, guild_id, options, self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This panel isn't for you.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="↩ Back", style=discord.ButtonStyle.grey, row=1)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        from views.economy.main_panel import EconomyPanelView
        from views.navigation import attach_back_target

        embed = await _build_economy_embed(interaction.user, interaction.guild_id)
        view = EconomyPanelView()
        # AB2: if a grandparent was propagated from the opener
        # (typically Help's back target), re-attach it so the rebuilt
        # Economy panel keeps the back-to-Help chain.
        origin = getattr(self, "_back_target", None)
        if origin is not None:
            attach_back_target(view, origin)
        await interaction.response.edit_message(embed=embed, view=view)
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


class _ShopPanelSelect(discord.ui.Select):
    """Shop select that updates in-place within the economy panel flow."""

    def __init__(self, user_id: int, guild_id: int, options, view: _ShopSubView):
        self._user_id = user_id
        self._guild_id = guild_id
        self._shop_view = view
        super().__init__(placeholder="Select an item to buy…", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        item_name = self.values[0]
        uid, gid = self._user_id, self._guild_id
        data = SHOP_ITEMS[item_name]

        if await db.has_item(uid, gid, item_name):
            await interaction.response.send_message(
                f"You already own a **{item_name}**!",
                ephemeral=True,
            )
            return

        bal = await db.get_coins(uid, gid)
        if bal < data["price"]:
            await interaction.response.send_message(
                f"❌ Need **{data['price']:,}** 🪙 — you only have **{bal:,}** 🪙.",
                ephemeral=True,
            )
            return

        new_bal = await economy_service.debit(
            gid,
            uid,
            data["price"],
            reason=f"shop:{item_name}",
            actor_id=uid,
        )
        await db.add_item(uid, gid, item_name)

        embed = discord.Embed(
            title=f"✅ Purchased: {data['emoji']} {item_name.replace('_', ' ').title()}",
            description=(
                f"**-{data['price']:,}** 🪙  |  New balance: **{new_bal:,}** 🪙\n\n"
                "Click **↩ Back** to return to the economy panel."
            ),
            color=SUCCESS_COLOR,
        )
        await interaction.response.edit_message(embed=embed, view=self._shop_view)

        log_embed = discord.Embed(
            title="🛒 Shop Purchase",
            description=(
                f"{interaction.user.mention} bought "
                f"**{data['emoji']} {item_name.replace('_', ' ').title()}** "
                f"for **{data['price']:,}** 🪙"
            ),
            color=WARNING_COLOR,
        )
        await post_log_embed(interaction.client, gid, log_embed)
