from __future__ import annotations

import logging
import random
import time

import discord
from discord.ext import commands

from core.runtime import panel_manager
from core.runtime.persistent_views import PersistentView, register
from utils import db
from utils.cooldowns import check_cooldown, format_remaining
from utils.helpers import post_log_embed
from utils.settings_keys import ECONOMY_LOG_CHANNEL
from utils.ui_constants import ECONOMY_COLOR, INFO_COLOR, SUCCESS_COLOR, WARNING_COLOR

logger = logging.getLogger("bot")

_WORK_COOLDOWN = 3600  # 1 hour between work sessions
_DAILY_COOLDOWN = 86400  # 24 hours between daily claims

# ---------------------------------------------------------------------------
# Daily reward tiers  (label, rarity_emoji, min, max, base_weight)
# ---------------------------------------------------------------------------
_DAILY_TIERS = [
    ("Common", "⬜", 500, 999, 45),
    ("Uncommon", "🟩", 1000, 1999, 25),
    ("Rare", "🟦", 2000, 2999, 15),
    ("Epic", "🟪", 3000, 3999, 8),
    ("Legendary", "🟧", 4000, 4999, 5),
    ("Mythic", "🟥", 5000, 5000, 2),
]


def _daily_weights(streak: int) -> list[float]:
    """Higher streak shifts weight toward better tiers (capped at 60 days of gain)."""
    luck = min(streak, 60)
    weights = [float(t[4]) for t in _DAILY_TIERS]
    shift = luck * 0.25
    take_c = min(weights[0] - 5, shift * 0.65)
    take_u = min(weights[1] - 5, shift * 0.35)
    taken = take_c + take_u
    weights[0] -= take_c
    weights[1] -= take_u
    per = taken / 4
    for i in range(2, 6):
        weights[i] += per
    return weights


def _pick_daily(streak: int) -> tuple[int, str, str]:
    """Return (amount, tier_label, rarity_emoji)."""
    weights = _daily_weights(streak)
    tier = random.choices(_DAILY_TIERS, weights=weights, k=1)[0]
    label, emoji, low, high, _ = tier
    return random.randint(low, high), label, emoji


# ---------------------------------------------------------------------------
# Job definitions  {name: {tier, pay, xp, level, items, emoji, desc}}
# ---------------------------------------------------------------------------
JOBS: dict[str, dict] = {
    # Tier 1 — no requirements
    "janitor": {
        "tier": 1,
        "pay": 50,
        "xp": 10,
        "level": 0,
        "items": [],
        "emoji": "🧹",
        "desc": "Sweep floors and empty bins.",
    },
    "cashier": {
        "tier": 1,
        "pay": 75,
        "xp": 15,
        "level": 0,
        "items": [],
        "emoji": "🏪",
        "desc": "Run the register at a store.",
    },
    "dishwasher": {
        "tier": 1,
        "pay": 60,
        "xp": 12,
        "level": 0,
        "items": [],
        "emoji": "🍽️",
        "desc": "Wash dishes at a restaurant.",
    },
    # Tier 2 — level 5+
    "security_guard": {
        "tier": 2,
        "pay": 150,
        "xp": 25,
        "level": 5,
        "items": [],
        "emoji": "🔒",
        "desc": "Guard an office building.",
    },
    "delivery_driver": {
        "tier": 2,
        "pay": 200,
        "xp": 30,
        "level": 5,
        "items": ["car"],
        "emoji": "🚗",
        "desc": "Deliver packages around town.",
    },
    "chef": {
        "tier": 2,
        "pay": 175,
        "xp": 28,
        "level": 5,
        "items": [],
        "emoji": "👨‍🍳",
        "desc": "Cook meals at a restaurant.",
    },
    # Tier 3 — level 15+
    "programmer": {
        "tier": 3,
        "pay": 400,
        "xp": 50,
        "level": 15,
        "items": [],
        "emoji": "💻",
        "desc": "Write software for clients.",
    },
    "mechanic": {
        "tier": 3,
        "pay": 350,
        "xp": 45,
        "level": 15,
        "items": ["toolkit"],
        "emoji": "🔧",
        "desc": "Repair vehicles at the garage.",
    },
    "nurse": {
        "tier": 3,
        "pay": 380,
        "xp": 48,
        "level": 15,
        "items": [],
        "emoji": "👩‍⚕️",
        "desc": "Care for patients at the clinic.",
    },
    # Tier 4 — level 30+
    "lawyer": {
        "tier": 4,
        "pay": 800,
        "xp": 80,
        "level": 30,
        "items": ["suit"],
        "emoji": "⚖️",
        "desc": "Represent clients in court.",
    },
    "doctor": {
        "tier": 4,
        "pay": 900,
        "xp": 90,
        "level": 30,
        "items": [],
        "emoji": "👨‍⚕️",
        "desc": "Treat patients at the hospital.",
    },
    "ceo": {
        "tier": 4,
        "pay": 1200,
        "xp": 100,
        "level": 50,
        "items": ["suit", "car"],
        "emoji": "👔",
        "desc": "Run your own company.",
    },
}

