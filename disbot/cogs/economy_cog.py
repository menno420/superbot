"""Economy subsystem — thin command dispatcher.

Persistent panel + ephemeral sub-views live under ``views.economy``.
Shared constants and helper functions (JOBS, SHOP_ITEMS, _pick_daily,
_build_economy_embed, …) live under ``cogs.economy._helpers``.

This file hosts only:
  - the EconomyCog class with its prefix commands
  - the economy-log channel lifecycle (on_ready / on_guild_join)
  - re-exports of every previously module-level public name so
    historical imports from ``cogs.economy_cog`` keep resolving.
"""

from __future__ import annotations

import logging
import time

import discord
from discord import app_commands
from discord.ext import commands

from core.runtime import panel_manager, resources
from core.runtime.interaction_helpers import safe_defer, safe_followup
from core.runtime.permission_checks import admin_or_owner
from services import economy_service
from services.economy_helpers import (
    _DAILY_COOLDOWN,
    _DAILY_TIERS,
    _WORK_COOLDOWN,
    JOBS,
    _available_jobs,
    _build_economy_embed,
    _daily_weights,
    _job_pay,
    _pick_daily,
    _shop_embed,
)
from utils import db
from utils.cooldowns import check_cooldown, format_remaining
from utils.helpers import post_log_embed
from utils.ui_constants import ECONOMY_COLOR, INFO_COLOR

# Views — importing this module triggers the @register decorator on
# EconomyPanelView, which adds it to persistent_views._REGISTRY so
# restoration on bot restart can re-attach the view.  Only the names
# this cog actually uses are imported here as of S5.2 — the unused
# back-compat re-exports of _JobSelect / _ShopPanelSelect / _ShopSelect
# / _ShopSubView / _WorkSubView have been dropped (no consumers).
from views.economy import EconomyPanelView, _ShopView, _WorkView

