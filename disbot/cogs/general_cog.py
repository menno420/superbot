from __future__ import annotations

import json
import logging
import os
import random

import discord
from discord.ext import commands

logger = logging.getLogger("bot")

_CONTENT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "json", "general_content.json"
)

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

MOTIVATIONS = [
    "Believe in yourself and all that you are!",
    "Every expert was once a beginner. Keep going.",
    "You are capable of amazing things.",
    "Small steps every day lead to big results.",
    "Difficult roads often lead to beautiful destinations.",
]


def _load_content() -> dict:
    try:
        with open(_CONTENT_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to load general_content.json: %s", exc)
        return {}


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        content = _load_content()
        self._facts: list[str] = content.get("facts", [])
        self._jokes: list[str] = content.get("jokes", [])
        self._quotes: list[str] = content.get("quotes", [])
        self._trivia: list[str] = content.get("trivia", [])

    @commands.command(name="fact", help="Sends a random interesting fact.")
    async def fact(self, ctx):
        if not self._facts:
            await ctx.send("No facts available.")
            return
        await ctx.send(random.choice(self._facts))

    @commands.command(name="joke", help="Sends a random joke.")
    async def joke(self, ctx):
        if not self._jokes:
            await ctx.send("No jokes available.")
            return
        await ctx.send(random.choice(self._jokes))

    @commands.command(name="quote", help="Sends a random famous quote.")
    async def quote(self, ctx):
        if not self._quotes:
            await ctx.send("No quotes available.")
            return
        await ctx.send(random.choice(self._quotes))

    @commands.command(
        name="trivia", help="Asks a trivia question (answer hidden in spoiler tag)."
    )
    async def trivia(self, ctx):
        if not self._trivia:
            await ctx.send("No trivia available.")
            return
        await ctx.send(random.choice(self._trivia))

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