# ---------------------------------------------------------------------------
# Shop items
# ---------------------------------------------------------------------------
SHOP_ITEMS: dict[str, dict] = {
    "car": {
        "price": 5000,
        "emoji": "🚗",
        "desc": "Required for delivery driver and CEO.",
    },
    "toolkit": {"price": 2000, "emoji": "🔧", "desc": "Required for mechanic work."},
    "suit": {
        "price": 3000,
        "emoji": "👔",
        "desc": "Required for lawyer and CEO roles.",
    },
}


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _job_pay(job_name: str, times_worked: int) -> int:
    """Base pay × (1 + min(times_worked, 100) / 100)."""
    base = JOBS[job_name]["pay"]
    return int(base * (1 + min(times_worked, 100) / 100))


async def _available_jobs(user_id: int, guild_id: int) -> list[str]:
    """Return job names the user is currently eligible for."""
    row = await db.get_xp(user_id, guild_id)
    level = row["level"]
    inv = await db.get_inventory(user_id, guild_id)
    return [
        name
        for name, data in JOBS.items()
        if level >= data["level"] and all(item in inv for item in data["items"])
    ]


def _shop_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🛒 Item Shop",
        description="Buy items to unlock higher-tier jobs.",
        color=WARNING_COLOR,
    )
    for name, data in SHOP_ITEMS.items():
        embed.add_field(
            name=f"{data['emoji']} {name.replace('_', ' ').title()} — {data['price']:,} 🪙",
            value=data["desc"],
            inline=False,
        )
    embed.set_footer(text="Select an item from the dropdown to purchase.")
    return embed


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    @commands.command(name="economymenu")
    async def economy_menu(self, ctx: commands.Context):
        """Open the interactive economy control panel."""
        view = EconomyPanelView()
        embed = await _build_economy_embed(ctx.author, ctx.guild.id)
        await panel_manager.get_or_render_panel(ctx, "economy", embed, view)

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

    async def _ensure_log_channel(self, guild: discord.Guild) -> None:
        """Create #economy-log for *guild* if it doesn't already exist."""
        cid = await db.get_setting(guild.id, ECONOMY_LOG_CHANNEL, "")
        if cid:
            ch = guild.get_channel(int(cid))
            if ch:
                return

        existing = discord.utils.get(guild.text_channels, name="economy-log")
        if existing:
            await db.set_setting(guild.id, ECONOMY_LOG_CHANNEL, str(existing.id))
            return

        try:
            cat = discord.utils.get(guild.categories, name="Bot") or discord.utils.get(
                guild.categories,
                name="General",
            )
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
            await db.set_setting(guild.id, ECONOMY_LOG_CHANNEL, str(ch.id))
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
        row = await db.get_economy(uid, gid)
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
        new_bal = await db.add_coins(uid, gid, amount)
        await db.set_economy(
            uid,
            gid,
            last_daily=now,
            daily_streak=streak,
            daily_count=new_count,
        )

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
        row = await db.get_economy(uid, gid)

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

        view = _WorkView(ctx.author.id, ctx.guild.id, available)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    # ------------------------------------------------------------------ !shop

    @commands.command(name="shop")
    async def shop(self, ctx: commands.Context):
        """Browse and buy items from the shop."""
        view = _ShopView(ctx.author.id, ctx.guild.id)
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

    # ------------------------------------------------------------------ !setlogchannel

    @commands.command(name="setlogchannel")
    @commands.has_permissions(administrator=True)
    async def setlogchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the economy log channel. Usage: !setlogchannel #channel"""
        await db.set_setting(ctx.guild.id, ECONOMY_LOG_CHANNEL, str(channel.id))
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


