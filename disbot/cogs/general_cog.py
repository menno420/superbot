from __future__ import annotations

import json
import logging
import os
import random

import discord
from discord.ext import commands

from utils.ui_constants import GENERAL_COLOR, SUCCESS_COLOR
from views.base import BaseView, send_panel

logger = logging.getLogger("bot")

_CONTENT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "json",
    "general_content.json",
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


def _overview_embed() -> discord.Embed:
    """Build the General subsystem panel overview embed."""
    return discord.Embed(
        title="💬 General",
        description=(
            "**💡 Fact** — random interesting fact\n"
            "**😄 Joke** — random joke\n"
            "**💬 Quote** — famous quote\n"
            "**🧠 Trivia** — trivia question with reveal\n"
            "**💪 Motivate** — motivational message\n"
            "**🎱 8-Ball** — yes/no question modal\n"
            "**👋 Greet** — random greeting"
        ),
        color=GENERAL_COLOR,
    )


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        content = _load_content()
        self._facts: list[str] = content.get("facts", [])
        self._jokes: list[str] = content.get("jokes", [])
        self._quotes: list[str] = content.get("quotes", [])
        self._trivia: list[str] = content.get("trivia", [])

    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    @commands.command(
        name="generalmenu",
        aliases=["gmenu"],
        help="Open the interactive General panel.",
    )
    async def general_menu(self, ctx: commands.Context) -> None:
        """Entry-point command for the General subsystem panel.

        The subsystem_registry's entry_points list must contain at least one
        actually-registered command — this command is that anchor (the help
        menu uses it to map "general" → this cog).
        """
        view = _GeneralPanelView(ctx.author, self)
        await send_panel(ctx, embed=_overview_embed(), view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook.

        Called by HelpPanelView._on_select when the user picks "General" from
        the help dropdown.  Returns the same (embed, view) pair that
        !generalmenu would produce, so the help message can be replaced in
        place with the General panel — no secondary navigation step required.
        Governance has already been resolved at the help layer.
        """
        view = _GeneralPanelView(interaction.user, self)  # type: ignore[arg-type]
        return _overview_embed(), view

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
        name="trivia",
        help="Asks a trivia question with a reveal button.",
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
        await send_panel(ctx, embed=embed, view=view)

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
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        text = self._answer.strip() if self._answer else "No answer recorded."
        await interaction.response.send_message(f"**Answer:** {text}", ephemeral=True)


# ---------------------------------------------------------------------------
# General Panel View
# ---------------------------------------------------------------------------


class _EightBallModal(discord.ui.Modal, title="🎱 Magic 8-Ball"):  # type: ignore[call-arg]
    question = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Ask a yes/no question",
        placeholder="Will I win the lottery?",
        max_length=200,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title="🎱 Magic 8-Ball", color=GENERAL_COLOR)
        embed.add_field(name="Question", value=str(self.question), inline=False)
        embed.add_field(name="Answer", value=random.choice(EIGHTBALL), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=False)


class _GeneralPanelView(BaseView):
    """Interactive panel for the General subsystem.

    Mirrors the pattern of _UtilityPanelView in utility_cog.py: each button
    edits the same message in place with a result embed.  Public=True so the
    panel can be shared in a channel context.
    """

    def __init__(self, author: discord.Member | discord.User, cog: General):
        super().__init__(author, public=True, timeout=300)
        self._cog = cog

    def _build_overview(self) -> discord.Embed:
        return _overview_embed()

    def _random_or_empty(self, pool: list[str], label: str) -> str:
        return random.choice(pool) if pool else f"No {label} available."

    @discord.ui.button(label="💡 Fact", style=discord.ButtonStyle.blurple, row=0)
    async def fact_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = discord.Embed(
            title="💡 Random Fact",
            description=self._random_or_empty(self._cog._facts, "facts"),
            color=GENERAL_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="😄 Joke", style=discord.ButtonStyle.blurple, row=0)
    async def joke_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = discord.Embed(
            title="😄 Random Joke",
            description=self._random_or_empty(self._cog._jokes, "jokes"),
            color=GENERAL_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="💬 Quote", style=discord.ButtonStyle.blurple, row=0)
    async def quote_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = discord.Embed(
            title="💬 Quote",
            description=self._random_or_empty(self._cog._quotes, "quotes"),
            color=GENERAL_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🧠 Trivia", style=discord.ButtonStyle.grey, row=1)
    async def trivia_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not self._cog._trivia:
            await interaction.response.send_message(
                "No trivia available.",
                ephemeral=True,
            )
            return
        raw = random.choice(self._cog._trivia)
        question, answer = (
            (raw.split(" || ", 1) + [None])[:2] if " || " in raw else (raw, None)
        )
        embed = discord.Embed(
            title="🧠 Trivia",
            description=question.strip(),
            color=GENERAL_COLOR,
        )
        embed.set_footer(text="Click 'Reveal Answer' below.")
        reveal_view = _TriviaRevealView(self._author, answer)  # type: ignore[arg-type]
        await interaction.response.send_message(embed=embed, view=reveal_view)

    @discord.ui.button(label="💪 Motivate", style=discord.ButtonStyle.grey, row=1)
    async def motivate_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = discord.Embed(
            title="💪 Motivation",
            description=random.choice(MOTIVATIONS),
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🎱 8-Ball", style=discord.ButtonStyle.grey, row=1)
    async def eightball_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(_EightBallModal())

    @discord.ui.button(label="👋 Greet", style=discord.ButtonStyle.green, row=2)
    async def greet_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = discord.Embed(
            title="👋 Greeting",
            description=f"{random.choice(GREETINGS)} {interaction.user.mention}",
            color=GENERAL_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="↩ Overview", style=discord.ButtonStyle.secondary, row=2)
    async def overview_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(embed=self._build_overview(), view=self)


async def setup(bot):
    await bot.add_cog(General(bot))
