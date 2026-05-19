"""Mining hub PersistentView + Build modal — extracted from ``cogs/mining_cog.py``.

Pattern B placement per ``docs/architecture.md`` §"PersistentView
placement": the view lives in views/ and the cog re-exports for the
persistent-view registry side-effect.

The Mine button opens a fresh ephemeral ``MineView`` from
``views.mining.mine_view``.  Harvest / Explore / Inventory / Stats
buttons call DB helpers directly — no cog round-trip needed.  The
Build button opens ``_BuildModal`` which loads the current recipes
list and validates the user's inventory.
"""

from __future__ import annotations

import discord

from cogs.mining.recipes import load_recipes
from cogs.mining.rewards import roll_explore_outcome, roll_harvest_amount
from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from core.runtime.persistent_views import PersistentView, register
from utils import db
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.mining.mine_view import MineView, _build_mine_prompt_embed


@register
class MiningHubView(PersistentView):
    """Persistent, stateless mining hub panel."""

    SUBSYSTEM = "mining"

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="⛏️ Mining Hub",
            description=(
                "**⛏️ Mine** — start a mining session\n"
                "**🌲 Harvest** — chop wood\n"
                "**🗺️ Explore** — discover random events\n"
                "**📦 Inventory** — view your mining resources\n"
                "**📊 Stats** — view your mining statistics\n"
                "**🔨 Build** — craft a structure"
            ),
            color=MINING_COLOR,
        )
        embed.set_footer(text="Only you can interact with this panel.")
        return embed

    @discord.ui.button(
        label="⛏️ Mine",
        style=discord.ButtonStyle.primary,
        custom_id="mining:mine",
        row=0,
    )
    async def mine_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.guild_id is None:
            await safe_followup(
                interaction,
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        view = MineView(interaction.user.id, interaction.guild_id)
        await interaction.response.edit_message(
            embed=_build_mine_prompt_embed(),
            view=view,
        )
        view.message = interaction.message

    @discord.ui.button(
        label="🌲 Harvest",
        style=discord.ButtonStyle.primary,
        custom_id="mining:harvest",
        row=0,
    )
    async def harvest_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        if interaction.guild_id is None:
            await safe_followup(
                interaction,
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        user_id = str(interaction.user.id)
        gid = interaction.guild_id
        inventory = await db.get_mining_inventory(user_id, gid)
        wood_amount = roll_harvest_amount(has_axe=inventory.get("axe", 0) > 0)
        await db.update_mining_item(user_id, gid, "wood", wood_amount)
        embed = discord.Embed(
            title="⛏️ Mining Hub",
            description=(
                f"{interaction.user.mention} chopped wood and collected "
                f"**{wood_amount}x wood**!"
            ),
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="🗺️ Explore",
        style=discord.ButtonStyle.primary,
        custom_id="mining:explore",
        row=0,
    )
    async def explore_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        if interaction.guild_id is None:
            await safe_followup(
                interaction,
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        user_id = str(interaction.user.id)
        gid = interaction.guild_id
        text, item, amount = roll_explore_outcome()
        if item:
            await db.update_mining_item(user_id, gid, item, amount)
        embed = discord.Embed(
            title="⛏️ Mining Hub",
            description=f"{interaction.user.mention} {text}",
            color=SUCCESS_COLOR if amount >= 0 else ERROR_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="📦 Inventory",
        style=discord.ButtonStyle.grey,
        custom_id="mining:inventory",
        row=1,
    )
    async def inventory_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        if not await safe_defer(interaction):
            return
        if interaction.guild_id is None:
            await safe_followup(
                interaction,
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        user_id = str(interaction.user.id)
        inventory = await db.get_mining_inventory(user_id, interaction.guild_id)
        if not inventory:
            # Empty-state UX rule (mother-hub-map.md): explain what the
            # feature does and what the next step is.
            description = (
                "Your mining inventory is empty. Use `!mine` in the mining "
                "channel to start collecting items."
            )
        else:
            description = "\n".join(
                f"**{item.title()}**: {qty}" for item, qty in sorted(inventory.items())
            )
        embed = discord.Embed(
            title=f"📦 {interaction.user.name}'s Mining Inventory",
            description=description,
            color=MINING_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="📊 Stats",
        style=discord.ButtonStyle.grey,
        custom_id="mining:stats",
        row=1,
    )
    async def stats_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        if interaction.guild_id is None:
            await safe_followup(
                interaction,
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        user_id = str(interaction.user.id)
        inventory = await db.get_mining_inventory(user_id, interaction.guild_id)
        total_items = sum(inventory.values())
        unique_items = len(inventory)
        embed = discord.Embed(
            title=f"📊 {interaction.user.name}'s Mining Stats",
            color=MINING_COLOR,
        )
        embed.add_field(name="Total Items Collected", value=str(total_items))
        embed.add_field(name="Unique Items", value=str(unique_items))
        embed.set_footer(text="Click ↩ Overview to return.")
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="🔨 Build",
        style=discord.ButtonStyle.grey,
        custom_id="mining:build",
        row=1,
    )
    async def build_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_BuildModal())

    @discord.ui.button(
        label="↩ Overview",
        style=discord.ButtonStyle.secondary,
        custom_id="mining:overview",
        row=2,
    )
    async def overview_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


class _BuildModal(discord.ui.Modal, title="Build a Structure"):  # type: ignore[call-arg]
    """Modal launched by the Build button — validates inventory then crafts."""

    structure = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Structure name",
        placeholder="e.g. stone hut, iron pickaxe",
        max_length=100,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        user_id = str(interaction.user.id)
        gid = interaction.guild_id
        structure_lower = self.structure.value.strip().lower()

        recipes = load_recipes()
        required_items = recipes.get(structure_lower)
        if not required_items:
            await interaction.response.send_message(
                (
                    f"Unknown structure **{self.structure.value}**.  "
                    "Use `!buildlist` to see available structures."
                ),
                ephemeral=True,
            )
            return

        inventory = await db.get_mining_inventory(user_id, gid)
        for item, amount_needed in required_items.items():
            if inventory.get(item, 0) < amount_needed:
                await interaction.response.send_message(
                    (
                        f"You don't have enough **{item}** to build "
                        f"**{self.structure.value}**."
                    ),
                    ephemeral=True,
                )
                return

        for item, amount_needed in required_items.items():
            await db.update_mining_item(user_id, gid, item, -amount_needed)
        await db.update_mining_item(user_id, gid, structure_lower, 1)

        await interaction.response.send_message(
            f"{interaction.user.mention} successfully built a "
            f"**{self.structure.value}**!",
            ephemeral=True,
        )