logger = logging.getLogger("bot")


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        from cogs.economy.schemas import register_schemas

        register_schemas()

    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    @commands.command(name="economymenu")
    async def economy_menu(self, ctx: commands.Context):
        """Open the interactive economy control panel."""
        view = EconomyPanelView()
        embed = await _build_economy_embed(ctx.author, ctx.guild.id)
        await panel_manager.get_or_render_panel(ctx, "economy", embed, view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the economy hub panel)."""
        view = EconomyPanelView()
        embed = await _build_economy_embed(interaction.user, interaction.guild_id)
        return embed, view

    @app_commands.command(
        name="economy",
        description="Open the Economy hub (daily, work, shop, balance).",
    )
    async def economy_slash(self, interaction: discord.Interaction) -> None:
        """Slash front door for the Economy hub — ephemeral.

        PR E1 — user-tier slash. Reuses
        :meth:`build_help_menu_view` so the slash entry uses the same
        panel + embed builder as the help-routed entry. Response is
        ephemeral (per the ``/help`` convention).
        """
        if not await safe_defer(interaction, ephemeral=True):
            return
        embed, view = await self.build_help_menu_view(interaction)
        await safe_followup(interaction, embed=embed, view=view, ephemeral=True)

    # ------------------------------------------------------------------ events

    @commands.Cog.listener()
    async def on_ready(self):
        """Ensure every guild the bot is in has an economy-log channel."""
        for guild in self.bot.guilds:
            await self._ensure_log_channel(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Auto-create an economy-log channel when the bot joins a new guild."""
        await self._ensure_log_channel(guild)

    async def _record_log_channel(
        self,
        guild: discord.Guild,
        channel_id: str,
        *,
        actor: discord.Member | discord.User | None,
        actor_type: str = "user",
    ) -> None:
        """Persist the economy log channel via :class:`BindingMutationPipeline`.

        P0-3 arc PR 2 retired the ``economy_log_channel`` scalar
        ``SettingSpec``; the log channel now lives in the binding lane
        (``economy.log_channel``) so there is one canonical pointer owner.
        Used by both the system-triggered ``_ensure_log_channel`` path
        (``on_ready`` / ``on_guild_join``, ``actor_type='system'``,
        ``actor=None``) and the admin ``!setlogchannel`` command
        (``actor_type='user'``, ``actor`` is the invoking member).  The
        pipeline records the change in ``binding_audit_log`` (a system
        write records the bot's own id as actor_id, since that column is
        NOT NULL — ``actor_type`` is the real discriminator).
        """
        from core.runtime.subsystem_schema import BindingKind
        from services.binding_mutation import BindingMutationPipeline

        await BindingMutationPipeline().set_binding(
            guild,
            "economy",
            "log_channel",
            BindingKind.CHANNEL,
            int(channel_id),
            actor,
            actor_type=actor_type,
        )

    async def _ensure_log_channel(self, guild: discord.Guild) -> None:
        """Create #economy-log for *guild* if it doesn't already exist."""
        from core.runtime.config_arbitration import get_economy_log_channel

        # Binding-first read (the economy_log_channel scalar was retired
        # in P0-3): a guild that already has the channel bound — or a
        # pre-migration legacy value — is left alone; only a truly
        # unconfigured guild gets one auto-created.
        configured = await get_economy_log_channel(guild.id)
        if (
            configured.value is not None
            and guild.get_channel(configured.value) is not None
        ):
            return

        existing = resources.resolve_channel(guild, name="economy-log")
        if existing:
            await self._record_log_channel(
                guild,
                str(existing.id),
                actor=None,
                actor_type="system",
            )
            return

        try:
            cat = resources.resolve_channel(
                guild,
                name="Bot",
                kind="category",
            ) or resources.resolve_channel(guild, name="General", kind="category")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=False,
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                ),
            }
            ch = await guild.create_text_channel(
                "economy-log",
                overwrites=overwrites,  # type: ignore[arg-type]
                category=cat,
                topic="Live feed of XP level-ups, daily rewards, work earnings, and shop purchases.",
            )
            await self._record_log_channel(
                guild,
                str(ch.id),
                actor=None,
                actor_type="system",
            )
            embed = discord.Embed(
                title="📊 Economy Log",
                description=(
                    "This channel will automatically log:\n"
                    "🏆 Level-ups  •  🎁 Daily rewards  •  💼 Work earnings  •  🛒 Shop purchases\n\n"
                    "Admins can move it with `!setlogchannel #channel`."
                ),
                color=ECONOMY_COLOR,
            )
            await ch.send(embed=embed)
            logger.info("Created economy-log channel in %s", guild.name)
        except discord.Forbidden:
            pass
        except Exception as e:
            logger.error("economy-log creation failed in %s: %s", guild.name, e)

    # ------------------------------------------------------------------ !daily

    @commands.cooldown(rate=2, per=5, type=commands.BucketType.user)
    @commands.command(name="daily")
    async def daily(self, ctx: commands.Context):
        """Claim your daily reward. Higher streaks unlock better odds!"""
        uid, gid = ctx.author.id, ctx.guild.id
        now = int(time.time())
        row = await db.ensure_and_get_economy(uid, gid)
        last = row["last_daily"]
        streak = row["daily_streak"]

        on_cd, secs = check_cooldown(last, _DAILY_COOLDOWN)
        if on_cd:
            await ctx.send(
                f"⏰ Already claimed today! Come back in **{format_remaining(secs)}**.",
                delete_after=10,
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

        weights = _daily_weights(streak)
        chance_preview = " · ".join(
            f"{t[0]}: {w:.1f}%" for t, w in zip(_DAILY_TIERS, weights, strict=True)
        )

        embed = discord.Embed(
            title="🎁 Daily Reward",
            description=f"{tier_emoji} **{tier_label}** reward!",
            color=ECONOMY_COLOR,
        )
        embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.display_avatar.url,
        )
        embed.add_field(name="Coins earned", value=f"**+{amount}** 🪙", inline=True)
        embed.add_field(name="Balance", value=f"**{new_bal}** 🪙", inline=True)
        embed.add_field(name="Streak", value=f"🔥 **{streak}** days", inline=True)
        embed.add_field(name="Total claims", value=str(new_count), inline=True)
        embed.set_footer(text=f"Current odds → {chance_preview}")
        await ctx.send(embed=embed)

        log_embed = discord.Embed(
            title="🎁 Daily Claimed",
            description=(
                f"{ctx.author.mention} claimed **{tier_emoji} {tier_label}** "
                f"— **+{amount}** 🪙  (streak: {streak})"
            ),
            color=ECONOMY_COLOR,
        )
        await post_log_embed(self.bot, gid, log_embed)

    # ------------------------------------------------------------------ !work

    @commands.cooldown(rate=2, per=5, type=commands.BucketType.user)
    @commands.command(name="work")
    async def work(self, ctx: commands.Context):
        """Open the job selector and earn coins + XP (1 h cooldown)."""
        uid, gid = ctx.author.id, ctx.guild.id
        row = await db.ensure_and_get_economy(uid, gid)

        on_cd, secs = check_cooldown(row["last_worked"], _WORK_COOLDOWN)
        if on_cd:
            await ctx.send(
                f"⏰ You're tired! Rest for **{format_remaining(secs)}** more.",
                delete_after=10,
            )
            return

        available = await _available_jobs(uid, gid)
        if not available:
            await ctx.send(
                "❌ No jobs available yet. Earn XP to unlock higher-tier jobs "
                "or buy required items from `!shop`.",
                delete_after=12,
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
        embed.set_footer(text="Pick a job from the dropdown.")

        view = _WorkView(ctx.author, ctx.guild.id, available)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    # ------------------------------------------------------------------ !shop

    @commands.command(name="shop")
    async def shop(self, ctx: commands.Context):
        """Browse and buy items from the shop."""
        view = _ShopView(ctx.author, ctx.guild.id)
        msg = await ctx.send(embed=_shop_embed(), view=view)
        view.message = msg

    # ------------------------------------------------------------------ !balance

    @commands.command(name="balance", aliases=["bal", "wallet"])
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        """Show your (or another user's) current coin balance."""
        target = member or ctx.author
        coins = await db.get_coins(target.id, ctx.guild.id)
        xp_row = await db.get_xp(target.id, ctx.guild.id)
        embed = discord.Embed(
            title=f"💰 {target.display_name}'s Wallet",
            color=ECONOMY_COLOR,
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🪙 Coins", value=f"**{coins:,}**", inline=True)
        embed.add_field(name="🏆 Level", value=str(xp_row["level"]), inline=True)
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------ !pay

    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    @commands.command(name="pay", aliases=["transfer"])
    async def pay(
        self,
        ctx: commands.Context,
        member: discord.Member = None,
        amount: int = None,
    ):
        """Send coins to another member. Usage: !pay @user <amount>"""
        if member is None or amount is None:
            await ctx.send("Usage: `!pay @user <amount>`", delete_after=10)
            return
        if member.bot:
            await ctx.send("❌ You can't pay a bot.", delete_after=10)
            return
        if member.id == ctx.author.id:
            await ctx.send("❌ You can't pay yourself.", delete_after=10)
            return
        if amount <= 0:
            await ctx.send("❌ Amount must be positive.", delete_after=10)
            return
        gid = ctx.guild.id
        try:
            new_from, new_to = await economy_service.transfer(
                gid,
                ctx.author.id,
                member.id,
                amount,
                reason="gift",
                actor_id=ctx.author.id,
            )
        except economy_service.InsufficientFundsError:
            coins = await db.get_coins(ctx.author.id, gid)
            await ctx.send(
                f"❌ Not enough coins — you have **{coins:,}** 🪙, "
                f"tried to send **{amount:,}** 🪙.",
                delete_after=10,
            )
            return

        embed = discord.Embed(
            title="💸 Payment sent",
            description=f"{ctx.author.mention} → {member.mention}",
            color=ECONOMY_COLOR,
        )
        embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.display_avatar.url,
        )
        embed.add_field(name="Amount", value=f"**{amount:,}** 🪙", inline=True)
        embed.add_field(name="Your balance", value=f"**{new_from:,}** 🪙", inline=True)
        embed.add_field(
            name=f"{member.display_name}'s balance",
            value=f"**{new_to:,}** 🪙",
            inline=True,
        )
        await ctx.send(embed=embed)

        log_embed = discord.Embed(
            title="💸 Coins transferred",
            description=(
                f"{ctx.author.mention} paid {member.mention} **{amount:,}** 🪙"
            ),
            color=ECONOMY_COLOR,
        )
        await post_log_embed(self.bot, gid, log_embed)

    # ------------------------------------------------------------------ !setlogchannel

    @commands.command(name="setlogchannel")
    @admin_or_owner()
    async def setlogchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the economy log channel. Usage: !setlogchannel #channel"""
        await self._record_log_channel(
            ctx.guild,
            str(channel.id),
            actor=ctx.author,
        )
        await ctx.send(f"✅ Economy log channel set to {channel.mention}.")

    # ------------------------------------------------------------------ !joblist

    @commands.command(name="joblist", aliases=["jobs"])
    async def joblist(self, ctx: commands.Context):
        """Show all jobs, requirements, and your mastery for each."""
        uid, gid = ctx.author.id, ctx.guild.id
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
                mastery = f" | mastery {times}/100" if times else ""
                lines.append(
                    f"{lock_str} {data['emoji']} **{name.replace('_', ' ').title()}** "
                    f"— {pay} 🪙 / work{req}{mastery}",
                )
            embed.add_field(
                name=f"Tier {tier_num}",
                value="\n".join(lines),
                inline=False,
            )
        embed.set_footer(
            text=f"Your level: {level}  |  Pay shown includes mastery bonus.",
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
