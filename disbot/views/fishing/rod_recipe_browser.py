"""Rod recipe browser — every fish→rod recipe + your live progress (S1 follow-up to #1515).

``!rodrecipes`` / the rod shop's **📋 Recipes** button open this panel. The rod
shop already advertises the *next* recipe's bare requirement ("10 fish, size ≤
6"), but never shows how close the player already is — this closes that gap:
every craftable tier (1‒``MAX_TIER``) renders with the player's current
eligible-fish count against the requirement, so a fisher can see at a glance
whether to keep grinding or set sail. Only the immediate next tier gets a live
**Craft** button, since :func:`services.fishing_workflow.craft_rod` always
crafts the rod directly above the one currently owned — further-out tiers are
shown for planning only.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import fishing_workflow
from utils import db
from utils.fishing import rods as rods_mod
from utils.ui_constants import ECONOMY_COLOR
from views.base import BaseView


def _recipe_line(
    rod: rods_mod.Rod,
    recipe: rods_mod.RodRecipe,
    eligible: int,
    *,
    owned: bool,
    is_next: bool,
) -> str:
    """One ladder line — owned (✅), the live-progress next tier (▶), or locked (🔒)."""
    if owned:
        return f"✅ {rod.emoji} **{rod.name}** — already wielded"
    target = recipe.fish_count
    progress = f"{min(eligible, target)}/{target} eligible fish"
    cutoff = f"size ≤ {recipe.max_size_rank}"
    mark = "**▶**" if is_next else "🔒"
    ready = " — ready to craft!" if is_next and eligible >= target else ""
    return f"{mark} {rod.emoji} **{rod.name}** — {progress} ({cutoff}){ready}"


def build_rod_recipe_embed(
    current_tier: int,
    eligible: dict[int, int],
    *,
    note: str | None = None,
) -> discord.Embed:
    """The recipe-browser embed — every craftable tier with live progress."""
    nxt = rods_mod.next_rod(current_tier)
    embed = discord.Embed(
        title="📋 Rod Recipes",
        description=(
            "Craft your way up the ladder from caught fish — smallest catches "
            "spend first, so your trophies are always safe. Coins remain the "
            "fast alternative (`!rod`)."
        ),
        color=ECONOMY_COLOR,
    )
    lines = []
    for rod in rods_mod.ROD_LADDER:
        recipe = rods_mod.rod_recipe(rod.tier)
        if recipe is None:  # the starter tier has no recipe
            continue
        lines.append(
            _recipe_line(
                rod,
                recipe,
                eligible.get(rod.tier, 0),
                owned=rod.tier <= current_tier,
                is_next=nxt is not None and rod.tier == nxt.tier,
            ),
        )
    embed.add_field(name="The ladder", value="\n".join(lines), inline=False)
    if note:
        embed.set_footer(text=note)
    return embed


async def _eligible_counts(user_id: int, guild_id: int) -> dict[int, int]:
    """The player's eligible-fish count toward every rod recipe, keyed by tier."""
    inventory = await db.get_mining_inventory(str(user_id), guild_id)
    return {
        tier: fishing_workflow.eligible_fish_total(inventory, recipe)
        for tier, recipe in rods_mod.ROD_RECIPES.items()
    }


async def build_recipe_panel(
    author: discord.Member | discord.User,
    guild_id: int,
) -> tuple[discord.Embed, RodRecipeBrowserView]:
    """Assemble the embed + view for the recipe browser — shared by the command and button."""
    tier = await db.get_rod_tier(author.id, guild_id)
    eligible = await _eligible_counts(author.id, guild_id)
    nxt = rods_mod.next_rod(tier)
    embed = build_rod_recipe_embed(tier, eligible)
    view = RodRecipeBrowserView(author, guild_id, at_max=nxt is None)
    return embed, view


class RodRecipeBrowserView(BaseView):
    """Author-restricted recipe-browser panel — craft-next + back to the rod shop."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
        *,
        at_max: bool,
    ) -> None:
        super().__init__(author, timeout=120)
        self.guild_id = guild_id
        self.craft_btn.disabled = at_max

    async def _rerender(
        self,
        interaction: discord.Interaction,
        tier: int,
        note: str,
    ) -> None:
        """Re-render the panel after a craft attempt and re-gate the button."""
        eligible = await _eligible_counts(self._author.id, self.guild_id)
        nxt = rods_mod.next_rod(tier)
        self.craft_btn.disabled = nxt is None
        embed = build_rod_recipe_embed(tier, eligible, note=note)
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="🎣 Craft next", style=discord.ButtonStyle.primary)
    async def craft_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        result = await fishing_workflow.craft_rod(self._author.id, self.guild_id)
        await self._rerender(interaction, result.tier, result.message)

    @discord.ui.button(
        label="↩ Rod shop",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def back_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        # The browser is opened both standalone (command) and from the rod shop
        # (button); either way, mint a fresh RodShopView to go back to. Lazy
        # import to avoid a module-load cycle (rod_shop also opens this view).
        from views.fishing.rod_shop import RodShopView, build_rod_embed

        if not await safe_defer(interaction):
            return
        tier = await db.get_rod_tier(self._author.id, self.guild_id)
        current = rods_mod.rod_for_tier(tier)
        nxt = rods_mod.next_rod(tier)
        balance = await db.get_coins(self._author.id, self.guild_id)
        embed = build_rod_embed(current, nxt, balance)
        view = RodShopView(self._author, self.guild_id, at_max=nxt is None)
        await safe_edit(interaction, embed=embed, view=view)
        view.message = interaction.message
