from __future__ import annotations

import json
import logging
import os
import random

import discord
from discord.ext import commands
from utils.ui_constants import GENERAL_COLOR, SUCCESS_COLOR
from views.base import BaseView

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
        embed = discord.Embed(
            title="💡 Random Fact",
            description=random.choice(self._facts),
            color=GENERAL_COLOR,
        )
        await ctx.send(embed=embed)

    @commands.command(name="joke", help="Sends a random joke.")
    async def joke(self, ctx):
        if not self._jokes:
            await ctx.send("No jokes available.")
            return
        embed = discord.Embed(
            title="😄 Random Joke",
            description=random.choice(self._jokes),
            color=GENERAL_COLOR,
        )
        await ctx.send(embed=embed)

    @commands.command(name="quote", help="Sends a random famous quote.")
    async def quote(self, ctx):
        if not self._quotes:
            await ctx.send("No quotes available.")
            return
        embed = discord.Embed(
            title="💬 Quote",
            description=random.choice(self._quotes),
            color=GENERAL_COLOR,
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="trivia", help="Asks a trivia question with a reveal button."
    )
    async def trivia(self, ctx):
        if not self._trivia:
            await ctx.send("No trivia available.")
            return
        raw = random.choice(self._trivia)
        if " || " in raw:
            question, answer = raw.split(" || ", 1)
        else:
            question, answer = raw, None
        view = _TriviaRevealView(ctx.author, answer)
        embed = discord.Embed(
            title="🧠 Trivia",
            description=question.strip(),
            color=GENERAL_COLOR,
        )
        embed.set_footer(text="Click 'Reveal Answer' when ready.")
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    @commands.command(name="motivate", help="Sends a motivational message.")
    async def motivate(self, ctx):
        embed = discord.Embed(
            title="💪 Motivation",
            description=random.choice(MOTIVATIONS),
            color=SUCCESS_COLOR,
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="eightball",
        aliases=["8ball"],
        help="Ask the Magic 8-Ball a yes/no question.",
    )
    async def eightball(self, ctx, *, question: str):
        embed = discord.Embed(title="🎱 Magic 8-Ball", color=GENERAL_COLOR)
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=random.choice(EIGHTBALL), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="greet", help="Greets you with a random greeting.")
    async def greet(self, ctx):
        embed = discord.Embed(
            title="👋 Greeting",
            description=f"{random.choice(GREETINGS)} {ctx.author.mention}",
            color=GENERAL_COLOR,
        )
        await ctx.send(embed=embed)


# ---------------------------------------------------------------------------
# Trivia Reveal View
# ---------------------------------------------------------------------------


class _TriviaRevealView(BaseView):
    def __init__(self, author: discord.Member, answer: str | None):
        super().__init__(author, public=True, timeout=120)
        self._answer = answer

    @discord.ui.button(label="Reveal Answer", style=discord.ButtonStyle.primary)
    async def reveal_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        text = self._answer.strip() if self._answer else "No answer recorded."
        await interaction.response.send_message(f"**Answer:** {text}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(General(bot))
