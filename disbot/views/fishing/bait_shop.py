"""The bait shop — view + buy the consumable rarity knob (owner design Q-0175 §4).

``!bait`` (and the menu's 🪱 Bait button) opens this panel: your currently-loaded
bait + remaining charges, the shelf of bait types, and a select to **buy a pack**
— spending coins through the audited ``fishing_workflow.buy_bait`` seam. A normal
author-restricted :class:`BaseView` panel (not a game-state view); the timed
cast/reel lifecycle lives in :mod:`views.fishing.cast_view`.

Bait is the *consumable* how-well knob beside the permanent rod ladder: while you
hold charges, each cast spends one and multiplies the rod's rarity pull, biasing
the catch toward bigger fish within your unlocked band.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import fishing_workflow
from utils import db
from utils.fishing import bait as bait_mod
from utils.ui_constants import ECONOMY_COLOR
from views.base import BaseView


def build_bait_embed(
    active: bait_mod.Bait | None,
    charges: int,
    balance: int,
    *,
    note: str | None = None,
) -> discord.Embed:
    """The bait-shop panel embed: what's loaded, the shelf, and your balance."""
    embed = discord.Embed(title="🪱 Bait Shop", color=ECONOMY_COLOR)
    if active is not None and charges > 0:
        embed.description = (
            f"Loaded: **{active.name}** {active.emoji} — "
            f"**{charges}** casts left (×{active.rarity_pull:g} rarity pull).\n"
            "*Each cast spends one charge and pulls your catch toward bigger fish.*"
        )
    else:
        embed.description = (
            "No bait loaded — you're fishing bare (which catches fine!).\n"
            "*Load a pack to bias your casts toward rarer, bigger fish.*"
        )

    shelf = []
    for bait in bait_mod.BAIT_CATALOG:
        shelf.append(
            f"{bait.emoji} **{bait.name}** — {bait.price} 🪙 "
            f"(×{bait.charges} casts, ×{bait.rarity_pull:g} rarity)",
        )
    embed.add_field(name="The shelf", value="\n".join(shelf), inline=False)
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
                description=(
                    f"×{bait.charges} casts · ×{bait.rarity_pull:g} rarity pull"
                ),
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
        active, charges = await fishing_workflow.get_active_bait(
            view._author.id,
            view.guild_id,
        )
        balance = await db.get_coins(view._author.id, view.guild_id)
        embed = build_bait_embed(active, charges, balance, note=result.message)
        await safe_edit(interaction, embed=embed, view=view)


class BaitShopView(BaseView):
    """Author-restricted bait-shop panel with a buy select."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
    ) -> None:
        super().__init__(author, timeout=120)
        self.guild_id = guild_id
        self.add_item(_BaitSelect())
