"""Character overview — a read-only profile of the whole mining character.

The seed of the brainstorm §7.6 "Profile & identity" card. One embed that
**aggregates, owns nothing** — position (``utils.mining.world``), equipped gear +
its :class:`~utils.equipment.EffectiveStats` (``utils.equipment``), coins (the
economy), and inventory net worth (``utils.mining.items``).  It reads from each
existing owner, so it grows for free as game-XP / skills / titles land.

The character *image* is the V-16 paper-doll (``build_character_doll`` →
``utils.character_render``) — the same figure ``!gear`` shows.  The embed keeps
gear **high-level** (equipped item names + set status, no per-slot durability):
the doll is the visual, and the detailed slot-by-slot condition view lives in
``!gear``.

Shared by the ``!character`` command and the hub's Character → Overview button —
one builder, no duplicate composition.
"""

from __future__ import annotations

import discord

from services import game_xp_service, title_service
from utils import db, equipment
from utils.mining import items, titles, workshop, world
from utils.ui_constants import MINING_COLOR


def _gear_overview(equipped: dict[str, str]) -> str:
    """High-level equipped-gear summary for the Character card.

    Item names only — no per-slot durability numbers (that detail belongs to
    ``!gear``; the paper-doll above is the gear *visual*) — plus the set-bonus
    status when one is active or in progress.
    """
    worn = [equipped[slot].title() for slot in equipment.SLOTS if equipped.get(slot)]
    if not worn:
        return "Nothing equipped yet — `!gear` to gear up."
    lines = [" · ".join(worn)]
    tier = equipment.active_set_tier(equipped)
    if tier is not None:
        lines.append(f"✨ **{tier.title()} set** — bonus active!")
    else:
        progress = equipment.set_progress(equipped)
        if progress is not None:
            lines.append(
                f"🧩 {progress[0].title()} set: "
                f"{progress[1]}/{len(equipment.SET_SLOTS)} pieces",
            )
    return "\n".join(lines)


async def build_character_embed(
    user_id: int,
    guild_id: int,
    *,
    name: str | None = None,
) -> discord.Embed:
    """Compose the read-only character overview for *user_id* in *guild_id*."""
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    equipped = await db.get_equipment(suid, guild_id)
    depth = await db.get_depth(suid, guild_id)
    max_depth = await db.get_max_depth(suid, guild_id)
    coins = await db.get_coins(user_id, guild_id)
    level, into, needed = await game_xp_service.level_info(guild_id, user_id)
    title = await title_service.equipped_title(guild_id, user_id)
    stats = equipment.compute_stats(equipped)

    embed = discord.Embed(
        title=f"🧍 {name}'s Character" if name else "🧍 Character",
        color=MINING_COLOR,
    )
    # Equipped title (Slice F) — only when one is set AND still earned; no title
    # → no field, so the card is byte-identical to the pre-titles version.
    if title is not None:
        embed.description = f"*{titles.display(title)}*"
    embed.add_field(
        name="📍 Location",
        value=(
            f"{world.describe_position(depth)}\n"
            f"Deepest: {world.describe_position(max_depth)}"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎮 Game Level",
        value=(
            f"Level **{level}** — {workshop.durability_bar(into, needed)} XP to next"
        ),
        inline=False,
    )
    embed.add_field(
        name="🧰 Gear",
        value=_gear_overview(equipped),
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
    embed.set_footer(text="!gear for slot details & condition · 🛒 Market to trade")
    return embed


async def build_character_doll(user_id: int, guild_id: int) -> bytes | None:
    """Render the player's paper-doll PNG — the same character image ``!gear``
    shows — or ``None`` without Pillow.

    The Character card's *visual*: composes the equipped loadout
    (``utils.character_render``) over the player's built-Home backdrop (Slice C).
    Callers always keep the embed and treat the doll as an additive attachment.
    """
    from utils.character_render import render_character_for
    from utils.mining import structures

    equipped = await db.get_equipment(str(user_id), guild_id)
    # Slice C: the player's built Home selects the card backdrop (0 = default).
    built = await db.get_structures(user_id, guild_id)
    return render_character_for(equipped, home_level=built.get(structures.HOME, 0))


__all__ = ["build_character_embed", "build_character_doll"]
