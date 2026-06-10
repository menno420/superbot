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

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from core.runtime.persistent_views import PersistentView, register
from services import mining_workflow
from utils import db, equipment
from utils.mining import items, workshop, world
from utils.mining.exploration import explore_from_state
from utils.mining.rewards import roll_harvest_amount
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.mining.mine_view import MineView, _build_mine_prompt_embed

# Display labels for the typed Inventory panel, keyed by ItemKind.value
# (string keys keep this rendering table independent of the enum).
_KIND_LABELS: dict[str, str] = {
    "resource": "⛏️ Resources",
    "tool": "🛠️ Tools",
    "consumable": "🧨 Consumables",
    "structure": "🏛️ Structures",
    "treasure": "💎 Treasure",
}

# The hub's routing guide — shared by the stateless fallback embed and the
# per-player live overview so the action list has one home.
_ACTIONS_GUIDE = (
    "**⛏️ Mine** — start a mining session\n"
    "**🌲 Harvest** — chop wood\n"
    "**🗺️ Explore** — discover random events\n"
    "**📦 Inventory** — view your mining resources\n"
    "**📊 Stats** — view your mining statistics\n"
    "**🔨 Build** — craft a structure\n"
    "**🔧 Workshop** — repair worn gear, craft replacements\n"
    "**⬇️ Descend / ⬆️ Ascend** — move between depth bands "
    "(deeper = richer, gated by your light)\n"
    "**🛒 Market** — sell ore for coins, buy gear\n"
    "**🧍 Character** — your full character overview"
)


async def build_overview_embed(
    user_id: int,
    guild_id: int,
    *,
    name: str | None = None,
) -> discord.Embed:
    """The mother panel's **live overview** (brainstorm §6.3): location ·
    equipped tool + durability · net worth at a glance, above the action guide.

    Rendered for the player opening the hub (``!minemenu`` / Help → Mining);
    the stateless :meth:`MiningHubView.build_embed` remains the fallback for
    restore paths with no player context.
    """
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    equipped = await db.get_equipment(suid, guild_id)
    wear = await db.get_gear_wear(suid, guild_id)
    depth = await db.get_depth(suid, guild_id)
    last_broken = await db.get_last_broken(suid, guild_id)

    def _gear_line(slot: str) -> str:
        item = equipped.get(slot)
        if not item:
            return "—"
        maximum = equipment.max_durability(item)
        if maximum is None:
            return item.title()
        bar = workshop.durability_bar(wear.get(item, maximum), maximum)
        return f"{item.title()} {bar}"

    embed = discord.Embed(
        title=f"⛏️ Mining Hub — {name}" if name else "⛏️ Mining Hub",
        description=_ACTIONS_GUIDE,
        color=MINING_COLOR,
    )
    embed.add_field(
        name="📍 Location",
        value=world.describe_position(depth),
        inline=True,
    )
    embed.add_field(name="🧰 Tool", value=_gear_line(equipment.TOOL), inline=True)
    embed.add_field(name="💡 Light", value=_gear_line(equipment.LIGHT), inline=True)
    embed.add_field(
        name="💰 Wealth",
        value=f"Net worth: **{items.total_value(inventory)}**",
        inline=True,
    )
    if last_broken:
        embed.add_field(
            name="💥 Broken gear",
            value=f"Your **{last_broken}** broke — quick-craft it at the 🔧 Workshop.",
            inline=True,
        )
    embed.set_footer(text="Only you can interact with this panel.")
    return embed


