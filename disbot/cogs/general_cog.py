import random

import discord
from discord.ext import commands

FACTS = [
    "Honey never spoils — archaeologists found 3000-year-old honey in Egyptian tombs.",
    "Octopuses have three hearts and blue blood.",
    "Bananas are berries, but strawberries aren't.",
    "A day on Venus is longer than a year on Venus.",
    "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid.",
    "Water can boil and freeze at the same time — this is called the triple point.",
    "The Eiffel Tower grows about 15 cm taller in summer due to thermal expansion.",
]

JOKES = [
    "Why can't skeletons fight each other? They don't have the guts.",
    "I told my doctor I broke my arm in two places. He told me to stop going to those places.",
    "Why do cows wear bells? Because their horns don't work.",
    "What do you call fake spaghetti? An impasta.",
    "I'm reading a book about anti-gravity. It's impossible to put down.",
]

QUOTES = [
    '"The only way to do great work is to love what you do." — Steve Jobs',
    '"In the middle of difficulty lies opportunity." — Albert Einstein',
    '"It does not matter how slowly you go as long as you do not stop." — Confucius',
    '"Life is what happens when you\'re busy making other plans." — John Lennon',
    '"The future belongs to those who believe in the beauty of their dreams." — Eleanor Roosevelt',
]

TRIVIA = [
    "What is the capital of Australia? || Canberra (not Sydney!)",
    "How many bones does a shark have? || Zero — sharks have no bones, only cartilage.",
    "What element does 'Au' represent on the periodic table? || Gold.",
    "How many sides does a heptagon have? || Seven.",
    "What is the fastest land animal? || The cheetah, reaching up to 120 km/h.",
]

MOTIVATIONS = [
    "Believe in yourself and all that you are!",
    "Every expert was once a beginner. Keep going.",
    "You are capable of amazing things.",
    "Small steps every day lead to big results.",
    "Difficult roads often lead to beautiful destinations.",
]

EIGHTBALL = [
    "Yes!",
    "No.",
    "Maybe.",
    "Ask again later.",
    "It is certain.",
    "Definitely not.",
    "Signs point to yes.",
    "Don't count on it.",
]

GREETINGS = ["Hello!", "Hi there!", "Greetings!", "Hey!", "What's up?"]


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="fact", help="Sends a random interesting fact.")
    async def fact(self, ctx):
        await ctx.send(random.choice(FACTS))

    @commands.command(name="joke", help="Sends a random joke.")
    async def joke(self, ctx):
        await ctx.send(random.choice(JOKES))

    @commands.command(name="quote", help="Sends a random famous quote.")
    async def quote(self, ctx):
        await ctx.send(random.choice(QUOTES))

    @commands.command(
        name="trivia", help="Asks a trivia question (answer hidden in spoiler tag)."
    )
    async def trivia(self, ctx):
        await ctx.send(random.choice(TRIVIA))

    @commands.command(name="motivate", help="Sends a motivational message.")
    async def motivate(self, ctx):
        await ctx.send(random.choice(MOTIVATIONS))

    @commands.command(
        name="eightball",
        aliases=["8ball"],
        help="Ask the Magic 8-Ball a yes/no question.",
    )
    async def eightball(self, ctx, *, question: str):
        await ctx.send(f"🎱 {random.choice(EIGHTBALL)}")

    @commands.command(name="greet", help="Greets you with a random greeting.")
    async def greet(self, ctx):
        await ctx.send(random.choice(GREETINGS))


async def setup(bot):
    await bot.add_cog(General(bot))
