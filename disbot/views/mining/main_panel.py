"""Mining hub PersistentView + Build modal — extracted from ``cogs/mining_cog.py``.

Pattern B placement per ``docs/architecture.md`` §"PersistentView
placement": the view lives in views/ and the cog re-exports for the
persistent-view registry side-effect.

The Mine button opens a fresh ephemeral ``MineView`` from
``views.mining.mine_view``.  Harvest / Explore / Inventory / Stats
buttons call DB helpers directly — no cog round-trip needed.  The
Build button opens ``_BuildModal`` which loads the current recipes
list and validates the user's inventory.

Navigation rule (PR #1 menu-lifecycle fix): the hub does not ship a
root-level "↩ Overview" button. Such a button would be a no-op when
the hub is already on its root state, violating the architecture
rule that root panels must not show no-op Overview controls. Action
buttons themselves are the navigation surface; after a Harvest /
Explore / Inventory / Stats action, the embed shows the result and
the user can click any action button to take the next step. The
``_MineResultsView`` in ``views.mining.mine_view`` retains its own
"↩ Mining Menu" button because it IS a child screen returning to
this hub's root.
"""

from __future__ import annotations

import discord

from cogs.mining.recipes import load_recipes
from cogs.mining.rewards import roll_harvest_amount
from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from core.runtime.persistent_views import PersistentView, register
from utils import db
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.mining.mine_view import MineView, _build_mine_prompt_embed

# Display labels for the typed Inventory panel, keyed by ItemKind.value so this
# module need not import the cogs-layer ItemKind enum (views→cogs layer rule).
_KIND_LABELS: dict[str, str] = {
    "resource": "⛏️ Resources",
    "tool": "🛠️ Tools",
    "consumable": "🧨 Consumables",
    "structure": "🏛️ Structures",
    "treasure": "💎 Treasure",
}


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
        embed.set_footer(text="Pick another action above to continue.")
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
        # Lazy import: the exploration engine is game-domain logic that lives
        # in cogs/, and views must not import cogs at module level (layer
        # rule).  A later step relocates the pure engine to a shared layer so
        # this can become a plain import (mining_exploration_brainstorm §7.4).
        from cogs.mining.exploration import explore_from_state

        user_id = str(interaction.user.id)
        gid = interaction.guild_id
        inventory = await db.get_mining_inventory(user_id, gid)
        equipped = await db.get_equipment(user_id, gid)
        text, item, amount = explore_from_state(equipped, inventory)
        if item:
            await db.update_mining_item(user_id, gid, item, amount)
        embed = discord.Embed(
            title="⛏️ Mining Hub",
            description=f"{interaction.user.mention} {text}",
            color=SUCCESS_COLOR if amount >= 0 else ERROR_COLOR,
        )
        embed.set_footer(text="Pick another action above to continue.")
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
        # Lazy import: the item taxonomy is game-domain logic in cogs/, and
        # views must not import cogs at module level (layer rule, as in
        # explore_btn above).
        from cogs.mining import items

        user_id = str(interaction.user.id)
        inventory = await db.get_mining_inventory(user_id, interaction.guild_id)
        embed = discord.Embed(
            title=f"📦 {interaction.user.name}'s Mining Inventory",
            color=MINING_COLOR,
        )
        if not inventory:
            # Empty-state UX rule (mother-hub-map.md): explain what the
            # feature does and what the next step is.
            embed.description = (
                "Your mining inventory is empty. Use `!mine` in the mining "
                "channel to start collecting items."
            )
            embed.set_footer(text="Pick another action above to continue.")
        else:
            for kind, rows in items.summarize_inventory(inventory):
                embed.add_field(
                    name=_KIND_LABELS.get(kind.value, kind.value.title()),
                    value="\n".join(f"**{name.title()}** ×{qty}" for name, qty in rows),
                    inline=False,
                )
            embed.set_footer(
                text=(
                    f"Net worth: {items.total_value(inventory)}  •  "
                    "Pick another action above to continue."
                ),
            )
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
        # Lazy import: cogs-layer taxonomy (layer rule — see explore_btn).
        from cogs.mining import items

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
        embed.add_field(name="Net Worth", value=str(items.total_value(inventory)))
        embed.set_footer(text="Pick another action above to continue.")
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="🔨 Build",
        style=discord.ButtonStyle.grey,
        custom_id="mining:build",
        row=1,
    )
    async def build_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_BuildModal())


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
