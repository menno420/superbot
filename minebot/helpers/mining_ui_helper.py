import discord
from helpers import embed_helper
from discord import Embed
from datetime import datetime

def create_mining_embed(user, tool: dict, depth: int, loot: str = None, quantity: int = 0, xp: int = 0):
    # Format depth with sign: if positive, add a + sign; if negative, it will already have a -
    depth_str = f"+{depth}" if depth > 0 else str(depth)
    fields = [
        ("Depth", depth_str, True),
    ]
    if tool:
        tool_name = tool.get("name", "Unknown Tool")
        tool_rarity = tool.get("rarity", "Common")
        tool_durability = tool.get("durability", "?")
        fields.append(("Tool", f"{tool_name} ({tool_rarity})", True))
        fields.append(("Durability", str(tool_durability), True))
    # Tier countdown (if applicable)
    countdown, next_tier = get_next_tier_countdown(abs(depth))
    fields.append(("Next Tier", f"{countdown} more levels to Tier {next_tier}", False))
    if loot:
        fields.append(("Loot Found", f"{quantity}x {loot}", True))
        fields.append(("XP Gained", str(xp), True))
    embed = Embed(
        title=f"{user.name}'s Mining Expedition",
        description="",
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )
    for name, value, inline in fields:
        embed.add_field(name=name, value=value, inline=inline)
    embed.set_footer(text="Happy Mining!")
    return embed

def get_next_tier_countdown(depth: int):
    next_tier = (depth // 5 + 1) * 5
    remaining = next_tier - depth
    return remaining, next_tier