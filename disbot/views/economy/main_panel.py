"""EconomyPanelView — the persistent economy hub.

PersistentView with SUBSYSTEM="economy"; six action buttons that
route through ``services.economy_service`` for every balance
mutation.  Sub-views (work, shop) are spawned via local imports
inside the button callbacks to keep the import graph acyclic.
"""

from __future__ import annotations

import time

import discord

from cogs.economy._helpers import (
    _DAILY_COOLDOWN,
    _WORK_COOLDOWN,
    JOBS,
    _available_jobs,
    _build_economy_embed,
    _job_pay,
    _pick_daily,
    _shop_embed,
)
from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from core.runtime.persistent_views import PersistentView, register
from services import economy_service
from utils import db
from utils.cooldowns import check_cooldown, format_remaining
from utils.helpers import post_log_embed
from utils.ui_constants import ECONOMY_COLOR, INFO_COLOR


@register
class EconomyPanelView(PersistentView):
    """Persistent, stateless economy control panel hub.

    All callbacks derive user context from ``interaction`` — no ``ctx`` stored.
    Ownership is enforced by PersistentView.interaction_check via anchor lookup.
    """

    SUBSYSTEM = "economy"

    @discord.ui.button(
        label="🎁 Daily",
        style=discord.ButtonStyle.green,
        custom_id="economy:daily",
        row=0,
    )
    async def daily_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Defer first — DB reads + writes below would otherwise risk
        # exceeding the 3-second interaction window.
        if not await safe_defer(interaction):
            return

        uid, gid = interaction.user.id, interaction.guild_id
        now = int(time.time())
        row = await db.get_economy(uid, gid)
        last = row["last_daily"]
        streak = row["daily_streak"]

        on_cd, secs = check_cooldown(last, _DAILY_COOLDOWN)
        if on_cd:
            await safe_followup(
                interaction,
                f"⏰ Already claimed today! Come back in **{format_remaining(secs)}**.",
                ephemeral=True,
            )
            return

        if last > 0 and now - last > _DAILY_COOLDOWN * 2:
            streak = 0
        streak += 1

        amount, tier_label, tier_emoji = _pick_daily(streak)
        new_count = row["daily_count"] + 1
        new_bal = await economy_service.credit(
            gid,
            uid,
            amount,
            reason="daily",
            actor_id=uid,
        )
        await db.set_economy(
            uid,
            gid,
            last_daily=now,
            daily_streak=streak,
            daily_count=new_count,
        )

        embed = discord.Embed(
            title="🎁 Daily Reward",
            description=f"{tier_emoji} **{tier_label}** reward!",
            color=ECONOMY_COLOR,
        )
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )
        embed.add_field(name="Coins earned", value=f"**+{amount}** 🪙", inline=True)
        embed.add_field(name="Balance", value=f"**{new_bal}** 🪙", inline=True)
        embed.add_field(name="Streak", value=f"🔥 **{streak}** days", inline=True)
        embed.set_footer(text="Click ↩ Overview to return.")
        await safe_edit(interaction, embed=embed, view=self)

        log_embed = discord.Embed(
            title="🎁 Daily Claimed",
            description=(
                f"{interaction.user.mention} claimed **{tier_emoji} {tier_label}** "
                f"— **+{amount}** 🪙  (streak: {streak})"
            ),
            color=ECONOMY_COLOR,
        )
        await post_log_embed(interaction.client, gid, log_embed)

    @discord.ui.button(
        label="💼 Work",
        style=discord.ButtonStyle.blurple,
        custom_id="economy:work",
        row=0,
    )
    async def work_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        from views.economy.work_panel import _WorkSubView

        if not await safe_defer(interaction):
            return

        uid, gid = interaction.user.id, interaction.guild_id
        row = await db.get_economy(uid, gid)

        on_cd, secs = check_cooldown(row["last_worked"], _WORK_COOLDOWN)
        if on_cd:
            await safe_followup(
                interaction,
                f"⏰ Still tired! Rest for **{format_remaining(secs)}** more.",
                ephemeral=True,
            )
            return

        available = await _available_jobs(uid, gid)
        if not available:
            await safe_followup(
                interaction,
                "❌ No jobs available. Earn XP or buy items from 🛒 Shop.",
                ephemeral=True,
            )
            return

        xp_row = await db.get_xp(uid, gid)
        embed = discord.Embed(
            title="💼 Job Center",
            description=(
                "Choose a job below.\n"
                "Pay increases **+1%** each time you work the same job (max +100%)."
            ),
            color=INFO_COLOR,
        )
        embed.add_field(name="Level", value=str(xp_row["level"]), inline=True)
        embed.add_field(name="Coins", value=f"{xp_row.get('coins', 0)} 🪙", inline=True)
        embed.set_footer(text="Pick a job from the dropdown, or click ↩ Back.")

        work_view = _WorkSubView(uid, gid, available)
        await safe_edit(interaction, embed=embed, view=work_view)

    @discord.ui.button(
        label="🛒 Shop",
        style=discord.ButtonStyle.blurple,
        custom_id="economy:shop",
        row=0,
    )
    async def shop_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        from views.economy.shop_panel import _ShopSubView

        uid, gid = interaction.user.id, interaction.guild_id
        shop_view = _ShopSubView(uid, gid)
        await interaction.response.edit_message(embed=_shop_embed(), view=shop_view)

    @discord.ui.button(
        label="💰 Balance",
        style=discord.ButtonStyle.grey,
        custom_id="economy:balance",
        row=1,
    )
    async def balance_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        uid, gid = interaction.user.id, interaction.guild_id
        coins = await db.get_coins(uid, gid)
        xp_row = await db.get_xp(uid, gid)
        embed = discord.Embed(
            title=f"💰 {interaction.user.display_name}'s Wallet",
            color=ECONOMY_COLOR,
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="🪙 Coins", value=f"**{coins:,}**", inline=True)
        embed.add_field(name="🏆 Level", value=str(xp_row["level"]), inline=True)
        embed.set_footer(text="Click ↩ Overview to return.")
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="🎒 Inventory",
        style=discord.ButtonStyle.grey,
        custom_id="economy:inventory",
        row=1,
    )
    async def inventory_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        from cogs.inventory_cog import UnifiedInventoryView, _build_combined_inventory

        uid, gid = interaction.user.id, interaction.guild_id
        grouped = await _build_combined_inventory(uid, gid)
        view = UnifiedInventoryView(interaction.user, None, interaction.user, grouped)
        await interaction.response.send_message(embed=view.build_hub_embed(), view=view)
        view.message = await interaction.original_response()

    @discord.ui.button(
        label="📋 Jobs",
        style=discord.ButtonStyle.grey,
        custom_id="economy:jobs",
        row=1,
    )
    async def jobs_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Multiple DB reads (get_xp, get_inventory, get_job_times per job)
        # easily exceed 3 s — defer immediately.
        if not await safe_defer(interaction):
            return
        uid, gid = interaction.user.id, interaction.guild_id
        xp_row = await db.get_xp(uid, gid)
        level = xp_row["level"]
        inv = await db.get_inventory(uid, gid)

        embed = discord.Embed(title="📋 All Jobs", color=INFO_COLOR)
        tiers: dict[int, list[str]] = {}
        for name, data in JOBS.items():
            tiers.setdefault(data["tier"], []).append(name)

        for tier_num in sorted(tiers):
            lines = []
            for name in tiers[tier_num]:
                data = JOBS[name]
                times = await db.get_job_times(uid, gid, name)
                pay = _job_pay(name, times)
                unlocked = level >= data["level"] and all(
                    item in inv for item in data["items"]
                )
                lock_str = "✅" if unlocked else "🔒"
                req_parts = []
                if data["level"]:
                    req_parts.append(f"Lv{data['level']}")
                if data["items"]:
                    req_parts.append(", ".join(data["items"]))
                req = f" *(req: {', '.join(req_parts)})*" if req_parts else ""
                lines.append(
                    f"{lock_str} {data['emoji']} **{name.replace('_', ' ').title()}** "
                    f"— {pay} 🪙 / work{req}",
                )
            embed.add_field(
                name=f"Tier {tier_num}",
                value="\n".join(lines),
                inline=False,
            )

        embed.set_footer(text=f"Your level: {level}  •  Click ↩ Overview to return.")
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="↩ Overview",
        style=discord.ButtonStyle.secondary,
        custom_id="economy:overview",
        row=2,
    )
    async def overview_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        embed = await _build_economy_embed(interaction.user, interaction.guild_id)
        await interaction.response.edit_message(embed=embed, view=self)
