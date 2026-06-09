"""Character overview — a read-only profile of the whole mining character.

The seed of the brainstorm §7.6 "Profile & identity" card (stat-card-first, zero
art): one embed that **aggregates, owns nothing** — position (``cogs.mining.world``),
equipped gear + its :class:`~utils.equipment.EffectiveStats` (``utils.equipment``),
coins (the economy), and inventory net worth (``cogs.mining.items``).  It reads
from each existing owner, so it grows for free as game-XP / skills / titles land.

Shared by the ``!character`` command and the hub's Character button — one builder,
no duplicate composition.  Cog-domain modules are lazy-imported (views→cogs rule).
"""

from __future__ import annotations

import discord

from utils import db, equipment
from utils.ui_constants import MINING_COLOR


async def build_character_embed(
    user_id: int,
    guild_id: int,
    *,
    name: str | None = None,
) -> discord.Embed:
    """Compose the read-only character overview for *user_id* in *guild_id*."""
    from cogs.mining import items, world

    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    equipped = await db.get_equipment(suid, guild_id)
    depth = await db.get_depth(suid, guild_id)
    coins = await db.get_coins(user_id, guild_id)
    stats = equipment.compute_stats(equipped)

    embed = discord.Embed(
        title=f"🧍 {name}'s Character" if name else "🧍 Character",
        color=MINING_COLOR,
    )
    embed.add_field(
        name="📍 Location",
        value=world.describe_position(depth),
        inline=False,
    )
    embed.add_field(
        name="🧰 Gear",
        value="\n".join(
            (
                f"**{slot.title()}**: {equipped[slot].title()}"
                if slot in equipped
                else f"**{slot.title()}**: —"
            )
            for slot in equipment.SLOTS
        ),
        inline=True,
    )
    bonuses = equipment.describe_stats(stats)
    embed.add_field(
        name="📊 Stats",
        value=(
            "\n".join(f"{label}: +{value}" for label, value in bonuses)
            if bonuses
            else "No bonuses yet — equip gear!"
        ),
        inline=True,
    )
    embed.add_field(
        name="💰 Wealth",
        value=f"**{coins}** 🪙 coins\nInventory net worth: **{items.total_value(inventory)}**",
        inline=False,
    )
    embed.set_footer(text="!equip <gear> to wear it · 🛒 Market to sell ore / buy gear")
    return embed


__all__ = ["build_character_embed"]