# ---------------------------------------------------------------------------
# Economy Panel — stateless persistent hub
# ---------------------------------------------------------------------------


async def _build_economy_embed(
    user: discord.Member | discord.User,
    guild_id: int,
) -> discord.Embed:
    """Build the economy overview embed for *user* (stateless, no ctx needed)."""
    uid = user.id
    row = await db.get_economy(uid, guild_id)
    xp_row = await db.get_xp(uid, guild_id)
    coins = await db.get_coins(uid, guild_id)

    on_cd_work, secs_work = check_cooldown(row["last_worked"], _WORK_COOLDOWN)
    on_cd_daily, secs_daily = check_cooldown(row["last_daily"], _DAILY_COOLDOWN)

    embed = discord.Embed(title="💰 Economy Panel", color=ECONOMY_COLOR)
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    embed.add_field(name="🪙 Coins", value=f"{coins:,}", inline=True)
    embed.add_field(name="🏆 Level", value=str(xp_row["level"]), inline=True)
    embed.add_field(
        name="🔥 Daily Streak",
        value=str(row.get("daily_streak", 0)),
        inline=True,
    )
    embed.add_field(
        name="🎁 Daily",
        value=(
            "✅ Available!" if not on_cd_daily else f"⏰ {format_remaining(secs_daily)}"
        ),
        inline=True,
    )
    embed.add_field(
        name="💼 Work",
        value=(
            "✅ Available!" if not on_cd_work else f"⏰ {format_remaining(secs_work)}"
        ),
        inline=True,
    )
    embed.set_footer(text="Use the buttons below to take actions.")
    return embed


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
        uid, gid = interaction.user.id, interaction.guild_id
        now = int(time.time())
        row = await db.get_economy(uid, gid)
        last = row["last_daily"]
        streak = row["daily_streak"]

        on_cd, secs = check_cooldown(last, _DAILY_COOLDOWN)
        if on_cd:
            await interaction.response.send_message(
                f"⏰ Already claimed today! Come back in **{format_remaining(secs)}**.",
                ephemeral=True,
            )
            return

        if last > 0 and now - last > _DAILY_COOLDOWN * 2:
            streak = 0
        streak += 1

        amount, tier_label, tier_emoji = _pick_daily(streak)
        new_count = row["daily_count"] + 1
        new_bal = await db.add_coins(uid, gid, amount)
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
        await interaction.response.edit_message(embed=embed, view=self)

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
        uid, gid = interaction.user.id, interaction.guild_id
        row = await db.get_economy(uid, gid)

        on_cd, secs = check_cooldown(row["last_worked"], _WORK_COOLDOWN)
        if on_cd:
            await interaction.response.send_message(
                f"⏰ Still tired! Rest for **{format_remaining(secs)}** more.",
                ephemeral=True,
            )
            return

        available = await _available_jobs(uid, gid)
        if not available:
            await interaction.response.send_message(
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
        await interaction.response.edit_message(embed=embed, view=work_view)

    @discord.ui.button(
        label="🛒 Shop",
        style=discord.ButtonStyle.blurple,
        custom_id="economy:shop",
        row=0,
    )
    async def shop_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
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
        await interaction.response.edit_message(embed=embed, view=self)

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
        await interaction.response.edit_message(embed=embed, view=self)

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


# ---------------------------------------------------------------------------
# Work UI  (ephemeral sub-view — not persistent, no custom_id required)
# ---------------------------------------------------------------------------


class _WorkView(discord.ui.View):
    def __init__(self, user_id: int, guild_id: int, available: list[str]):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.guild_id = guild_id
        self.message: discord.Message | None = None
        self.add_item(_JobSelect(user_id, guild_id, available, self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This job menu isn't for you.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass


class _JobSelect(discord.ui.Select):
    def __init__(
        self,
        user_id: int,
        guild_id: int,
        available: list[str],
        view: _WorkView,
    ):
        self._user_id = user_id
        self._guild_id = guild_id
        self._work_view = view
        options = []
        for name in available:
            j = JOBS[name]
            options.append(
                discord.SelectOption(
                    label=f"{j['emoji']} {name.replace('_', ' ').title()}",
                    value=name,
                    description=f"Base pay: {j['pay']} 🪙  |  +{j['xp']} XP  |  Tier {j['tier']}",
                ),
            )
        super().__init__(
            placeholder="Choose a job to work…",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        job_name = self.values[0]
        uid, gid = self._user_id, self._guild_id
        now = int(time.time())

        eco = await db.get_economy(uid, gid)
        on_cd, secs = check_cooldown(eco["last_worked"], _WORK_COOLDOWN)
        if on_cd:
            await interaction.response.send_message(
                f"⏰ Still on cooldown! {format_remaining(secs)} left.",
                ephemeral=True,
            )
            return

        times = await db.get_job_times(uid, gid, job_name)
        pay = _job_pay(job_name, times)
        job = JOBS[job_name]
        xp_gain = job["xp"]

        new_times = await db.increment_job(uid, gid, job_name)
        new_bal = await db.add_coins(uid, gid, pay)
        new_xp, new_lv, lvup = await db.add_xp(uid, gid, xp_gain, now)
        await db.set_economy(uid, gid, last_worked=now)

        bonus_pct = min(times, 100)
        embed = discord.Embed(
            title=f"{job['emoji']} Work Complete — {job_name.replace('_', ' ').title()}",
            description=job["desc"],
            color=SUCCESS_COLOR,
        )
        embed.add_field(name="Earned", value=f"**+{pay}** 🪙", inline=True)
        embed.add_field(name="XP gained", value=f"**+{xp_gain}** XP", inline=True)
        embed.add_field(name="Balance", value=f"**{new_bal}** 🪙", inline=True)
        embed.add_field(
            name="Job mastery",
            value=f"{new_times}× worked (+{bonus_pct}% pay)",
            inline=True,
        )
        embed.add_field(
            name="Level",
            value=f"**{new_lv}**{'  🎉 Level up!' if lvup else ''}",
            inline=True,
        )
        embed.set_footer(text="Come back in 1 hour to work again!")

        for item in self._work_view.children:
            item.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(embed=embed, view=self._work_view)
        self._work_view.stop()

        log_embed = discord.Embed(
            title="💼 Work Completed",
            description=(
                f"{interaction.user.mention} worked as "
                f"**{job['emoji']} {job_name.replace('_', ' ').title()}**\n"
                f"Earned **+{pay}** 🪙 and **+{xp_gain}** XP"
                + ("  🎉 *Level up!*" if lvup else "")
            ),
            color=SUCCESS_COLOR,
        )
        await post_log_embed(interaction.client, gid, log_embed)


class _WorkSubView(_WorkView):
    """Work sub-panel with a Back button to return to the economy hub."""

    def __init__(self, user_id: int, guild_id: int, available: list[str]):
        super().__init__(user_id, guild_id, available)

    @discord.ui.button(label="↩ Back", style=discord.ButtonStyle.grey, row=1)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        embed = await _build_economy_embed(interaction.user, interaction.guild_id)
        await interaction.response.edit_message(embed=embed, view=EconomyPanelView())
        self.stop()


# ---------------------------------------------------------------------------
# Shop UI  (ephemeral sub-view)
# ---------------------------------------------------------------------------


class _ShopView(discord.ui.View):
    def __init__(self, user_id: int, guild_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.guild_id = guild_id
        self.message: discord.Message | None = None
        options = [
            discord.SelectOption(
                label=f"{d['emoji']} {name.replace('_', ' ').title()} — {d['price']:,} 🪙",
                value=name,
                description=d["desc"],
            )
            for name, d in SHOP_ITEMS.items()
        ]
        self.add_item(_ShopSelect(user_id, guild_id, options, self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This shop isn't for you.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass


class _ShopSelect(discord.ui.Select):
    def __init__(self, user_id: int, guild_id: int, options, view: _ShopView):
        self._user_id = user_id
        self._guild_id = guild_id
        self._shop_view = view
        super().__init__(
            placeholder="Select an item to buy…",
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        item_name = self.values[0]
        uid, gid = self._user_id, self._guild_id
        data = SHOP_ITEMS[item_name]

        if await db.has_item(uid, gid, item_name):
            await interaction.response.send_message(
                f"You already own a **{item_name}**!",
                ephemeral=True,
            )
            return

        bal = await db.get_coins(uid, gid)
        if bal < data["price"]:
            await interaction.response.send_message(
                f"❌ Need **{data['price']:,}** 🪙 — you only have **{bal:,}** 🪙.",
                ephemeral=True,
            )
            return

        new_bal = await db.add_coins(uid, gid, -data["price"])
        await db.add_item(uid, gid, item_name)

        embed = discord.Embed(
            title=f"✅ Purchased: {data['emoji']} {item_name.replace('_', ' ').title()}",
            description=f"**-{data['price']:,}** 🪙  |  New balance: **{new_bal:,}** 🪙",
            color=SUCCESS_COLOR,
        )
        await interaction.response.send_message(embed=embed)

        log_embed = discord.Embed(
            title="🛒 Shop Purchase",
            description=(
                f"{interaction.user.mention} bought "
                f"**{data['emoji']} {item_name.replace('_', ' ').title()}** "
                f"for **{data['price']:,}** 🪙"
            ),
            color=WARNING_COLOR,
        )
        await post_log_embed(interaction.client, gid, log_embed)


class _ShopSubView(discord.ui.View):
    """Shop sub-panel that edits the economy panel message — includes a Back button."""

    def __init__(self, user_id: int, guild_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.guild_id = guild_id
        self.message: discord.Message | None = None
        options = [
            discord.SelectOption(
                label=f"{d['emoji']} {name.replace('_', ' ').title()} — {d['price']:,} 🪙",
                value=name,
                description=d["desc"],
            )
            for name, d in SHOP_ITEMS.items()
        ]
        self.add_item(_ShopPanelSelect(user_id, guild_id, options, self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This panel isn't for you.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="↩ Back", style=discord.ButtonStyle.grey, row=1)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        embed = await _build_economy_embed(interaction.user, interaction.guild_id)
        await interaction.response.edit_message(embed=embed, view=EconomyPanelView())
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


class _ShopPanelSelect(discord.ui.Select):
    """Shop select that updates in-place within the economy panel flow."""

    def __init__(self, user_id: int, guild_id: int, options, view: _ShopSubView):
        self._user_id = user_id
        self._guild_id = guild_id
        self._shop_view = view
        super().__init__(placeholder="Select an item to buy…", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        item_name = self.values[0]
        uid, gid = self._user_id, self._guild_id
        data = SHOP_ITEMS[item_name]

        if await db.has_item(uid, gid, item_name):
            await interaction.response.send_message(
                f"You already own a **{item_name}**!",
                ephemeral=True,
            )
            return

        bal = await db.get_coins(uid, gid)
        if bal < data["price"]:
            await interaction.response.send_message(
                f"❌ Need **{data['price']:,}** 🪙 — you only have **{bal:,}** 🪙.",
                ephemeral=True,
            )
            return

        new_bal = await db.add_coins(uid, gid, -data["price"])
        await db.add_item(uid, gid, item_name)

        embed = discord.Embed(
            title=f"✅ Purchased: {data['emoji']} {item_name.replace('_', ' ').title()}",
            description=(
                f"**-{data['price']:,}** 🪙  |  New balance: **{new_bal:,}** 🪙\n\n"
                "Click **↩ Back** to return to the economy panel."
            ),
            color=SUCCESS_COLOR,
        )
        await interaction.response.edit_message(embed=embed, view=self._shop_view)

        log_embed = discord.Embed(
            title="🛒 Shop Purchase",
            description=(
                f"{interaction.user.mention} bought "
                f"**{data['emoji']} {item_name.replace('_', ' ').title()}** "
                f"for **{data['price']:,}** 🪙"
            ),
            color=WARNING_COLOR,
        )
        await post_log_embed(interaction.client, gid, log_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
    logger.info("EconomyCog loaded.")
