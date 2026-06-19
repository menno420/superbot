"""Shared economy data + helpers.

Pure-function helpers + lookup tables used by both ``cogs/economy_cog``
and the views under ``views/economy/``.  Hosted in ``services/`` (the
shared-logic layer) so the views can import them without reaching into
``cogs/`` — the layer boundary that ``views → cogs`` must not cross.
"""

from __future__ import annotations

import random

import discord

from utils import db
from utils.cooldowns import check_cooldown, format_remaining
from utils.ui_constants import ECONOMY_COLOR, WARNING_COLOR

# Cooldown configuration (seconds)
_WORK_COOLDOWN = 3600  # 1 hour between work sessions
_DAILY_COOLDOWN = 86400  # 24 hours between daily claims

# Daily reward tiers  (label, rarity_emoji, min, max, base_weight)
_DAILY_TIERS = [
    ("Common", "⬜", 500, 999, 45),
    ("Uncommon", "🟩", 1000, 1999, 25),
    ("Rare", "🟦", 2000, 2999, 15),
    ("Epic", "🟪", 3000, 3999, 8),
    ("Legendary", "🟧", 4000, 4999, 5),
    ("Mythic", "🟥", 5000, 5000, 2),
]

# Job definitions  {name: {tier, pay, xp, level, items, emoji, desc}}
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

# Shop items
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


def _daily_weights(streak: int) -> list[float]:
    """Higher streak shifts weight toward better tiers (capped at 60 days)."""
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
    """Return (amount, tier_label, rarity_emoji) for a daily claim."""
    weights = _daily_weights(streak)
    tier = random.choices(_DAILY_TIERS, weights=weights, k=1)[0]
    label, emoji, low, high, _ = tier
    return random.randint(low, high), label, emoji


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


async def _build_economy_embed(
    user: discord.Member | discord.User,
    guild_id: int,
) -> discord.Embed:
    """Build the economy overview embed for *user* (stateless, no ctx)."""
    uid = user.id
    row = await db.ensure_and_get_economy(uid, guild_id)
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
