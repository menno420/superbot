"""The rod shop — view + buy your way up the rod ladder (owner design Q-0175).

``!rod`` opens this panel: your current rod, the next tier and its price, and an
**Upgrade** button that spends coins through the audited
``fishing_workflow.buy_rod`` seam. A normal author-restricted :class:`BaseView`
panel (not a game-state view) — the timed cast/reel lifecycle lives in
:mod:`views.fishing.cast_view`.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import fishing_workflow
from utils import db
from utils.fishing import rods as rods_mod
from utils.ui_constants import ECONOMY_COLOR
from views.base import BaseView


def _knob_summary(rod: rods_mod.Rod) -> str:
    """A friendly one-liner of what a rod's knobs buy (vs. the bare starter)."""
    if rod.tier == 0:
        return "the trusty starter — catches everything, just no bonuses"
    bits = [
        f"+{rod.window_bonus:.1f}s reaction time",
        f"bites {round((1 - rod.bite_speed) * 100)}% faster",
        "better catches in your band",
        f"{round(rod.escape_resist * 100)}% less escape in fights",
        f"{round(rod.premature_grace * 100)}% chance to forgive an early reel",
    ]
    return " · ".join(bits)


def build_rod_embed(
    current: rods_mod.Rod,
    nxt: rods_mod.Rod | None,
    balance: int,
    *,
    note: str | None = None,
) -> discord.Embed:
    """The rod-shop panel embed: current rod, the ladder, and the next upgrade."""
    embed = discord.Embed(title="🎣 Your Fishing Rod", color=ECONOMY_COLOR)
    embed.description = (
        f"You're wielding the **{current.name}** {current.emoji}\n"
        f"*{_knob_summary(current)}*"
    )

    ladder_lines = []
    for rod in rods_mod.ROD_LADDER:
        if rod.tier < current.tier:
            mark = "✅"
        elif rod.tier == current.tier:
            mark = "**▶**"
        else:
            mark = "🔒"
        price = "—" if rod.price == 0 else f"{rod.price} 🪙"
        ladder_lines.append(f"{mark} {rod.emoji} **{rod.name}** ({price})")
    embed.add_field(name="The ladder", value="\n".join(ladder_lines), inline=False)

    if nxt is None:
        embed.add_field(
            name="Next upgrade",
            value="You wield the finest rod there is. 💎",
            inline=False,
        )
    else:
        recipe = rods_mod.rod_recipe(nxt.tier)
        craft_line = (
            f"\n🎣 _or craft from {rods_mod.rod_recipe_text(recipe)}_"
            " (📋 Recipes shows your live progress)"
            if recipe is not None
            else ""
        )
        embed.add_field(
            name=f"Next: {nxt.emoji} {nxt.name} — {nxt.price} 🪙",
            value=(
                f"_{_knob_summary(nxt)}_\nYour balance: **{balance}** 🪙{craft_line}"
            ),
            inline=False,
        )
    if note:
        embed.set_footer(text=note)
    return embed


class RodShopView(BaseView):
    """Author-restricted rod-shop panel with a single Upgrade button."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
        *,
        at_max: bool,
    ) -> None:
        super().__init__(author, timeout=120)
        self.guild_id = guild_id
        self.upgrade_btn.disabled = at_max
        self.craft_btn.disabled = at_max

    async def _rerender(
        self,
        interaction: discord.Interaction,
        tier: int,
        note: str,
    ) -> None:
        """Re-render the panel after a buy/craft attempt and re-gate the buttons."""
        current = rods_mod.rod_for_tier(tier)
        nxt = rods_mod.next_rod(tier)
        balance = await db.get_coins(self._author.id, self.guild_id)
        self.upgrade_btn.disabled = nxt is None
        self.craft_btn.disabled = nxt is None
        embed = build_rod_embed(current, nxt, balance, note=note)
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="⬆️ Upgrade rod", style=discord.ButtonStyle.success)
    async def upgrade_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        result = await fishing_workflow.buy_rod(self._author.id, self.guild_id)
        await self._rerender(interaction, result.tier, result.message)

    @discord.ui.button(label="🎣 Craft from fish", style=discord.ButtonStyle.primary)
    async def craft_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        result = await fishing_workflow.craft_rod(self._author.id, self.guild_id)
        await self._rerender(interaction, result.tier, result.message)

    @discord.ui.button(label="📋 Recipes", style=discord.ButtonStyle.secondary)
    async def recipes_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        # Lazy import: rod_recipe_browser's own back button re-opens this view,
        # so importing it at module level would create a load-time cycle.
        from views.fishing.rod_recipe_browser import build_recipe_panel

        if not await safe_defer(interaction):
            return
        embed, view = await build_recipe_panel(self._author, self.guild_id)
        await safe_edit(interaction, embed=embed, view=view)
        view.message = interaction.message

    @discord.ui.button(
        label="↩ Fishing menu",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def back_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        # The menu self.stop()s when it opens this shop, so a player would be
        # stranded here — rebuild the fully-navigable menu in place. Lazy import
        # to respect the menu→shop import direction.
        from views.fishing.menu import open_fishing_menu

        self.stop()
        await open_fishing_menu(interaction, self._author, self.guild_id)
