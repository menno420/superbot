"""Community Spotlight — live server activity dashboard.

Surfaces real server data: XP leaders, richest members, game champions,
and a live level-up feed powered by the EventBus. All data comes from
the same providers and DB helpers used by !leaderboard and !rank.
"""

from __future__ import annotations

import datetime
import logging
from collections import deque
from typing import Any

import discord
from discord.ext import commands, tasks

from core.events import bus
from core.runtime import resources
from core.runtime.interaction_helpers import safe_defer
from services import xp_service
from services.rank_providers import get_provider
from utils import db
from utils.ui_constants import ECONOMY_COLOR, GAME_COLOR, GENERAL_COLOR, UTILITY_COLOR
from views.base import BaseView

logger = logging.getLogger(__name__)

MEDALS = ["🥇", "🥈", "🥉"]
_MAX_LEVELUP_ENTRIES = 5

# guild_id → deque of recent level-up strings, populated via EventBus
_levelup_feed: dict[int, deque[str]] = {}


# ---------------------------------------------------------------------------
# Embed builders
# ---------------------------------------------------------------------------


async def _build_main_embed(guild: discord.Guild) -> discord.Embed:
    """Build the live spotlight embed for *guild*."""
    embed = discord.Embed(
        title=f"🌟 Community Spotlight — {guild.name}",
        color=GENERAL_COLOR,
    )

    # ── Server overview ─────────────────────────────────────────────────────
    total_xp, total_coins = await db.get_guild_xp_totals(guild.id)
    # member_count is Optional — None until the guild is chunked/cached.
    member_count = guild.member_count or 0
    embed.add_field(
        name="📊 Server at a Glance",
        value=(
            f"👥 **{member_count:,}** members\n"
            f"⭐ **{total_xp:,}** XP earned\n"
            f"🪙 **{total_coins:,}** coins in circulation"
        ),
        inline=True,
    )

    # ── Top 3 XP leaders ────────────────────────────────────────────────────
    xp_provider = get_provider("xp")
    xp_lines: list[str] = []
    if xp_provider is not None:
        top_xp = await xp_provider.top(guild)
        for i, entry in enumerate(top_xp[:3]):
            medal = MEDALS[i] if i < 3 else f"`#{i + 1}`"
            xp_lines.append(f"{medal} {entry.label}")
    embed.add_field(
        name="🏆 XP Leaders",
        value="\n".join(xp_lines) if xp_lines else "*No activity yet*",
        inline=True,
    )

    # ── Top coin holder ─────────────────────────────────────────────────────
    coins_provider = get_provider("coins")
    coins_lines: list[str] = []
    if coins_provider is not None:
        top_coins = await coins_provider.top(guild)
        for i, entry in enumerate(top_coins[:3]):
            medal = MEDALS[i] if i < 3 else f"`#{i + 1}`"
            coins_lines.append(f"{medal} {entry.label}")
    embed.add_field(
        name="💰 Richest Members",
        value="\n".join(coins_lines) if coins_lines else "*No coins earned yet*",
        inline=True,
    )

    # ── Recent level-ups (EventBus feed) ────────────────────────────────────
    feed = list(_levelup_feed.get(guild.id, []))
    if feed:
        feed_text = "\n".join(f"• {entry}" for entry in reversed(feed[-5:]))
    else:
        feed_text = "*Waiting for the next level-up…*"
    embed.add_field(name="🎉 Recent Level-Ups", value=feed_text, inline=False)

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M UTC")
    embed.set_footer(text=f"Updated {now} • Use the buttons to explore leaderboards")
    return embed


async def _build_provider_embed(name: str, guild: discord.Guild) -> discord.Embed:
    """Build a full top-10 leaderboard embed for the named provider."""
    provider = get_provider(name)
    if provider is None:
        return discord.Embed(
            description=f"Unknown category `{name}`.",
            color=UTILITY_COLOR,
        )
    embed = discord.Embed(title=provider.display_title, color=ECONOMY_COLOR)
    entries = await provider.top(guild)
    if not entries:
        embed.description = provider.empty_hint
        return embed
    lines = []
    for i, entry in enumerate(entries):
        icon = MEDALS[i] if i < 3 else f"`#{i + 1}`"
        lines.append(f"{icon} {entry.label}")
    embed.description = "\n".join(lines)
    return embed


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


