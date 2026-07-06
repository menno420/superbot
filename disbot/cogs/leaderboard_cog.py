"""Centralised leaderboards for XP, coins, mining, deathmatch, RPS, farm, and counting.

PR G refactored the per-category branches that previously lived in a
single ``_build_embed`` function into a provider registry under
:mod:`services.rank_providers`. This cog now contains only the
embed-rendering shell + the Discord-facing command surface; adding a
new category means registering a provider, not touching this file.
"""

from __future__ import annotations

import io

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer
from services.rank_providers import (
    ALIASES,
    RankEntry,
    RankProvider,
    get_provider,
    provider_names,
)
from utils.ui_constants import ECONOMY_COLOR, UTILITY_COLOR
from utils.ux_patterns.image_builders import render_leaderboard_image
from views.base import BaseView

MEDALS = ["🥇", "🥈", "🥉"]

# The image card the board attaches when a provider exposes structured rows.
_CARD_FILENAME = "leaderboard.jpg"


def _embed_from_entries(
    provider: RankProvider,
    entries: list[RankEntry],
) -> discord.Embed:
    """Build the leaderboard embed from already-fetched provider rows."""
    embed = discord.Embed(title=provider.display_title, color=ECONOMY_COLOR)
    if not entries:
        embed.description = provider.empty_hint
        return embed
    lines = []
    for i, entry in enumerate(entries):
        icon = MEDALS[i] if i < 3 else f"`#{i + 1}`"
        lines.append(f"{icon} {entry.label}")
    embed.description = "\n".join(lines)
    return embed


def _render_card(
    provider: RankProvider,
    entries: list[RankEntry],
) -> discord.File | None:
    """Render the top-N rows as an image card, or ``None`` for embed-only.

    ``None`` (caller keeps the plain embed) when: Pillow is unavailable, the
    board is empty, or any displayed entry lacks the structured
    ``(name, score)`` projection the bars need — so a provider that hasn't
    opted into the card degrades cleanly rather than rendering a broken board.
    """
    rows = [
        (entry.name, entry.score)
        for entry in entries
        if entry.name is not None and entry.score is not None
    ]
    if not rows or len(rows) != len(entries):
        return None
    value_texts = tuple((entry.value_text or "") for entry in entries)
    jpeg = render_leaderboard_image(
        tuple(rows),
        title=provider.display_title,
        value_texts=value_texts,
        theme=provider.card_theme,
    )
    if jpeg is None:  # Pillow unavailable → embed-only fallback.
        return None
    return discord.File(io.BytesIO(jpeg), filename=_CARD_FILENAME)


async def _build_provider_embed(
    provider: RankProvider,
    guild: discord.Guild,
) -> discord.Embed:
    """Render a leaderboard embed from a provider's top-N rows."""
    return _embed_from_entries(provider, await provider.top(guild))


async def _build_provider_response(
    provider: RankProvider,
    guild: discord.Guild,
) -> tuple[discord.Embed, discord.File | None]:
    """Fetch once and return the embed plus an optional image card.

    The card is the showpiece (Q-0023 visual card engine, H2); the embed
    stays the source of truth and the fallback, so a card-less category or a
    Pillow-less host renders exactly as before.
    """
    entries = await provider.top(guild)
    embed = _embed_from_entries(provider, entries)
    card = _render_card(provider, entries)
    if card is not None:
        embed.set_image(url=f"attachment://{_CARD_FILENAME}")
    return embed, card


def _build_overview_embed() -> discord.Embed:
    return discord.Embed(
        title="📊 Leaderboards",
        description="Select a category below to view the leaderboard.",
        color=UTILITY_COLOR,
    )


def _select_options() -> list[discord.SelectOption]:
    """Build the category-selector options from the provider registry.

    Order matches :func:`services.rank_providers.provider_names` so a
    new provider added there shows up here without further edits.
    """
    options: list[discord.SelectOption] = []
    for name in provider_names():
        provider = get_provider(name)
        if provider is None:
            continue
        options.append(
            discord.SelectOption(
                label=provider.select_label,
                value=provider.name,
                emoji=provider.select_emoji,
            ),
        )
    return options


class LeaderboardView(BaseView):
    """Category-selector view for the leaderboard panel."""

    def __init__(
        self,
        guild: discord.Guild,
        channel: discord.abc.GuildChannel,
        author: discord.Member | discord.User,
    ):
        super().__init__(author, timeout=120)
        self.guild = guild
        self.channel = channel
        self.add_item(_CategorySelect())


class _CategorySelect(discord.ui.Select):
    """Runtime-built select whose options come from the provider registry."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose a leaderboard category…",
            options=_select_options(),
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view = self.view
        if not isinstance(view, LeaderboardView):
            await interaction.followup.send(
                "This dropdown is no longer attached to the leaderboard.",
                ephemeral=True,
            )
            return
        provider = get_provider(self.values[0])
        if provider is None:
            await interaction.followup.send(
                f"Unknown category `{self.values[0]}`.",
                ephemeral=True,
            )
            return
        embed, card = await _build_provider_response(provider, view.guild)
        # Pass attachments explicitly so switching categories replaces (or
        # clears, with []) any card from the previously-selected category.
        await interaction.edit_original_response(
            embed=embed,
            view=view,
            attachments=[card] if card is not None else [],
        )


class LeaderboardCog(commands.Cog, name="Leaderboard"):  # type: ignore[call-arg]
    """Centralised leaderboards for XP, coins, mining, deathmatch, RPS, farm, and counting."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.cooldown(rate=2, per=10, type=commands.BucketType.user)
    @commands.command(
        name="leaderboard",
        aliases=[
            "lb",
            "rankings",
            "minelb",
            "miningleaderboard",
            "fishlb",
            "dm_leaderboard",
            "dm_lb",
            "rpslb",
            "farmlb",
            "countlb",
            "counting_leaderboard",
        ],
        # Q-A03 (held default, 2026-06-10): the per-game compatibility
        # aliases stay callable but are legacy routes — `!leaderboard
        # <category>` is the canonical spelling.  Display integration
        # rides the Help projection seam (consolidated plan Batch 6).
        extras={"alias_classification": "legacy_duplicate"},
    )
    async def leaderboard(self, ctx: commands.Context, category: str = ""):
        """Show a leaderboard.  !leaderboard [xp|coins|mining|fishing|farm|deathmatch|rps|counting]

        Aliases (``!minelb``, ``!dm_lb``, ``!rpslb``, ``!farmlb``, ``!countlb``, etc.)
        resolve to the same provider via the registry's alias map.
        """
        # Prefer the alias (``ctx.invoked_with``) only when it is itself
        # a known alias key. Otherwise fall back to the operator-typed
        # category argument so ``!leaderboard mining`` still works.
        invoked = (ctx.invoked_with or "").lower()
        if invoked in ALIASES:
            provider = get_provider(invoked)
        else:
            provider = get_provider(category) if category else None

        view = LeaderboardView(ctx.guild, ctx.channel, ctx.author)  # type: ignore[arg-type]
        card: discord.File | None = None
        if provider is not None:
            embed, card = await _build_provider_response(provider, ctx.guild)
        else:
            embed = _build_overview_embed()

        if card is not None:
            view.message = await ctx.send(embed=embed, view=view, file=card)
        else:
            view.message = await ctx.send(embed=embed, view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the leaderboard hub)."""
        view = LeaderboardView(
            interaction.guild,  # type: ignore[arg-type]
            interaction.channel,  # type: ignore[arg-type]
            interaction.user,  # type: ignore[arg-type]
        )
        return _build_overview_embed(), view


async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
