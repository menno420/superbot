from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer
from utils import db
from utils.ui_constants import ECONOMY_COLOR, UTILITY_COLOR
from views.base import BaseView

MEDALS = ["🥇", "🥈", "🥉"]

CATEGORIES = {
    "xp": ("🏆 XP Leaderboard", "xp"),
    "coins": ("🪙 Coin Leaderboard", "coins"),
    "mining": ("⛏️ Mining Leaderboard", "mining"),
    "deathmatch": ("⚔️ Deathmatch Leaderboard", "deathmatch"),
    "rps": ("✂️ RPS Leaderboard", "rps"),
    "counting": ("🔢 Counting Leaderboard", "counting"),
}

ALIASES_MAP = {
    "minelb": "mining",
    "miningleaderboard": "mining",
    "dm_leaderboard": "deathmatch",
    "dm_lb": "deathmatch",
    "board": "deathmatch",
    "rpslb": "rps",
    "countlb": "counting",
    "counting_leaderboard": "counting",
    "lb": "xp",
    "rankings": "xp",
}


async def _build_embed(
    category: str,
    guild: discord.Guild,
    ctx_channel: discord.abc.GuildChannel,
) -> discord.Embed:
    title, _ = CATEGORIES.get(category, ("Leaderboard", ""))
    embed = discord.Embed(title=title, color=ECONOMY_COLOR)

    if category == "xp":
        rows = await db.fetchall(
            "SELECT user_id, xp, level FROM xp WHERE guild_id=$1 ORDER BY xp DESC LIMIT 10",
            (guild.id,),
        )
        lines = []
        for i, row in enumerate(rows):
            m = guild.get_member(row["user_id"])
            name = m.display_name if m else f"<@{row['user_id']}>"
            icon = MEDALS[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{icon} **{name}** — Level {row['level']} ({row['xp']} XP)")
        embed.description = "\n".join(lines) or "No data yet!"

    elif category == "coins":
        rows = await db.fetchall(
            "SELECT user_id, coins FROM xp WHERE guild_id=$1 ORDER BY coins DESC LIMIT 10",
            (guild.id,),
        )
        lines = []
        for i, row in enumerate(rows):
            m = guild.get_member(row["user_id"])
            name = m.display_name if m else f"<@{row['user_id']}>"
            icon = MEDALS[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{icon} **{name}** — {row['coins']} 🪙")
        embed.description = "\n".join(lines) or "No data yet!"

    elif category == "mining":
        rows = await db.get_all_mining_totals(guild.id)
        lines = []
        for i, (user_id, total) in enumerate(rows):
            m = guild.get_member(int(user_id)) if user_id.isdigit() else None
            name = m.display_name if m else f"<@{user_id}>"
            icon = MEDALS[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{icon} **{name}** — {total} items")
        embed.description = "\n".join(lines) or "No data yet!"

    elif category == "deathmatch":
        rows = await db.get_deathmatch_leaderboard()
        lines = []
        for i, row in enumerate(rows):
            m = guild.get_member(row["user_id"])
            name = m.display_name if m else f"<@{row['user_id']}>"
            icon = MEDALS[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{icon} **{name}** — {row['wins']}W / {row['losses']}L")
        embed.description = "\n".join(lines) or "No data yet!"

    elif category == "rps":
        rows = await db.rps_get_leaderboard(guild.id)
        lines = []
        for i, row in enumerate(rows):
            icon = MEDALS[i] if i < 3 else f"`#{i+1}`"
            lines.append(
                f"{icon} **{row['name']}** — {row['wins']}W / {row['losses']}L / {row['ties']}T",
            )
        embed.description = "\n".join(lines) or "No data yet!"

    elif category == "counting":
        # Aggregate counting totals across all channels for this guild
        state = await db.get_counting_state(guild.id)
        totals: dict[str, int] = {}
        for ch_data in state.get("channels", {}).values():
            for uid, cnt in ch_data.get("leaderboard", {}).items():
                totals[uid] = totals.get(uid, 0) + cnt
        sorted_totals = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:10]
        lines = []
        for i, (uid, cnt) in enumerate(sorted_totals):
            m = guild.get_member(int(uid)) if uid.isdigit() else None
            name = m.display_name if m else f"<@{uid}>"
            icon = MEDALS[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{icon} **{name}** — {cnt} counts")
        embed.description = "\n".join(lines) or "No counting data yet!"

    return embed


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

    @discord.ui.select(
        placeholder="Choose a leaderboard category…",
        options=[
            discord.SelectOption(label="XP", value="xp", emoji="🏆"),
            discord.SelectOption(label="Coins", value="coins", emoji="🪙"),
            discord.SelectOption(label="Mining", value="mining", emoji="⛏️"),
            discord.SelectOption(label="Deathmatch", value="deathmatch", emoji="⚔️"),
            discord.SelectOption(label="RPS", value="rps", emoji="✂️"),
            discord.SelectOption(label="Counting", value="counting", emoji="🔢"),
        ],
    )
    async def select_category(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select,
    ):
        if not await safe_defer(interaction):
            return
        embed = await _build_embed(select.values[0], self.guild, self.channel)
        await interaction.edit_original_response(embed=embed, view=self)


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
    )
    async def leaderboard(self, ctx: commands.Context, category: str = ""):
        """Show a leaderboard.  !leaderboard [xp|coins|mining|deathmatch|rps|counting]"""
        cat = ALIASES_MAP.get(ctx.invoked_with, category.lower()) or ""
        cat = ALIASES_MAP.get(cat, cat)

        view = LeaderboardView(ctx.guild, ctx.channel, ctx.author)  # type: ignore[arg-type]

        if cat and cat in CATEGORIES:
            embed = await _build_embed(cat, ctx.guild, ctx.channel)  # type: ignore[arg-type]
        else:
            embed = discord.Embed(
                title="📊 Leaderboards",
                description="Select a category below to view the leaderboard.",
                color=UTILITY_COLOR,
            )

        view.message = await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
