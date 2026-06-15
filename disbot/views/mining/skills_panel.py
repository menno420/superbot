"""Mining skills panel — the capped skill tree UI (brainstorm §7.4).

An ephemeral child of the mining hub: shows the four branches, points spent vs.
the per-branch cap, available points, and the stat preview, with a button per
branch to spend a point and a Respec button (coin sink).  Every mutation runs
through :mod:`services.skill_service` (the audited write boundary — cogs/views
never write ``player_skills`` directly); this view is only the buttons that call
it.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import game_xp_service, skill_service
from utils import db, equipment
from utils.mining import skills
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import HubView


async def build_skills_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str = "",
) -> discord.Embed:
    """The skills embed: level, available points, per-branch allocation + preview."""
    level, _, _ = await game_xp_service.level_info(guild_id, user_id)
    alloc = await db.get_skills(user_id, guild_id)
    avail = await skill_service.available_points(guild_id, user_id)

    embed = discord.Embed(title="🌳 Skill Tree", color=MINING_COLOR)
    if note:
        embed.description = note
    embed.add_field(
        name="Points",
        value=(
            f"**{avail}** available · {skills.total_spent(alloc)} spent\n"
            f"Game level **{level}** (points cap at **{skills.SOFT_TOTAL_CAP}** "
            f"— you can't max every branch, so specialize)."
        ),
        inline=False,
    )
    for branch in skills.BRANCHES:
        points = alloc.get(branch, 0)
        bonus = equipment.describe_stats(skills.branch_stats(branch, points))
        bonus_text = ", ".join(f"+{v} {label}" for label, v in bonus) or "—"
        embed.add_field(
            name=f"{skills.BRANCH_LABELS[branch]}  ({points}/{skills.PER_BRANCH_CAP})",
            value=bonus_text,
            inline=False,
        )
    respec_cost = skill_service.respec_cost(level)
    embed.set_footer(
        text=(
            "Tap a branch to spend a point  •  "
            f"♻ Respec refunds all for {respec_cost} 🪙"
        ),
    )
    return embed


class MiningSkillsView(HubView):
    """Spend-a-point-per-branch + respec panel; a child of the mining hub."""

    SUBSYSTEM = "mining"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    async def _spend(self, interaction: discord.Interaction, branch: str) -> None:
        if not await safe_defer(interaction):
            return
        result = await skill_service.allocate(self.guild_id, self._author.id, branch)
        embed = await build_skills_embed(
            self._author.id,
            self.guild_id,
            note=("✅ " if result.ok else "❌ ") + result.message,
        )
        embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="⛏️ Mining", style=discord.ButtonStyle.primary, row=0)
    async def mining_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._spend(interaction, skills.MINING)

    @discord.ui.button(label="⚔️ Combat", style=discord.ButtonStyle.primary, row=0)
    async def combat_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._spend(interaction, skills.COMBAT)

    @discord.ui.button(label="🍀 Fortune", style=discord.ButtonStyle.primary, row=0)
    async def fortune_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._spend(interaction, skills.FORTUNE)

    @discord.ui.button(label="🛠️ Crafting", style=discord.ButtonStyle.primary, row=0)
    async def crafting_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await self._spend(interaction, skills.CRAFTING)

    @discord.ui.button(label="♻ Respec", style=discord.ButtonStyle.danger, row=1)
    async def respec_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        result = await skill_service.respec(self.guild_id, self._author.id)
        embed = await build_skills_embed(
            self._author.id,
            self.guild_id,
            note=("✅ " if result.ok else "❌ ") + result.message,
        )
        embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="↩ Mining Hub", style=discord.ButtonStyle.secondary, row=1)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Late import keeps the module-load graph acyclic (the hub imports this).
        from views.mining.main_panel import MiningHubView, build_overview_embed

        embed = await build_overview_embed(
            self._author.id,
            self.guild_id,
            name=getattr(self._author, "display_name", None),
        )
        view = MiningHubView()
        await interaction.response.edit_message(embed=embed, view=view)
        self.stop()


__all__ = ["MiningSkillsView", "build_skills_embed"]
