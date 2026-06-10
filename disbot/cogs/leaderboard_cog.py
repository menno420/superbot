"""Centralised leaderboards for XP, coins, mining, deathmatch, RPS, and counting.

PR G refactored the per-category branches that previously lived in a
single ``_build_embed`` function into a provider registry under
:mod:`services.rank_providers`. This cog now contains only the
embed-rendering shell + the Discord-facing command surface; adding a
new category means registering a provider, not touching this file.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer
from services.rank_providers import (
    ALIASES,
    RankProvider,
    get_provider,
    provider_names,
)
from utils.ui_constants import ECONOMY_COLOR, UTILITY_COLOR
from views.base import BaseView

MEDALS = ["🥇", "🥈", "🥉"]


async def _build_provider_embed(
    provider: RankProvider,
    guild: discord.Guild,
) -> discord.Embed:
    """Render a leaderboard embed from a provider's top-N rows."""
    embed = discord.Embed(title=provider.display_title, color=ECONOMY_COLOR)
    entries = await provider.top(guild)
    if not entries:
        embed.description = provider.empty_hint
        return embed
    lines = []
    for i, entry in enumerate(entries):
        icon = MEDALS[i] if i < 3 else f"`#{i+1}`"
        lines.append(f"{icon} {entry.label}")
    embed.description = "\n".join(lines)
    return embed


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
        embed = await _build_provider_embed(provider, view.guild)
        await interaction.edit_original_response(embed=embed, view=view)


class LeaderboardCog(commands.Cog, name="Leaderboard"):  # type: ignore[call-arg]
    """Centralised leaderboards for XP, coins, mining, deathmatch, RPS, and counting."""

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
            "dm_leaderboard",
            "dm_lb",
            "rpslb",
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
        """Show a leaderboard.  !leaderboard [xp|coins|mining|deathmatch|rps|counting]

        Aliases (``!minelb``, ``!dm_lb``, ``!rpslb``, ``!countlb``, etc.)
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
        if provider is not None:
            embed = await _build_provider_embed(provider, ctx.guild)
        else:
            embed = _build_overview_embed()

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
