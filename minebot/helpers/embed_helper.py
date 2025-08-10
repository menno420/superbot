# embed_helper.py
import discord
from discord import Embed
from datetime import datetime

def create_embed(title: str, description: str = "", color: discord.Color = discord.Color.blue(), fields: list = None, footer: str = None, thumbnail_url: str = None) -> Embed:
    embed = Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())

    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

    if footer:
        embed.set_footer(text=footer)

    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    return embed

# Quick error embed
def error_embed(description: str) -> Embed:
    return create_embed("❌ Error", description, discord.Color.red())

# Quick success embed
def success_embed(description: str) -> Embed:
    return create_embed("✅ Success", description, discord.Color.green())
