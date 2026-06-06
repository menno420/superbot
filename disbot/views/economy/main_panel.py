"""EconomyPanelView — the persistent economy hub.

PersistentView with SUBSYSTEM="economy"; six action buttons that
route through ``services.economy_service`` for every balance
mutation.  Sub-views (work, shop) are spawned via local imports
inside the button callbacks to keep the import graph acyclic.

Also exports :func:`attach_back_to_economy_button`, mirroring the
sibling helpers
:func:`disbot.cogs.help_cog._attach_back_to_help_button`,
:func:`disbot.cogs.admin_cog.attach_back_to_admin_button`,
:func:`disbot.views.settings.subsystem_view.attach_back_to_settings_button`,
and :func:`disbot.views.games.hub.attach_back_to_games_button`.
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
from views.navigation import BackTarget, attach_back_button, chain_back


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
        await db.set_daily_claim(uid, gid, now, streak, new_count)

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

        work_view = _WorkSubView(
            uid,
            gid,
            available,
            back_target=getattr(self, "_back_target", None),
        )
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
        # AB2: propagate this panel's back target (e.g. back-to-Help)
        # so the shop's Back button rebuilds Economy with the chain
        # re-attached.
        shop_view._back_target = getattr(self, "_back_target", None)
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

        if not await safe_defer(interaction):
            return

        uid, gid = interaction.user.id, interaction.guild_id
        grouped = await _build_combined_inventory(uid, gid)
        view = UnifiedInventoryView(interaction.user, interaction.user, grouped)
        # AB2: forward this panel's own back target (back-to-Help if
        # opened via /help economy) so back-to-Economy from Inventory
        # rebuilds Economy WITH back-to-Help re-attached.
        attach_back_to_economy_button(
            view,
            interaction.user,
            grandparent=getattr(self, "_back_target", None),
        )
        await safe_edit(interaction, embed=view.build_hub_embed(), view=view)
        view.message = interaction.message

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


def attach_back_to_economy_button(
    view: discord.ui.View,
    author: discord.Member | discord.User,
    *,
    grandparent: BackTarget | None = None,
) -> bool:
    """Append a "↩ Back to Economy" control to a child view opened from the hub.

    Thin wrapper around :func:`views.navigation.attach_back_button`. The
    parent-builder closure rebuilds a fresh :class:`EconomyPanelView` on
    click so the persistent hub reflects current state, not a snapshot.

    AB2: when ``grandparent`` is supplied (typically Help's own
    :class:`BackTarget`), :func:`views.navigation.chain_back` wraps the
    builder so the rebuilt Economy panel also gets the grandparent
    re-attached. This is how Help → Economy → Inventory → Back
    preserves back-to-Help on the rebuilt Economy.

    Also stashes ``view._back_target`` for further-down openers (e.g.
    a Category view inside Inventory) to chain back through Economy.

    Returns ``False`` (no-op) if the view is already at Discord's 25-component
    cap — ``attach_back_button`` logs a WARNING in that case so operators can
    see why a panel lost its back nav.
    """

    async def _build_economy_parent(
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        embed = await _build_economy_embed(author, interaction.guild_id)
        return embed, EconomyPanelView()

    composed_builder = chain_back(_build_economy_parent, grandparent)
    added = attach_back_button(
        view,
        label="↩ Back to Economy",
        custom_id="economy:back",
        parent_builder=composed_builder,
        row=4,
        style=discord.ButtonStyle.secondary,
        error_message="Could not reload the Economy hub. Please try again.",
    )
    view._back_target = BackTarget(  # type: ignore[attr-defined]
        builder=composed_builder,
        label="↩ Back to Economy",
        custom_id="economy:back",
    )
    return added


__all__ = ["EconomyPanelView", "attach_back_to_economy_button"]
