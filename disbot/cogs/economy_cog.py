from __future__ import annotations
import time
import random
import discord
from discord.ext import commands
import logging
from utils import db

logger = logging.getLogger("bot")

_WORK_COOLDOWN  = 3600   # 1 hour between work sessions
_DAILY_COOLDOWN = 86400  # 24 hours between daily claims

# ---------------------------------------------------------------------------
# Daily reward tiers  (label, rarity_emoji, min, max, base_weight)
# ---------------------------------------------------------------------------
_DAILY_TIERS = [
    ("Common",    "⬜", 500,  999,  45),
    ("Uncommon",  "🟩", 1000, 1999, 25),
    ("Rare",      "🟦", 2000, 2999, 15),
    ("Epic",      "🟪", 3000, 3999,  8),
    ("Legendary", "🟧", 4000, 4999,  5),
    ("Mythic",    "🟥", 5000, 5000,  2),
]


def _daily_weights(streak: int) -> list[float]:
    """Higher streak shifts weight toward better tiers (capped at 60 days of gain)."""
    luck = min(streak, 60)
    weights = [float(t[4]) for t in _DAILY_TIERS]
    # Each day of streak moves 0.25 total weight from bottom tiers to top tiers
    shift = luck * 0.25
    take_c = min(weights[0] - 5, shift * 0.65)
    take_u = min(weights[1] - 5, shift * 0.35)
    taken  = take_c + take_u
    weights[0] -= take_c
    weights[1] -= take_u
    per = taken / 4
    for i in range(2, 6):
        weights[i] += per
    return weights


def _pick_daily(streak: int) -> tuple[int, str, str]:
    """Return (amount, tier_label, rarity_emoji)."""
    weights = _daily_weights(streak)
    tier    = random.choices(_DAILY_TIERS, weights=weights, k=1)[0]
    label, emoji, low, high, _ = tier
    return random.randint(low, high), label, emoji


# ---------------------------------------------------------------------------
# Job definitions  {name: {tier, pay, xp, level, items, emoji, desc}}
# ---------------------------------------------------------------------------
JOBS: dict[str, dict] = {
    # Tier 1 — no requirements
    "janitor":         {"tier": 1, "pay": 50,   "xp": 10,  "level": 0,  "items": [],              "emoji": "🧹",  "desc": "Sweep floors and empty bins."},
    "cashier":         {"tier": 1, "pay": 75,   "xp": 15,  "level": 0,  "items": [],              "emoji": "🏪",  "desc": "Run the register at a store."},
    "dishwasher":      {"tier": 1, "pay": 60,   "xp": 12,  "level": 0,  "items": [],              "emoji": "🍽️", "desc": "Wash dishes at a restaurant."},
    # Tier 2 — level 5+
    "security_guard":  {"tier": 2, "pay": 150,  "xp": 25,  "level": 5,  "items": [],              "emoji": "🔒",  "desc": "Guard an office building."},
    "delivery_driver": {"tier": 2, "pay": 200,  "xp": 30,  "level": 5,  "items": ["car"],         "emoji": "🚗",  "desc": "Deliver packages around town."},
    "chef":            {"tier": 2, "pay": 175,  "xp": 28,  "level": 5,  "items": [],              "emoji": "👨‍🍳", "desc": "Cook meals at a restaurant."},
    # Tier 3 — level 15+
    "programmer":      {"tier": 3, "pay": 400,  "xp": 50,  "level": 15, "items": [],              "emoji": "💻",  "desc": "Write software for clients."},
    "mechanic":        {"tier": 3, "pay": 350,  "xp": 45,  "level": 15, "items": ["toolkit"],     "emoji": "🔧",  "desc": "Repair vehicles at the garage."},
    "nurse":           {"tier": 3, "pay": 380,  "xp": 48,  "level": 15, "items": [],              "emoji": "👩‍⚕️", "desc": "Care for patients at the clinic."},
    # Tier 4 — level 30+
    "lawyer":          {"tier": 4, "pay": 800,  "xp": 80,  "level": 30, "items": ["suit"],        "emoji": "⚖️",  "desc": "Represent clients in court."},
    "doctor":          {"tier": 4, "pay": 900,  "xp": 90,  "level": 30, "items": [],              "emoji": "👨‍⚕️", "desc": "Treat patients at the hospital."},
    "ceo":             {"tier": 4, "pay": 1200, "xp": 100, "level": 50, "items": ["suit", "car"], "emoji": "👔",  "desc": "Run your own company."},
}