@register
class MiningHubView(PersistentView):
    """Persistent, stateless mining hub panel."""

    SUBSYSTEM = "mining"

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="⛏️ Mining Hub",
            description=_ACTIONS_GUIDE,
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
        user_id = str(interaction.user.id)
        gid = interaction.guild_id
        inventory = await db.get_mining_inventory(user_id, gid)
        equipped = await db.get_equipment(user_id, gid)
        depth = await db.get_depth(user_id, gid)
        text, item, amount = explore_from_state(
            equipped,
            inventory,
            biome=world.biome_for_depth(depth),
        )
        if item:
            await db.update_mining_item(user_id, gid, item, amount)
        wear = await mining_workflow.wear_tick(
            interaction.user.id,
            gid,
            action=workshop.ACTION_EXPLORE,
            depth=depth,
            equipped=equipped,
        )
        description = (
            f"{interaction.user.mention} {text}\n_{world.describe_position(depth)}_"
        )
        if wear.notes:
            description += "\n" + "\n".join(wear.notes)
        embed = discord.Embed(
            title="⛏️ Mining Hub",
            description=description,
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

    @discord.ui.button(
        label="🔧 Workshop",
        style=discord.ButtonStyle.grey,
        custom_id="mining:workshop",
        row=1,
    )
    async def workshop_btn(
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
        # Lazy import: views→views child panel (mirrors the Market button).
        from views.mining.workshop_panel import MiningWorkshopView, build_workshop_embed

        embed = await build_workshop_embed(interaction.user.id, interaction.guild_id)
        view = await MiningWorkshopView.create(interaction.user, interaction.guild_id)
        await safe_edit(interaction, embed=embed, view=view)

    @discord.ui.button(
        label="⬇️ Descend",
        style=discord.ButtonStyle.success,
        custom_id="mining:descend",
        row=2,
    )
    async def descend_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
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
        depth = await db.get_depth(user_id, gid)
        stats = equipment.compute_stats(await db.get_equipment(user_id, gid))
        new_depth = world.descend(depth, stats)
        if new_depth == depth:
            description = (
                f"{interaction.user.mention} can't descend any deeper.\n"
                f"_{world.descend_hint(stats)}_"
            )
            color = ERROR_COLOR
        else:
            await db.set_depth(user_id, gid, new_depth)
            description = (
                f"{interaction.user.mention} descended to "
                f"**{world.describe_position(new_depth)}**."
            )
            color = SUCCESS_COLOR
        embed = discord.Embed(
            title="⛏️ Mining Hub",
            description=description,
            color=color,
        )
        embed.set_footer(text="Pick another action above to continue.")
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="⬆️ Ascend",
        style=discord.ButtonStyle.secondary,
        custom_id="mining:ascend",
        row=2,
    )
    async def ascend_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
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
        depth = await db.get_depth(user_id, gid)
        new_depth = world.ascend(depth)
        if new_depth == depth:
            description = f"{interaction.user.mention} is already at the **Surface**."
            color = MINING_COLOR
        else:
            await db.set_depth(user_id, gid, new_depth)
            description = (
                f"{interaction.user.mention} climbed up to "
                f"**{world.describe_position(new_depth)}**."
            )
            color = SUCCESS_COLOR
        embed = discord.Embed(
            title="⛏️ Mining Hub",
            description=description,
            color=color,
        )
        embed.set_footer(text="Pick another action above to continue.")
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="🛒 Market",
        style=discord.ButtonStyle.primary,
        custom_id="mining:market",
        row=2,
    )
    async def market_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        if interaction.guild_id is None:
            await safe_followup(
                interaction,
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        # Lazy import: views→views child panel (avoids any import-order surprise
        # with the back-link the market panel makes to this hub).
        from views.mining.market_panel import MiningMarketView, build_market_embed

        embed = await build_market_embed(interaction.user.id, interaction.guild_id)
        view = MiningMarketView(interaction.user, interaction.guild_id)
        await safe_edit(interaction, embed=embed, view=view)

    @discord.ui.button(
        label="🧍 Character",
        style=discord.ButtonStyle.grey,
        custom_id="mining:character",
        row=3,
    )
    async def character_btn(
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
        # Read-only character overview, shown in place on the hub.
        from views.mining.character_panel import build_character_embed

        embed = await build_character_embed(
            interaction.user.id,
            interaction.guild_id,
            name=interaction.user.display_name,
        )
        embed.set_footer(text="Pick another action above to continue.")
        await safe_edit(interaction, embed=embed, view=self)


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
        # One shared craft implementation (atomic materials+product
        # transaction) serves this modal, !build/!craft, and the Workshop
        # panel — services/mining_workflow.py (RS02).
        result = await mining_workflow.craft(
            interaction.user.id,
            interaction.guild_id,
            self.structure.value,
        )
        await interaction.response.send_message(
            f"{interaction.user.mention} {result.message}",
            ephemeral=True,
        )
