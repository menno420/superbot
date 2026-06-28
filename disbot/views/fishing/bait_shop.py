"""The bait shop — view + buy the consumable rarity knob (owner design Q-0175 §4).

``!bait`` (and the menu's 🪱 Bait button) opens this panel: your currently-loaded
bait + remaining charges, the shelf of bait types, and a select to **buy a pack**
— spending coins through the audited ``fishing_workflow.buy_bait`` seam. A normal
author-restricted :class:`BaseView` panel (not a game-state view); the timed
cast/reel lifecycle lives in :mod:`views.fishing.cast_view`.

Bait is the *consumable* how-well knob beside the permanent rod ladder: while you
hold charges, each cast spends one and turns one or both of its knobs — rarity
pull (bias the catch toward bigger fish) and bite speed (fish bite sooner) — on
top of the equipped rod's.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import fishing_workflow
from utils import db
from utils.fishing import PEARL_ITEM
from utils.fishing import bait as bait_mod
from utils.ui_constants import ECONOMY_COLOR
from views.base import BaseView


def build_bait_embed(
    active: bait_mod.Bait | None,
    charges: int,
    balance: int,
    *,
    pearls: int = 0,
    note: str | None = None,
) -> discord.Embed:
    """The bait-shop panel embed: what's loaded, the shelf, and your balance."""
    embed = discord.Embed(title="🪱 Bait Shop", color=ECONOMY_COLOR)
    if active is not None and charges > 0:
        embed.description = (
            f"Loaded: **{active.name}** {active.emoji} — "
            f"**{charges}** casts left ({bait_mod.effect_text(active)}).\n"
            "*Each cast spends one charge and applies these on top of your rod.*"
        )
    else:
        embed.description = (
            "No bait loaded — you're fishing bare (which catches fine!).\n"
            "*Load a pack for rarer, bigger fish or quicker bites.*"
        )

    shelf = []
    for bait in bait_mod.BAIT_CATALOG:
        shelf.append(
            f"{bait.emoji} **{bait.name}** — {bait.price} 🪙 "
            f"(×{bait.charges} casts, {bait_mod.effect_text(bait)})",
        )
    embed.add_field(name="The shelf", value="\n".join(shelf), inline=False)

    craftable = []
    for key in bait_mod.CRAFTABLE_KEYS:
        bait = bait_mod.bait_by_key(key)
        recipe = bait_mod.craft_recipe(key)
        if bait is None or recipe is None:
            continue
        craftable.append(
            f"{bait.emoji} **{bait.name}** — {bait_mod.recipe_text(recipe)}",
        )
    if craftable:
        embed.add_field(
            name="Craft from fish",
            value="\n".join(craftable)
            + "\n*Turn small catches into bait — no coins needed.*",
            inline=False,
        )

    pearl_craftable = []
    for key in bait_mod.PEARL_CRAFTABLE_KEYS:
        bait = bait_mod.bait_by_key(key)
        pearl_cost = bait_mod.pearl_recipe(key)
        if bait is None or pearl_cost is None:
            continue
        pearl_craftable.append(
            f"{bait.emoji} **{bait.name}** — {bait_mod.pearl_recipe_text(pearl_cost)}",
        )
    if pearl_craftable:
        embed.add_field(
            name=f"Craft from pearls (you have {pearls} 🦪)",
            value="\n".join(pearl_craftable)
            + "\n*Pearls drop rarely when you reel in a fish — bigger fish, "
            "better odds.*",
            inline=False,
        )

    embed.add_field(
        name="Your balance",
        value=f"**{balance}** 🪙",
        inline=False,
    )
    if note:
        embed.set_footer(text=note)
    return embed


class _BaitSelect(discord.ui.Select):
    """Pick a bait pack to buy — one option per shelf entry."""

    def __init__(self) -> None:
        options = [
            discord.SelectOption(
                label=f"{bait.name} — {bait.price} coins",
                value=bait.key,
                emoji=bait.emoji,
                description=f"×{bait.charges} casts · {bait_mod.effect_text(bait)}",
            )
            for bait in bait_mod.BAIT_CATALOG
        ]
        super().__init__(
            placeholder="Buy a pack of bait…",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: BaitShopView = self.view  # type: ignore[assignment]
        result = await fishing_workflow.buy_bait(
            view._author.id,
            view.guild_id,
            self.values[0],
        )
        await view.rerender(interaction, note=result.message)


class _BaitCraftSelect(discord.ui.Select):
    """Pick a craftable bait — turn small caught fish into a pack (no coins)."""

    def __init__(self) -> None:
        options = []
        for key in bait_mod.CRAFTABLE_KEYS:
            bait = bait_mod.bait_by_key(key)
            recipe = bait_mod.craft_recipe(key)
            if bait is None or recipe is None:
                continue
            options.append(
                discord.SelectOption(
                    label=f"{bait.name} — {bait_mod.recipe_text(recipe)}",
                    value=bait.key,
                    emoji=bait.emoji,
                    description=f"×{bait.charges} casts · {bait_mod.effect_text(bait)}",
                ),
            )
        super().__init__(
            placeholder="Craft a pack from caught fish…",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: BaitShopView = self.view  # type: ignore[assignment]
        result = await fishing_workflow.craft_bait(
            view._author.id,
            view.guild_id,
            self.values[0],
        )
        await view.rerender(interaction, note=result.message)


class _PearlCraftSelect(discord.ui.Select):
    """Pick a pearl-craftable bait — spend the rare reel-drop material (no coins)."""

    def __init__(self) -> None:
        options = []
        for key in bait_mod.PEARL_CRAFTABLE_KEYS:
            bait = bait_mod.bait_by_key(key)
            pearl_cost = bait_mod.pearl_recipe(key)
            if bait is None or pearl_cost is None:
                continue
            options.append(
                discord.SelectOption(
                    label=f"{bait.name} — {bait_mod.pearl_recipe_text(pearl_cost)}",
                    value=bait.key,
                    emoji="🦪",
                    description=f"×{bait.charges} casts · {bait_mod.effect_text(bait)}",
                ),
            )
        super().__init__(
            placeholder="Craft a pack from pearls…",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: BaitShopView = self.view  # type: ignore[assignment]
        result = await fishing_workflow.craft_pearl_bait(
            view._author.id,
            view.guild_id,
            self.values[0],
        )
        await view.rerender(interaction, note=result.message)


class BaitShopView(BaseView):
    """Bait-shop panel: buy with coins, craft from fish, or craft from pearls."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
    ) -> None:
        super().__init__(author, timeout=120)
        self.guild_id = guild_id
        self.add_item(_BaitSelect())
        self.add_item(_BaitCraftSelect())
        self.add_item(_PearlCraftSelect())

    async def rerender(
        self,
        interaction: discord.Interaction,
        *,
        note: str | None = None,
    ) -> None:
        """Re-read the player's bait / balance / pearls and redraw the panel."""
        active, charges = await fishing_workflow.get_active_bait(
            self._author.id,
            self.guild_id,
        )
        balance = await db.get_coins(self._author.id, self.guild_id)
        inventory = await db.get_mining_inventory(str(self._author.id), self.guild_id)
        pearls = inventory.get(PEARL_ITEM, 0)
        embed = build_bait_embed(active, charges, balance, pearls=pearls, note=note)
        await safe_edit(interaction, embed=embed, view=self)
