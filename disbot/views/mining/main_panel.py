"""Mining hub PersistentView + Build modal — extracted from ``cogs/mining_cog.py``.

Pattern B placement per ``docs/architecture.md`` §"PersistentView
placement": the view lives in views/ and the cog re-exports for the
persistent-view registry side-effect.

Option A declutter (owner-directed, 2026-06-15;
``docs/planning/mining-hub-redesign-2026-06-15.md``): the main hub is six
buttons — **⛏️ Mine · 🌲 Harvest · 🗺️ Explore · 🧍 Character · 🧰 Gear ·
🔨 Workshop** — and everything else moved into a sub-hub or the Mine action:

- **🧍 Character** sub-hub (``character_hub``): Overview · Inventory · Stats ·
  Skills · Vault · Home.
- **🗺️ Explore** sub-hub (``explore_hub``): the open-world explorer (Fishing /
  Roam / Quests), a stub for now. *Distinct* from the old depth-tied mining
  random-event "explore", which folded into the Mine action.
- **🔨 Workshop** sub-hub (``workshop_hub``): Craft · Repair · Forge · Market.
- **Mine** (``MineView``) absorbed Descend / Ascend + the old mining-explore
  random-event as an interim until PR3's grid Mine.

The Mine button opens a fresh ephemeral ``MineView`` from
``views.mining.mine_view``.

Navigation rule (PR #1 menu-lifecycle fix): the hub does not ship a
root-level "↩ Overview" button. Action buttons themselves are the
navigation surface; sub-hubs return via their own "↩ Mining Hub" button.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from core.runtime.persistent_views import PersistentView, register
from services import mining_workflow
from utils import db, equipment
from utils.mining import capacity, items, workshop, world
from utils.ui_constants import MINING_COLOR, SUCCESS_COLOR
from views.mining.mine_view import MineView, _build_mine_prompt_embed

# The hub's routing guide — shared by the stateless fallback embed and the
# per-player live overview so the action list has one home. Six top-level
# actions; each detailed list lives on its sub-hub (Option A declutter).
_ACTIONS_GUIDE = (
    "**⛏️ Mine** — dig for ore, move between depths, explore for events\n"
    "**🌲 Harvest** — chop wood\n"
    "**🗺️ Explore** — the open-world explorer (fishing, roam, quests — early)\n"
    "**🧍 Character** — you: overview · inventory · stats · skills · vault · home\n"
    "**🧰 Gear** — equip your best tools, lights, and combat gear\n"
    "**🔨 Workshop** — craft & build · repair · 🔥 forge · 🛒 market (all here)"
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
    pack = capacity.pack_status(inventory)
    embed.add_field(
        name="🎒 Pack",
        value=f"{pack.used}/{pack.cap} item types",
        inline=True,
    )
    pack_nudge = capacity.pack_warning(pack)
    if pack_nudge:
        embed.add_field(name="​", value=pack_nudge, inline=False)
    if last_broken:
        embed.add_field(
            name="💥 Broken gear",
            value=f"Your **{last_broken}** broke — quick-craft it at the 🔧 Workshop.",
            inline=True,
        )
    embed.set_footer(text="Only you can interact with this panel.")
    return embed


async def _edit_in_place(
    interaction: discord.Interaction,
    *,
    embed: discord.Embed,
    view: discord.ui.View,
    image: discord.File | None = None,
) -> None:
    """Edit the hub's anchor message in place, owning its optional image.

    The gear paper-doll renders *into* this one message (``image=...``) instead
    of a separate ephemeral follow-up that piles up on every click (the owner's
    2026-06-15 "too many ephemeral panels"). Every other action passes no image,
    which clears a prior card so it never lingers on the next screen.
    """
    await safe_edit(
        interaction,
        embed=embed,
        view=view,
        attachments=[image] if image is not None else [],
    )


@register
class MiningHubView(PersistentView):
    """Persistent, stateless mining hub panel — the six Option A top actions."""

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
        view = MineView(interaction.user, interaction.guild_id)
        await interaction.response.edit_message(
            embed=_build_mine_prompt_embed(),
            view=view,
            attachments=[],  # clear a prior inventory/gear card so it doesn't linger
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
        result = await mining_workflow.harvest(
            interaction.user.id,
            interaction.guild_id,
        )
        description = (
            f"{interaction.user.mention} chopped wood and collected "
            f"**{result.amount}x wood**!"
        )
        if result.xp_note:
            description += "\n" + result.xp_note
        if result.pack_warning:
            description += "\n" + result.pack_warning
        embed = discord.Embed(
            title="⛏️ Mining Hub",
            description=description,
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="Pick another action above to continue.")
        await _edit_in_place(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="🗺️ Explore",
        style=discord.ButtonStyle.primary,
        custom_id="mining:explore_hub",
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
        # Option A: this opens the open-world explorer sub-hub (stub). It is a
        # DIFFERENT concept from the old depth-tied mining random-event explore,
        # which folded into the Mine action. New custom_id (mining:explore_hub)
        # so the persistent panel doesn't reuse the old mining:explore id.
        from views.mining.explore_hub import (
            MiningExploreHubView,
            build_explore_hub_embed,
        )

        embed = build_explore_hub_embed()
        view = MiningExploreHubView(interaction.user, interaction.guild_id)
        await _edit_in_place(interaction, embed=embed, view=view)

    @discord.ui.button(
        label="🧍 Character",
        style=discord.ButtonStyle.grey,
        custom_id="mining:character",
        row=1,
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
        # Option A: the Character sub-hub groups Overview / Inventory / Stats /
        # Skills / Vault / Home (Home placed here per the 2026-06-19 deviation).
        from views.mining.character_hub import (
            MiningCharacterHubView,
            build_character_hub_embed,
        )

        embed = build_character_hub_embed()
        view = MiningCharacterHubView(interaction.user, interaction.guild_id)
        await _edit_in_place(interaction, embed=embed, view=view)

    @discord.ui.button(
        label="🧰 Gear",
        style=discord.ButtonStyle.primary,
        custom_id="mining:gear",
        row=1,
    )
    async def gear_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        if interaction.guild_id is None:
            await safe_followup(
                interaction,
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        # Lazy import: views→views child panel (mirrors the Workshop button).
        from views.mining.gear_panel import (
            MiningGearView,
            build_gear_embed,
            render_gear_doll,
        )

        embed = await build_gear_embed(interaction.user.id, interaction.guild_id)
        view = await MiningGearView.create(interaction.user, interaction.guild_id)
        # V-16: the paper-doll renders *into* this message (one self-replacing
        # panel) instead of a separate ephemeral follow-up that stacks per click.
        doll = await render_gear_doll(embed, interaction.user.id, interaction.guild_id)
        await _edit_in_place(interaction, embed=embed, view=view, image=doll)

    @discord.ui.button(
        label="🔨 Workshop",
        style=discord.ButtonStyle.primary,
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
        # Declutter (Option A, 2026-06-15): one Workshop sub-hub groups
        # Craft (consolidated build/craft/recipes) · Repair · Forge · Market.
        from views.mining.workshop_hub import (
            MiningWorkshopHubView,
            build_workshop_hub_embed,
        )

        embed = build_workshop_hub_embed()
        view = MiningWorkshopHubView(interaction.user, interaction.guild_id)
        await _edit_in_place(interaction, embed=embed, view=view)


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
        from utils.mining.names import resolve_item_name
        from utils.mining.recipes import load_recipes

        wanted = self.structure.value
        wanted = resolve_item_name(wanted, load_recipes()) or wanted
        result = await mining_workflow.craft(
            interaction.user.id,
            interaction.guild_id,
            wanted,
        )
        await interaction.response.send_message(
            f"{interaction.user.mention} {result.message}",
            ephemeral=True,
        )
