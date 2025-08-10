import discord
from discord.ext import commands
import random

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Sends a random fact from the pre-loaded facts list
    @commands.command(name="fact", help="Sends a random fact.")
    async def fact(self, ctx):
        await ctx.send(random.choice(self.bot.facts))

    # Sends a random joke from the pre-loaded jokes list
    @commands.command(name="joke", help="Sends a random joke.")
    async def joke(self, ctx):
        await ctx.send(random.choice(self.bot.jokes))

    # Sends a random quote from the pre-loaded quotes list
    @commands.command(name="quote", help="Sends a random quote.")
    async def quote(self, ctx):
        await ctx.send(random.choice(self.bot.quotes))

    # Provides a random fun fact
    @commands.command(name="funfact", help="Sends a random fun fact.")
    async def funfact(self, ctx):
        fun_facts = [
            "Did you know that honey never spoils?",
            "Bananas are berries, but strawberries aren't!",
            "Octopuses have three hearts!",
            # Add more fun facts if needed
        ]
        await ctx.send(random.choice(fun_facts))

    # Asks a random trivia question
    @commands.command(name="trivia", help="Asks a random trivia question.")
    async def trivia(self, ctx):
        await ctx.send(random.choice(self.bot.trivia))

    # Sends a motivational quote
    @commands.command(name="motivate", help="Sends a motivational quote.")
    async def motivate(self, ctx):
        motivational_quotes = [
            "Believe in yourself!",
            "You can do it!",
            "Every step counts!",
            # Add more motivational quotes as needed
        ]
        await ctx.send(random.choice(motivational_quotes))

    # Magic 8-Ball style fortune telling
    @commands.command(name="eightball", aliases=["8ball"], help="Answers a yes/no question using a Magic 8-Ball.")
    async def eightball(self, ctx, *, question: str):
        responses = [
            "Yes!", "No.", "Maybe.", "Ask again later.", "It is certain.", "Definitely not."
        ]
        await ctx.send(f"🎱 {random.choice(responses)}")

    # Greets the user with a random greeting
    @commands.command(name="greet", help="Greets the user with a random greeting.")
    async def greet(self, ctx):
        greetings = ["Hello!", "Hi there!", "Greetings!", "Hey!", "What's up?"]
        await ctx.send(random.choice(greetings))

# Proper async setup function for the cog
async def setup(bot):
    await bot.add_cog(General(bot))
