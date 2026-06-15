"""Mining workshop panel — repair worn gear, craft replacements (durability UI).

An ephemeral child of the mining hub (mirrors ``market_panel``).  All
durability / money / inventory moves live in
:mod:`services.mining_workflow` (one transaction per operation — Q-0071 —
shared with the ``!repair`` / ``!craft`` / ``!quickcraft`` commands); this
view is just the buttons + selects that call it.  The pure pricing /
listing helpers come from :mod:`utils.mining.workshop`.

Because the repair/craft options depend on DB state, the view is built via the
async :meth:`MiningWorkshopView.create` factory and rebuilt after every action
(a repair changes what is worn; a craft changes what is craftable).
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db, equipment
from utils.mining import workshop
from utils.mining.recipes import load_recipes
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import HubView


async def build_workshop_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str = "",
) -> discord.Embed:
    """Build the workshop embed: gear condition, repair costs, craftable gear."""
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    equipped = await db.get_equipment(suid, guild_id)
    wear = await db.get_gear_wear(suid, guild_id)
    last_broken = await db.get_last_broken(suid, guild_id)
    balance = await db.get_coins(user_id, guild_id)

    embed = discord.Embed(title="🔧 Workshop", color=MINING_COLOR)
    if note:
        embed.description = note

    gear_lines = []
    for slot in equipment.SLOTS:
        item = equipped.get(slot)
        if not item:
            continue
        maximum = equipment.max_durability(item)
        if maximum is None:
            gear_lines.append(f"**{item.title()}** — does not wear")
            continue
        remaining = wear.get(item, maximum)
        line = f"**{item.title()}** {workshop.durability_bar(remaining, maximum)}"
        cost = workshop.repair_cost(item, remaining)
        if cost is not None:
            line += f" — repair {cost} 🪙"
        gear_lines.append(line)
    embed.add_field(
        name="🧰 Equipped gear",
        value="\n".join(gear_lines) if gear_lines else "Nothing equipped yet.",
        inline=False,
    )

    if last_broken:
        embed.add_field(
            name="💥 Last broken",
            value=f"**{last_broken.title()}** — hit 🔁 Quick-craft to replace it.",
            inline=False,
        )

    craftables = workshop.craftable_gear(load_recipes(), inventory)
    if craftables:
        # The set-piece catalogue (30+ gear recipes) outgrew one field's
        # 1024-char cap: show what is craftable NOW, point at the Recipe
        # browser for the full tree.
        ready = [g for g in craftables if g.craftable]
        lines = [
            f"✅ **{g.name.title()}** — {workshop.describe_materials(g.materials)}"
            for g in ready[:12]
        ]
        if not ready:
            lines = ["▫️ Nothing craftable from your current resources."]
        lines.append(
            f"📖 All **{len(craftables)}** gear recipes: the Recipe browser "
            f"(`!recipes`).",
        )
        embed.add_field(name="🛠️ Craft gear", value="\n".join(lines), inline=False)
    embed.set_footer(
        text=f"Balance: {balance} 🪙  •  !repair <item> · !craft <item> · !quickcraft",
    )
    return embed


class _RepairSelect(discord.ui.Select):
    """Worn-gear dropdown — repairs one item through the audited coin path."""

    def __init__(self, user_id: int, guild_id: int, options: list) -> None:
        self._user_id = user_id
        self._guild_id = guild_id
        super().__init__(placeholder="Repair worn gear…", options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.repair(
            self._user_id,
            self._guild_id,
            self.values[0],
        )
        await _rerender(interaction, self.view, result)


class _CraftSelect(discord.ui.Select):
    """Gear-recipe dropdown — crafts one item (atomic materials+product)."""

    def __init__(self, user_id: int, guild_id: int, options: list) -> None:
        self._user_id = user_id
        self._guild_id = guild_id
        super().__init__(
            placeholder="Craft gear from resources…",
            options=options,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.craft(
            self._user_id,
            self._guild_id,
            self.values[0],
        )
        await _rerender(interaction, self.view, result)


async def _rerender(
    interaction: discord.Interaction,
    view: discord.ui.View | None,
    result,
) -> None:
    """Rebuild the panel after an action (state changed under the selects)."""
    author = getattr(view, "_author", interaction.user)
    guild_id = getattr(view, "guild_id", interaction.guild_id)
    embed = await build_workshop_embed(
        author.id,
        guild_id,
        note=("✅ " if result.ok else "❌ ") + result.message,
    )
    embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
    new_view = await MiningWorkshopView.create(author, guild_id)
    await safe_edit(interaction, embed=embed, view=new_view)
    if view is not None:
        view.stop()


class MiningWorkshopView(HubView):
    """Repair + craft + quick-craft panel; a child of the mining hub."""

    SUBSYSTEM = "mining"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @classmethod
    async def create(
        cls,
        author: discord.Member | discord.User,
        guild_id: int,
    ) -> MiningWorkshopView:
        """Async factory — the selects depend on the player's current state."""
        view = cls(author, guild_id)
        suid = str(author.id)
        inventory = await db.get_mining_inventory(suid, guild_id)
        wear = await db.get_gear_wear(suid, guild_id)
        last_broken = await db.get_last_broken(suid, guild_id)

        repair_options = [
            discord.SelectOption(
                label=f"{item.title()} — {cost} 🪙",
                value=item,
            )
            for item, remaining in sorted(wear.items())
            if inventory.get(item, 0) > 0
            and (cost := workshop.repair_cost(item, remaining)) is not None
        ]
        if repair_options:
            view.add_item(
                _RepairSelect(author.id, guild_id, repair_options[:25]),
            )

        # Craftable-now first, so the 25-option cap drops the recipes the
        # player can't afford anyway (the Recipe browser carries the full
        # catalogue).
        craft_options = [
            discord.SelectOption(
                label=f"{g.name.title()} — {workshop.describe_materials(g.materials)}"[
                    :100
                ],
                value=g.name,
                emoji="✅" if g.craftable else None,
            )
            for g in sorted(
                workshop.craftable_gear(load_recipes(), inventory),
                key=lambda g: (not g.craftable, g.name),
            )
        ]
        if craft_options:
            view.add_item(_CraftSelect(author.id, guild_id, craft_options[:25]))

        if not last_broken:
            view.quick_craft_btn.disabled = True
        return view

    @discord.ui.button(
        label="🔁 Quick-craft last broken",
        style=discord.ButtonStyle.success,
        row=2,
    )
    async def quick_craft_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.quick_craft(self._author.id, self.guild_id)
        await _rerender(interaction, self, result)

    @discord.ui.button(label="↩ Workshop", style=discord.ButtonStyle.secondary, row=2)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Back to the Workshop sub-hub that opened this panel (owner ask 2026-06-15).
        from views.mining.workshop_hub import (
            MiningWorkshopHubView,
            build_workshop_hub_embed,
        )

        await interaction.response.edit_message(
            embed=build_workshop_hub_embed(),
            view=MiningWorkshopHubView(self._author, self.guild_id),
            attachments=[],
        )
        self.stop()


__all__ = ["MiningWorkshopView", "build_workshop_embed"]
