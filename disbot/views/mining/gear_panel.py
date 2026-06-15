"""Mining gear panel — slot-by-slot equipping UI (the old EquipSlotView +
MultiEquipView, modernized onto selects).

An ephemeral child of the mining hub (the ``workshop_panel`` pattern):
built via an async factory because the selects depend on the player's
inventory/equipment, and rebuilt after every action.  All writes go
through :mod:`services.mining_workflow` (``equip``/``unequip``); the
"Equip Best" button is the modern MULTIEQUIP — one click fills every
slot with the strongest owned gear (pure ``utils.mining.loadout``).
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db, equipment
from utils.mining import workshop
from utils.mining.loadout import best_loadout
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import HubView

_UNEQUIP_SENTINEL = "__unequip__"

_SLOT_EMOJI = {
    equipment.TOOL: "🧰",
    equipment.LIGHT: "💡",
    equipment.CHARM: "🍀",
    equipment.WEAPON: "⚔️",
    equipment.SHIELD: "🛡️",
    equipment.HELMET: "⛑️",
    equipment.CHESTPLATE: "🦺",
    equipment.LEGGINGS: "👖",
    equipment.BOOTS: "🥾",
}


def _set_line(equipped: dict[str, str]) -> str | None:
    """The set-collection status line ("Diamond set 4/6" / bonus active)."""
    tier = equipment.active_set_tier(equipped)
    if tier is not None:
        bonus = equipment.set_bonus(equipped)
        return (
            f"✨ **{tier.title()} set complete** — bonus +{bonus.damage} damage, "
            f"+{bonus.max_health} max health"
        )
    progress = equipment.set_progress(equipped)
    if progress is None:
        return None
    tier, count = progress
    return f"🧩 {tier.title()} set: **{count}/{len(equipment.SET_SLOTS)}** pieces"


async def build_gear_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str = "",
) -> discord.Embed:
    """The gear panel embed: every slot's item + condition, and the stats."""
    suid = str(user_id)
    equipped = await db.get_equipment(suid, guild_id)
    wear = await db.get_gear_wear(suid, guild_id)
    stats = equipment.compute_stats(equipped)

    embed = discord.Embed(title="🧰 Gear", color=MINING_COLOR)
    if note:
        embed.description = note
    lines = []
    for slot in equipment.SLOTS:
        item = equipped.get(slot)
        if not item:
            lines.append(f"{_SLOT_EMOJI.get(slot, '•')} **{slot.title()}**: —")
            continue
        line = f"{_SLOT_EMOJI.get(slot, '•')} **{slot.title()}**: {item.title()}"
        maximum = equipment.max_durability(item)
        if maximum is not None:
            line += f" {workshop.durability_bar(wear.get(item, maximum), maximum)}"
        lines.append(line)
    set_line = _set_line(equipped)
    if set_line:
        lines.append(set_line)
    embed.add_field(name="Slots", value="\n".join(lines), inline=False)
    bonuses = equipment.describe_stats(stats)
    embed.add_field(
        name="📊 Stats",
        value=(
            "\n".join(f"{label}: +{value}" for label, value in bonuses)
            if bonuses
            else "No bonuses yet — equip some gear!"
        ),
        inline=False,
    )
    embed.set_footer(
        text="Pick a slot, then an item  •  !equip <item> · !unequip <slot>",
    )
    return embed


_DOLL_FILENAME = "character_doll.png"


async def render_gear_doll(
    embed: discord.Embed,
    user_id: int,
    guild_id: int,
) -> discord.File | None:
    """Render the paper-doll and wire it into *embed* as the in-place image.

    Returns the :class:`discord.File` to attach to the gear panel's **own**
    message (or ``None`` without Pillow), so the doll rides one self-replacing
    message instead of a separate ephemeral follow-up that stacks on every Gear
    click (V-16 phase 1; the owner's 2026-06-15 "too many ephemeral panels").
    Additive: a missing/broken Pillow returns ``None`` and the embed renders
    exactly as before.
    """
    import io

    from utils.character_render import render_character_for

    equipped = await db.get_equipment(str(user_id), guild_id)
    png = render_character_for(equipped)
    if png is None:
        return None
    embed.set_image(url=f"attachment://{_DOLL_FILENAME}")
    return discord.File(io.BytesIO(png), filename=_DOLL_FILENAME)


