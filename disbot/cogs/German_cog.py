import discord
from discord.ext import commands
import random
class GermanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gutenmorgen")
    async def guten_morgen(self, ctx):
        """Sendet eine Guten-Morgen-Nachricht."""
        await ctx.send("Guten Morgen! Ich hoffe, du hast einen wunderbaren Tag! 🌞")

    @commands.command(name="hallo")
    async def hallo(self, ctx):
        """Antwortet mit einer Begrüßung."""
        await ctx.send("Hallo! Wie geht es dir heute? 😊")

    @commands.command(name="witz")
    async def witz(self, ctx):
        """Erzählt einen Witz auf Deutsch."""
        jokes = [
            "Warum können Geister so schlecht lügen? Weil man sie durchschauen kann!",
            "Wie nennt man einen Keks unter einem Baum? Ein schattiges Plätzchen!",
            "Warum haben Pilze so gute Partys? Weil sie die besten Räume haben!"
        ]
        await ctx.send(random.choice(jokes))

    @commands.command(name="tschüss")
    async def tschuss(self, ctx):
        """Verabschiedet sich höflich."""
        await ctx.send("Tschüss! Bis bald! 👋")

async def setup(bot):
    await bot.add_cog(GermanCog(bot))