# ---------------------------------------------------------------------------
# Shop items
# ---------------------------------------------------------------------------
SHOP_ITEMS: dict[str, dict] = {
    "car":     {"price": 5000, "emoji": "🚗", "desc": "Required for delivery driver and CEO."},
    "toolkit": {"price": 2000, "emoji": "🔧", "desc": "Required for mechanic work."},
    "suit":    {"price": 3000, "emoji": "👔", "desc": "Required for lawyer and CEO roles."},
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
    row   = await db.get_xp(user_id, guild_id)
    level = row["level"]
    inv   = await db.get_inventory(user_id, guild_id)
    return [
        name for name, data in JOBS.items()
        if level >= data["level"] and all(item in inv for item in data["items"])
    ]


async def post_economy_log(bot: commands.Bot, guild_id: int, embed: discord.Embed) -> None:
    """Post an economy event embed to the guild's configured log channel."""
    cid = await db.get_setting(guild_id, "economy_log_channel", "")
    if not cid:
        return
    ch = bot.get_channel(int(cid))
    if ch:
        try:
            await ch.send(embed=embed)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------

class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
        cid = await db.get_setting(guild.id, "economy_log_channel", "")
        if cid:
            ch = guild.get_channel(int(cid))
            if ch:
                return  # channel still exists, nothing to do

        # on_ready can fire on every reconnect — check by name before creating
        existing = discord.utils.get(guild.text_channels, name="economy-log")
        if existing:
            await db.set_setting(guild.id, "economy_log_channel", str(existing.id))
            return

        try:
            cat = (discord.utils.get(guild.categories, name="Bot")
                   or discord.utils.get(guild.categories, name="General"))
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    read_messages=True, send_messages=False
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                ),
            }
            ch = await guild.create_text_channel(
                "economy-log",
                overwrites=overwrites,
                category=cat,
                topic="Live feed of XP level-ups, daily rewards, work earnings, and shop purchases.",
            )
            await db.set_setting(guild.id, "economy_log_channel", str(ch.id))
            embed = discord.Embed(
                title="📊 Economy Log",
                description=(
                    "This channel will automatically log:\n"
                    "🏆 Level-ups  •  🎁 Daily rewards  •  💼 Work earnings  •  🛒 Shop purchases\n\n"
                    "Admins can move it with `!setlogchannel #channel`."
                ),
                color=discord.Color.gold(),
            )
            await ch.send(embed=embed)
            logger.info("Created economy-log channel in %s", guild.name)
        except discord.Forbidden:
            pass
        except Exception as e:
            logger.error("economy-log creation failed in %s: %s", guild.name, e)

    # ------------------------------------------------------------------ !daily

    @commands.command(name="daily")
    async def daily(self, ctx: commands.Context):
        """Claim your daily reward. Higher streaks unlock better odds!"""
        uid, gid = ctx.author.id, ctx.guild.id
        now  = int(time.time())
        row  = await db.get_economy(uid, gid)
        last = row["last_daily"]
        streak = row["daily_streak"]

        if now - last < _DAILY_COOLDOWN:
            remaining = _DAILY_COOLDOWN - (now - last)
            h, m = divmod(remaining // 60, 60)
            await ctx.send(
                f"⏰ Already claimed today! Come back in **{h}h {m}m**.",
                delete_after=10,
            )
            return

        # Reset streak if more than 48 h have passed since last claim
        if last > 0 and now - last > _DAILY_COOLDOWN * 2:
            streak = 0
        streak += 1

        amount, tier_label, tier_emoji = _pick_daily(streak)
        new_count = row["daily_count"] + 1
        new_bal   = await db.add_coins(uid, gid, amount)
        await db.set_economy(uid, gid,
                             last_daily=now,
                             daily_streak=streak,
                             daily_count=new_count)

        weights = _daily_weights(streak)
        chance_preview = " · ".join(
            f"{t[0]}: {w:.1f}%" for t, w in zip(_DAILY_TIERS, weights)
        )

        embed = discord.Embed(
            title="🎁 Daily Reward",
            description=f"{tier_emoji} **{tier_label}** reward!",
            color=discord.Color.gold(),
        )
        embed.set_author(name=ctx.author.display_name,
                         icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Coins earned",  value=f"**+{amount}** 🪙",    inline=True)
        embed.add_field(name="Balance",       value=f"**{new_bal}** 🪙",    inline=True)
        embed.add_field(name="Streak",        value=f"🔥 **{streak}** days", inline=True)
        embed.add_field(name="Total claims",  value=str(new_count),          inline=True)
        embed.set_footer(text=f"Current odds → {chance_preview}")
        await ctx.send(embed=embed)

        log_embed = discord.Embed(
            title="🎁 Daily Claimed",
            description=(
                f"{ctx.author.mention} claimed **{tier_emoji} {tier_label}** "
                f"— **+{amount}** 🪙  (streak: {streak})"
            ),
            color=discord.Color.gold(),
        )
        await post_economy_log(self.bot, gid, log_embed)

    # ------------------------------------------------------------------ !work

    @commands.command(name="work")
    async def work(self, ctx: commands.Context):
        """Open the job selector and earn coins + XP (1 h cooldown)."""
        uid, gid = ctx.author.id, ctx.guild.id
        now  = int(time.time())
        row  = await db.get_economy(uid, gid)

        if now - row["last_worked"] < _WORK_COOLDOWN:
            remaining = (_WORK_COOLDOWN - (now - row["last_worked"])) // 60
            await ctx.send(f"⏰ You're tired! Rest for **{remaining}m** more.", delete_after=10)
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
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Level",  value=str(xp_row["level"]),             inline=True)
        embed.add_field(name="Coins",  value=f"{xp_row.get('coins', 0)} 🪙",  inline=True)
        embed.set_footer(text="Pick a job from the dropdown.")

        view = _WorkView(ctx, available)
        msg  = await ctx.send(embed=embed, view=view)
        view.message = msg

    # ------------------------------------------------------------------ !shop

    @commands.command(name="shop")
    async def shop(self, ctx: commands.Context):
        """Browse and buy items from the shop."""
        view = _ShopView(ctx)
        msg  = await ctx.send(embed=_shop_embed(), view=view)
        view.message = msg

    # ------------------------------------------------------------------ !inventory

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx: commands.Context, member: discord.Member = None):
        """Show your (or another user's) inventory."""
        target = member or ctx.author
        inv = await db.get_inventory(target.id, ctx.guild.id)
        embed = discord.Embed(
            title=f"🎒 {target.display_name}'s Inventory",
            color=discord.Color.blurple(),
        )
        if inv:
            lines = []
            for item_name, qty in inv.items():
                data  = SHOP_ITEMS.get(item_name, {})
                emoji = data.get("emoji", "📦")
                lines.append(f"{emoji} **{item_name.replace('_', ' ').title()}** × {qty}")
            embed.description = "\n".join(lines)
        else:
            embed.description = "Empty — visit `!shop` to buy items!"
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------ !balance

    @commands.command(name="balance", aliases=["bal", "wallet"])
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        """Show your (or another user's) current coin balance."""
        target = member or ctx.author
        coins = await db.get_coins(target.id, ctx.guild.id)
        xp_row = await db.get_xp(target.id, ctx.guild.id)
        embed = discord.Embed(
            title=f"💰 {target.display_name}'s Wallet",
            color=discord.Color.gold(),
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
        await db.set_setting(ctx.guild.id, "economy_log_channel", str(channel.id))
        await ctx.send(f"✅ Economy log channel set to {channel.mention}.")

    # ------------------------------------------------------------------ !joblist

    @commands.command(name="joblist", aliases=["jobs"])
    async def joblist(self, ctx: commands.Context):
        """Show all jobs, requirements, and your mastery for each."""
        uid, gid = ctx.author.id, ctx.guild.id
        xp_row   = await db.get_xp(uid, gid)
        level    = xp_row["level"]
        inv      = await db.get_inventory(uid, gid)

        embed = discord.Embed(title="📋 All Jobs", color=discord.Color.blurple())
        tiers: dict[int, list[str]] = {}
        for name, data in JOBS.items():
            tiers.setdefault(data["tier"], []).append(name)

        for tier_num in sorted(tiers):
            lines = []
            for name in tiers[tier_num]:
                data  = JOBS[name]
                times = await db.get_job_times(uid, gid, name)
                pay   = _job_pay(name, times)
                unlocked = (level >= data["level"]
                            and all(item in inv for item in data["items"]))
                lock_str = "✅" if unlocked else "🔒"
                req_parts = []
                if data["level"]: req_parts.append(f"Lv{data['level']}")
                if data["items"]: req_parts.append(", ".join(data["items"]))
                req = f" *(req: {', '.join(req_parts)})*" if req_parts else ""
                mastery = f" | mastery {times}/100" if times else ""
                lines.append(
                    f"{lock_str} {data['emoji']} **{name.replace('_', ' ').title()}** "
                    f"— {pay} 🪙 / work{req}{mastery}"
                )
            embed.add_field(
                name=f"Tier {tier_num}",
                value="\n".join(lines),
                inline=False,
            )
        embed.set_footer(text=f"Your level: {level}  |  Pay shown includes mastery bonus.")
        await ctx.send(embed=embed)


# ---------------------------------------------------------------------------
# Work UI
# ---------------------------------------------------------------------------

class _WorkView(discord.ui.View):
    def __init__(self, ctx: commands.Context, available: list[str]):
        super().__init__(timeout=60)
        self.ctx     = ctx
        self.message: discord.Message | None = None
        self.add_item(_JobSelect(ctx, available, self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "This job menu isn't for you.", ephemeral=True)
            return False
        return True

    _run_checks = interaction_check

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass


class _JobSelect(discord.ui.Select):
    def __init__(self, ctx: commands.Context, available: list[str], view: _WorkView):
        self._ctx        = ctx
        self._work_view  = view
        options = []
        for name in available:
            j = JOBS[name]
            options.append(discord.SelectOption(
                label=f"{j['emoji']} {name.replace('_', ' ').title()}",
                value=name,
                description=f"Base pay: {j['pay']} 🪙  |  +{j['xp']} XP  |  Tier {j['tier']}",
            ))
        super().__init__(
            placeholder="Choose a job to work…",
            min_values=1, max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        job_name = self.values[0]
        uid, gid = self._ctx.author.id, self._ctx.guild.id
        now      = int(time.time())

        # Re-check cooldown (guard against double-click)
        eco = await db.get_economy(uid, gid)
        if now - eco["last_worked"] < _WORK_COOLDOWN:
            remaining = (_WORK_COOLDOWN - (now - eco["last_worked"])) // 60
            await interaction.response.send_message(
                f"⏰ Still on cooldown! {remaining}m left.", ephemeral=True)
            return

        times   = await db.get_job_times(uid, gid, job_name)
        pay     = _job_pay(job_name, times)
        job     = JOBS[job_name]
        xp_gain = job["xp"]

        new_times             = await db.increment_job(uid, gid, job_name)
        new_bal               = await db.add_coins(uid, gid, pay)
        new_xp, new_lv, lvup = await db.add_xp(uid, gid, xp_gain, now)
        await db.set_economy(uid, gid, last_worked=now)

        bonus_pct = min(times, 100)
        embed = discord.Embed(
            title=f"{job['emoji']} Work Complete — {job_name.replace('_', ' ').title()}",
            description=job["desc"],
            color=discord.Color.green(),
        )
        embed.add_field(name="Earned",      value=f"**+{pay}** 🪙",                  inline=True)
        embed.add_field(name="XP gained",   value=f"**+{xp_gain}** XP",              inline=True)
        embed.add_field(name="Balance",     value=f"**{new_bal}** 🪙",               inline=True)
        embed.add_field(name="Job mastery", value=f"{new_times}× worked (+{bonus_pct}% pay)", inline=True)
        embed.add_field(name="Level",       value=f"**{new_lv}**{'  🎉 Level up!' if lvup else ''}", inline=True)
        embed.set_footer(text="Come back in 1 hour to work again!")

        for item in self._work_view.children:
            item.disabled = True
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
            color=discord.Color.green(),
        )
        await post_economy_log(self._ctx.bot, gid, log_embed)


# ---------------------------------------------------------------------------
# Shop UI
# ---------------------------------------------------------------------------

def _shop_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🛒 Item Shop",
        description="Buy items to unlock higher-tier jobs.",
        color=discord.Color.orange(),
    )
    for name, data in SHOP_ITEMS.items():
        embed.add_field(
            name=f"{data['emoji']} {name.replace('_', ' ').title()} — {data['price']:,} 🪙",
            value=data["desc"],
            inline=False,
        )
    embed.set_footer(text="Select an item from the dropdown to purchase.")
    return embed


class _ShopView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=120)
        self.ctx     = ctx
        self.message: discord.Message | None = None
        options = [
            discord.SelectOption(
                label=f"{d['emoji']} {name.replace('_', ' ').title()} — {d['price']:,} 🪙",
                value=name,
                description=d["desc"],
            )
            for name, d in SHOP_ITEMS.items()
        ]
        self.add_item(_ShopSelect(ctx, options, self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "This shop isn't for you.", ephemeral=True)
            return False
        return True

    _run_checks = interaction_check

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass


class _ShopSelect(discord.ui.Select):
    def __init__(self, ctx: commands.Context, options, view: _ShopView):
        self._ctx        = ctx
        self._shop_view  = view
        super().__init__(
            placeholder="Select an item to buy…",
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        item_name = self.values[0]
        uid, gid  = self._ctx.author.id, self._ctx.guild.id
        data      = SHOP_ITEMS[item_name]

        if await db.has_item(uid, gid, item_name):
            await interaction.response.send_message(
                f"You already own a **{item_name}**!", ephemeral=True)
            return

        bal = await db.get_coins(uid, gid)
        if bal < data["price"]:
            await interaction.response.send_message(
                f"❌ Need **{data['price']:,}** 🪙 — you only have **{bal:,}** 🪙.",
                ephemeral=True)
            return

        new_bal = await db.add_coins(uid, gid, -data["price"])
        await db.add_item(uid, gid, item_name)

        embed = discord.Embed(
            title=f"✅ Purchased: {data['emoji']} {item_name.replace('_', ' ').title()}",
            description=f"**-{data['price']:,}** 🪙  |  New balance: **{new_bal:,}** 🪙",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)

        log_embed = discord.Embed(
            title="🛒 Shop Purchase",
            description=(
                f"{interaction.user.mention} bought "
                f"**{data['emoji']} {item_name.replace('_', ' ').title()}** "
                f"for **{data['price']:,}** 🪙"
            ),
            color=discord.Color.orange(),
        )
        await post_economy_log(self._ctx.bot, gid, log_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
    logger.info("EconomyCog loaded.")