async def _edit_gear_screen(
    interaction: discord.Interaction,
    *,
    embed: discord.Embed,
    view: MiningGearView,
    user_id: int,
    guild_id: int,
) -> None:
    """Edit the gear panel in place with a freshly-rendered doll attached.

    Always passes ``attachments`` explicitly so the doll refreshes when gear
    changes and never lingers as a stale image when Pillow is unavailable.
    """
    doll = await render_gear_doll(embed, user_id, guild_id)
    await safe_edit(
        interaction,
        embed=embed,
        view=view,
        attachments=[doll] if doll is not None else [],
    )


class _SlotSelect(discord.ui.Select):
    """Step 1 — pick the slot to manage."""

    def __init__(self, equipped: dict[str, str], wear: dict[str, int]) -> None:
        options = []
        for slot in equipment.SLOTS:
            item = equipped.get(slot)
            description = "empty"
            if item:
                description = item.title()
                maximum = equipment.max_durability(item)
                if maximum is not None:
                    description += f" ({wear.get(item, maximum)}/{maximum})"
            options.append(
                discord.SelectOption(
                    label=slot.title(),
                    value=slot,
                    description=description[:100],
                    emoji=_SLOT_EMOJI.get(slot),
                ),
            )
        super().__init__(placeholder="Pick a slot to manage…", options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: MiningGearView = self.view  # type: ignore[assignment]
        new_view = await MiningGearView.create(
            view._author,
            view.guild_id,
            slot=self.values[0],
        )
        embed = await build_gear_embed(view._author.id, view.guild_id)
        await _edit_gear_screen(
            interaction,
            embed=embed,
            view=new_view,
            user_id=view._author.id,
            guild_id=view.guild_id,
        )
        view.stop()


def _preview(item: str, slot: str, equipped: dict[str, str]) -> str:
    """The stat preview line for an item-picker option (≤100 chars).

    Shows the item's own bonuses, the net stat change vs what is currently
    in the slot ("→ Damage +2"), and a warning when equipping it would break
    an active same-tier set bonus.
    """
    stats = equipment.item_stats(item)
    parts = [f"{label} +{value}" for label, value in equipment.describe_stats(stats)]
    text = ", ".join(parts) if parts else "no stat bonuses"
    equipped_item = equipped.get(slot)
    if equipped_item and equipped_item.lower() != item.lower():
        current = equipment.item_stats(equipped_item)
        deltas = [
            f"{label} {value - getattr(current, name):+d}"
            for name, label in equipment.STAT_LABELS.items()
            if (value := getattr(stats, name)) != getattr(current, name)
        ]
        if deltas:
            text += "  →  " + ", ".join(deltas)
    if (
        equipment.active_set_tier(equipped) is not None
        and equipment.active_set_tier({**equipped, slot: item}) is None
    ):
        text = "⚠ breaks set bonus · " + text
    return text[:100]


class _ItemSelect(discord.ui.Select):
    """Step 2 — pick the owned item to equip into the chosen slot."""

    def __init__(
        self,
        slot: str,
        owned: list[str],
        equipped: dict[str, str] | None = None,
    ) -> None:
        self._slot = slot
        equipped = equipped or {}
        options = [
            discord.SelectOption(
                label=item.title(),
                value=item,
                description=_preview(item, slot, equipped),
            )
            for item in owned[:24]  # 24 + the unequip sentinel ≤ 25 (Discord cap)
        ]
        options.append(
            discord.SelectOption(
                label="— Unequip slot —",
                value=_UNEQUIP_SENTINEL,
                emoji="✖️",
            ),
        )
        super().__init__(
            placeholder=f"Equip into the {slot} slot…",
            options=options,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: MiningGearView = self.view  # type: ignore[assignment]
        if self.values[0] == _UNEQUIP_SENTINEL:
            result = await mining_workflow.unequip(
                view._author.id,
                view.guild_id,
                self._slot,
            )
        else:
            result = await mining_workflow.equip(
                view._author.id,
                view.guild_id,
                self.values[0],
            )
        await _rerender(interaction, view, result)


async def _rerender(
    interaction: discord.Interaction,
    view: MiningGearView,
    result,
) -> None:
    """Rebuild the panel after an action (equipment changed under it)."""
    note = ("✅ " if result.ok else "❌ ") + result.message
    embed = await build_gear_embed(view._author.id, view.guild_id, note=note)
    embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
    new_view = await MiningGearView.create(view._author, view.guild_id)
    await _edit_gear_screen(
        interaction,
        embed=embed,
        view=new_view,
        user_id=view._author.id,
        guild_id=view.guild_id,
    )
    view.stop()


class MiningGearView(HubView):
    """Slot picker → item picker → Equip Best; a child of the mining hub."""

    SUBSYSTEM = "mining"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @classmethod
    async def create(
        cls,
        author: discord.Member | discord.User,
        guild_id: int,
        *,
        slot: str | None = None,
    ) -> MiningGearView:
        """Async factory — the selects depend on the player's current state."""
        view = cls(author, guild_id)
        suid = str(author.id)
        inventory = await db.get_mining_inventory(suid, guild_id)
        equipped = await db.get_equipment(suid, guild_id)
        wear = await db.get_gear_wear(suid, guild_id)
        view.add_item(_SlotSelect(equipped, wear))
        if slot is not None:
            owned = sorted(
                (
                    item
                    for item, qty in inventory.items()
                    if qty > 0 and equipment.slot_for(item) == slot
                ),
                # Weakest → strongest (tier ladder), then name — so the picker
                # reads as the upgrade path.
                key=lambda it: (
                    sum(
                        getattr(equipment.item_stats(it), f)
                        for f in equipment.STAT_LABELS
                    ),
                    it,
                ),
            )
            view.add_item(_ItemSelect(slot, owned, equipped))
        return view

    @discord.ui.button(
        label="✨ Equip Best (all slots)",
        style=discord.ButtonStyle.success,
        row=2,
    )
    async def equip_best_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        inventory = await db.get_mining_inventory(str(self._author.id), self.guild_id)
        picks = best_loadout(inventory)
        if not picks:
            from utils.mining.market import TradeResult

            await _rerender(
                interaction,
                self,
                TradeResult(False, "You own no equippable gear yet."),
            )
            return
        equipped_lines = []
        for slot, item in sorted(picks.items()):
            result = await mining_workflow.equip(
                self._author.id,
                self.guild_id,
                item,
            )
            if result.ok:
                equipped_lines.append(f"**{slot}** → {item.title()}")
        from utils.mining.market import TradeResult

        await _rerender(
            interaction,
            self,
            TradeResult(True, "Equipped your best gear: " + ", ".join(equipped_lines)),
        )

    @discord.ui.button(label="↩ Mining Hub", style=discord.ButtonStyle.secondary, row=2)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Late import keeps the module-load graph acyclic (the hub imports this).
        from views.mining.main_panel import MiningHubView, build_overview_embed

        embed = await build_overview_embed(
            self._author.id,
            self.guild_id,
            name=getattr(self._author, "display_name", None),
        )
        view = MiningHubView()
        # Clear the paper-doll attachment so it does not linger on the hub.
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])
        self.stop()


__all__ = ["MiningGearView", "build_gear_embed", "render_gear_doll"]