class SpotlightView(BaseView):
    """Main Community Spotlight panel with leaderboard navigation."""

    def __init__(self, guild: discord.Guild, author: discord.Member | discord.User):
        super().__init__(author, public=True, timeout=300)
        self.guild = guild

    @discord.ui.button(
        label="XP Leaders",
        style=discord.ButtonStyle.blurple,
        emoji="🏆",
    )
    async def xp_leaders(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        embed = await _build_provider_embed("xp", self.guild)
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="Richest", style=discord.ButtonStyle.blurple, emoji="💰")
    async def richest(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        embed = await _build_provider_embed("coins", self.guild)
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="Games", style=discord.ButtonStyle.green, emoji="🎮")
    async def games(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        games_view = GamesView(self.guild, interaction.user)
        games_view.message = self.message
        embed = discord.Embed(
            title="🎮 Game Leaderboards",
            description="Select a game below to view its leaderboard.",
            color=GAME_COLOR,
        )
        await interaction.edit_original_response(embed=embed, view=games_view)

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.gray, emoji="🔄")
    async def refresh(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        embed = await _build_main_embed(self.guild)
        await interaction.edit_original_response(embed=embed, view=self)


class GamesView(BaseView):
    """Game leaderboard sub-panel with a category select."""

    def __init__(self, guild: discord.Guild, author: discord.Member | discord.User):
        super().__init__(author, public=True, timeout=120)
        self.guild = guild
        self.add_item(_GameSelect())

    @discord.ui.button(label="← Back", style=discord.ButtonStyle.gray)
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        main_view = SpotlightView(self.guild, interaction.user)
        main_view.message = self.message
        embed = await _build_main_embed(self.guild)
        await interaction.edit_original_response(embed=embed, view=main_view)


class _GameSelect(discord.ui.Select):
    _GAMES = [
        ("mining", "Mining", "⛏️"),
        ("rps", "Rock-Paper-Scissors", "✊"),
        ("deathmatch", "Deathmatch", "⚔️"),
        ("counting", "Counting", "🔢"),
    ]

    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose a game leaderboard…",
            options=[
                discord.SelectOption(label=label, value=name, emoji=emoji)
                for name, label, emoji in self._GAMES
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, GamesView):
            return
        if not await safe_defer(interaction):
            return
        embed = await _build_provider_embed(self.values[0], view.guild)
        await interaction.edit_original_response(embed=embed, view=view)


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class CommunitySpotlightCog(commands.Cog, name="Community Spotlight"):  # type: ignore[call-arg]
    """Live server activity hub — leaders, level-ups, and game stats."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        bus.on(xp_service.EVT_LEVEL_UP, self._on_level_up)
        self._cache_trim_loop.start()
        logger.info("CommunitySpotlightCog loaded — subscribed to xp.level_up")

    async def cog_unload(self) -> None:
        bus.off(xp_service.EVT_LEVEL_UP, self._on_level_up)
        self._cache_trim_loop.cancel()

    async def _on_level_up(self, **payload: Any) -> None:
        """EventBus handler — cache a human-readable level-up blurb per guild."""
        guild_id: int = payload.get("guild_id", 0)
        user_id: int = payload.get("user_id", 0)
        new_level: int = payload.get("new_level", 0)
        guild = self.bot.get_guild(guild_id)
        name = resources.member_display(guild, user_id) if guild else f"<@{user_id}>"
        entry = f"**{name}** reached Level **{new_level}**"
        feed = _levelup_feed.setdefault(guild_id, deque(maxlen=_MAX_LEVELUP_ENTRIES))
        feed.append(entry)

    @tasks.loop(hours=1)
    async def _cache_trim_loop(self) -> None:
        # Evict guilds the bot is no longer in so the dict doesn't grow unbounded.
        stale = [gid for gid in _levelup_feed if self.bot.get_guild(gid) is None]
        for gid in stale:
            del _levelup_feed[gid]

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help/hub direct-navigation hook (returns the Spotlight panel).

        Called by the Help dropdown and the Community hub's child routing;
        the caller appends its own back-navigation button.
        """
        if interaction.guild is None:
            return (
                discord.Embed(
                    description="The Community Spotlight is only available "
                    "inside a server.",
                ),
                discord.ui.View(),
            )
        embed = await _build_main_embed(interaction.guild)
        view = SpotlightView(interaction.guild, interaction.user)
        return embed, view

    @commands.cooldown(rate=2, per=15, type=commands.BucketType.user)
    @commands.command(
        name="spotlight",
        aliases=["activity"],
    )
    async def spotlight(self, ctx: commands.Context) -> None:
        """Show the Community Spotlight — live XP, coins, games, and level-ups."""
        if ctx.guild is None:
            await ctx.send("This command can only be used in a server.", ephemeral=True)
            return
        embed = await _build_main_embed(ctx.guild)
        view = SpotlightView(ctx.guild, ctx.author)
        view.message = await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommunitySpotlightCog(bot))
