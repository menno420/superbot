from __future__ import annotations
import time
import random
import discord
from discord.ext import commands
import logging
from utils import db
from utils.helpers import CogMenuView, post_log_embed
from utils.cooldowns import check_cooldown, format_remaining

logger = logging.getLogger("bot")

_XP_MENU_COMMANDS: list[tuple[str, str, str]] = [
    ("xpmenu",       "!xpmenu",                    "Show this XP command menu."),
    ("rank",         "!rank [@user] [xp|coins]",   "Show XP/coin rank card for a user."),
    ("leaderboard",  "!leaderboard [xp|coins]",    "Show the top-10 XP or coin leaderboard."),
    ("xpconfig",     "!xpconfig",                  "Configure XP gain range, cooldown, and announce channel (admin)."),
    ("givexp",       "!givexp <@user> <amount>",   "Give XP to a user (admin only)."),
    ("resetxp",      "!resetxp <@user>",           "Reset a user's XP to zero (admin only)."),
]


_XP_MIN = 15
_XP_MAX = 25
_COOLDOWN = 60  # seconds

# Stat types recognised by !rank and !leaderboard.  Add future stats here.
_STAT_TYPES: set[str] = {"xp", "coins", "both"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _guild_xp_settings(guild_id: int) -> tuple[int, int, int]:
    """Return (xp_min, xp_max, cooldown_seconds) for this guild."""
    mn = int(await db.get_setting(guild_id, "xp_min", str(_XP_MIN)))
    mx = int(await db.get_setting(guild_id, "xp_max", str(_XP_MAX)))
    cd = int(await db.get_setting(guild_id, "xp_cooldown", str(_COOLDOWN)))
    return mn, mx, cd


def _progress_bar(current: int, needed: int, width: int = 10) -> str:
    filled = int((current / needed) * width) if needed else width
    return "█" * filled + "░" * (width - filled)


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------

class XpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="xpmenu")
    async def xp_menu(self, ctx: commands.Context):
        """Show a quick-reference menu for all XP commands."""
        view = CogMenuView(ctx, "🏆 XP Commands", _XP_MENU_COMMANDS)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg

    # ------------------------------------------------------------------ events

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        guild_id = message.guild.id
        now = int(time.time())

        row = await db.get_xp(user_id, guild_id)
        xp_min, xp_max, cooldown = await _guild_xp_settings(guild_id)

        on_cd, _ = check_cooldown(row["last_xp"], cooldown)
        if on_cd:
            return

        amount = random.randint(xp_min, xp_max)
        new_xp, new_level, leveled_up = await db.add_xp(user_id, guild_id, amount, now)

        if leveled_up:
            channel_id = await db.get_setting(guild_id, "xp_announce_channel", "")
            announce_ch: discord.TextChannel | None = None
            if channel_id:
                announce_ch = message.guild.get_channel(int(channel_id))
            announce_ch = announce_ch or message.channel

            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{message.author.mention} reached **Level {new_level}**!",
                color=discord.Color.gold(),
            )
            try:
                await announce_ch.send(embed=embed)
            except discord.Forbidden:
                pass

            log_embed = discord.Embed(
                title="🏆 Level Up",
                description=(
                    f"{message.author.mention} reached **Level {new_level}**! "
                    f"(Total XP: {new_xp})"
                ),
                color=discord.Color.gold(),
            )
            await post_log_embed(self.bot, guild_id, log_embed)

    # ------------------------------------------------------------------ commands

    @commands.command(name="rank")
    async def rank(self, ctx: commands.Context, *args):
        """Show XP/coin rank.  !rank [user] [xp|coins]"""
        # Parse optional member and optional stat type from positional args
        member: discord.Member = ctx.author
        stat: str = "both"
        for arg in args:
            if arg.lower() in _STAT_TYPES:
                stat = arg.lower()
            else:
                try:
                    member = await commands.MemberConverter().convert(ctx, arg)
                except commands.BadArgument:
                    pass

        row = await db.get_xp(member.id, ctx.guild.id)
        level, current, needed = db.level_progress(row["xp"])

        all_xp = await db.fetchall(
            "SELECT user_id FROM xp WHERE guild_id=? ORDER BY xp DESC", (ctx.guild.id,)
        )
        all_coins = await db.fetchall(
            "SELECT user_id FROM xp WHERE guild_id=? ORDER BY coins DESC", (ctx.guild.id,)
        )
        xp_rank = next((i + 1 for i, r in enumerate(all_xp)    if r["user_id"] == member.id), "?")
        co_rank = next((i + 1 for i, r in enumerate(all_coins)  if r["user_id"] == member.id), "?")

        embed = discord.Embed(title=f"📊 {member.display_name}", color=discord.Color.blue())
        embed.set_thumbnail(url=member.display_avatar.url)

        if stat in ("both", "xp"):
            bar = _progress_bar(current, needed)
            embed.add_field(name="XP Rank",  value=f"#{xp_rank}",    inline=True)
            embed.add_field(name="Level",    value=str(level),        inline=True)
            embed.add_field(name="Total XP", value=str(row["xp"]),   inline=True)
            embed.add_field(
                name="Progress",
                value=f"`{bar}` {current}/{needed} XP",
                inline=False,
            )
            embed.add_field(name="Messages", value=str(row["messages"]), inline=True)

        if stat in ("both", "coins"):
            embed.add_field(name="Coin Rank", value=f"#{co_rank}",         inline=True)
            embed.add_field(name="🪙 Coins",  value=str(row.get("coins", 0)), inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="leaderboard", aliases=["lb"])
    async def leaderboard(self, ctx: commands.Context, stat: str = "xp"):
        """Show the top 10.  !leaderboard [xp|coins]"""
        stat = stat.lower()
        if stat not in ("xp", "coins"):
            await ctx.send(
                f"Unknown stat `{stat}`. Choose from: `xp`, `coins`.",
                delete_after=8,
            )
            return

        medals = ["🥇", "🥈", "🥉"]
        lines = []
        if stat == "xp":
            rows = await db.fetchall(
                "SELECT user_id, xp, level FROM xp WHERE guild_id=? ORDER BY xp DESC LIMIT 10",
                (ctx.guild.id,),
            )
            title = "🏆 XP Leaderboard"
            for i, row in enumerate(rows):
                m = ctx.guild.get_member(row["user_id"])
                name = m.display_name if m else f"<@{row['user_id']}>"
                icon = medals[i] if i < 3 else f"`#{i+1}`"
                lines.append(f"{icon} **{name}** — Level {row['level']} ({row['xp']} XP)")
        else:  # coins
            rows = await db.fetchall(
                "SELECT user_id, coins FROM xp WHERE guild_id=? ORDER BY coins DESC LIMIT 10",
                (ctx.guild.id,),
            )
            title = "🪙 Coin Leaderboard"
            for i, row in enumerate(rows):
                m = ctx.guild.get_member(row["user_id"])
                name = m.display_name if m else f"<@{row['user_id']}>"
                icon = medals[i] if i < 3 else f"`#{i+1}`"
                lines.append(f"{icon} **{name}** — {row['coins']} 🪙")

        embed = discord.Embed(title=title, color=discord.Color.gold())
        embed.description = "\n".join(lines) if lines else "No data yet!"
        await ctx.send(embed=embed)

    @commands.command(name="givexp")
    @commands.has_permissions(administrator=True)
    async def givexp(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Give XP to a user (admin only)."""
        if amount <= 0:
            await ctx.send("Amount must be positive.", delete_after=5)
            return
        new_xp, new_level, _ = await db.add_xp(member.id, ctx.guild.id, amount, 0)
        await ctx.send(
            f"✅ Gave **{amount}** XP to {member.mention}. "
            f"They now have **{new_xp}** XP (Level **{new_level}**)."
        )

    @commands.command(name="resetxp")
    @commands.has_permissions(administrator=True)
    async def resetxp(self, ctx: commands.Context, member: discord.Member):
        """Reset a user's XP to zero (admin only)."""
        await db.execute(
            "DELETE FROM xp WHERE user_id=? AND guild_id=?", (member.id, ctx.guild.id)
        )
        await ctx.send(f"✅ Reset XP for {member.mention}.")

    @commands.command(name="xpconfig")
    @commands.has_permissions(administrator=True)
    async def xpconfig(self, ctx: commands.Context):
        """Open the XP configuration panel (admin only)."""
        view = XpConfigView(ctx)
        msg = await ctx.send(embed=await view.build_embed(), view=view)
        view.message = msg


# ---------------------------------------------------------------------------
# XP Config UI
# ---------------------------------------------------------------------------

class XpConfigView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.message: discord.Message | None = None

    async def build_embed(self) -> discord.Embed:
        gid = self.ctx.guild.id
        xp_min, xp_max, cooldown = await _guild_xp_settings(gid)
        cid = await db.get_setting(gid, "xp_announce_channel", "")
        channel_str = f"<#{cid}>" if cid else "Same channel as message"

        embed = discord.Embed(title="⚙️ XP Configuration", color=discord.Color.blurple())
        embed.add_field(name="XP per message", value=f"{xp_min}–{xp_max}",  inline=True)
        embed.add_field(name="Cooldown",        value=f"{cooldown}s",        inline=True)
        embed.add_field(name="Level-up channel", value=channel_str,          inline=True)
        embed.set_footer(text="Click a button below to change a setting.")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This panel isn't for you.", ephemeral=True)
            return False
        return True

    _run_checks = interaction_check

    async def _refresh(self, interaction: discord.Interaction):
        await interaction.message.edit(embed=await self.build_embed(), view=self)

    @discord.ui.button(label="XP Range", style=discord.ButtonStyle.blurple, row=0)
    async def btn_xp_range(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_XpRangeModal(self))

    @discord.ui.button(label="Cooldown", style=discord.ButtonStyle.blurple, row=0)
    async def btn_cooldown(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_XpCooldownModal(self))

    @discord.ui.button(label="Level-up Channel", style=discord.ButtonStyle.blurple, row=0)
    async def btn_channel(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_XpChannelModal(self))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass


class _XpRangeModal(discord.ui.Modal, title="Set XP Range"):
    xp_min = discord.ui.TextInput(label="Min XP per message", placeholder="15", max_length=4)
    xp_max = discord.ui.TextInput(label="Max XP per message", placeholder="25", max_length=4)

    def __init__(self, view: XpConfigView):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            mn, mx = int(self.xp_min.value), int(self.xp_max.value)
            if mn <= 0 or mx < mn:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "Invalid values — min and max must be positive integers with min ≤ max.",
                ephemeral=True,
            )
            return
        gid = self.view.ctx.guild.id
        await db.set_setting(gid, "xp_min", str(mn))
        await db.set_setting(gid, "xp_max", str(mx))
        await interaction.response.defer()
        await self.view._refresh(interaction)


class _XpCooldownModal(discord.ui.Modal, title="Set XP Cooldown"):
    seconds = discord.ui.TextInput(label="Cooldown in seconds", placeholder="60", max_length=5)

    def __init__(self, view: XpConfigView):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.seconds.value)
            if val < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "Must be a non-negative integer.", ephemeral=True
            )
            return
        await db.set_setting(self.view.ctx.guild.id, "xp_cooldown", str(val))
        await interaction.response.defer()
        await self.view._refresh(interaction)


class _XpChannelModal(discord.ui.Modal, title="Level-up Announcement Channel"):
    channel_id = discord.ui.TextInput(
        label="Channel ID (leave blank = same channel)",
        required=False,
        max_length=25,
    )

    def __init__(self, view: XpConfigView):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        val = self.channel_id.value.strip()
        if val and not val.isdigit():
            await interaction.response.send_message(
                "Enter a valid numeric channel ID, or leave blank.", ephemeral=True
            )
            return
        await db.set_setting(self.view.ctx.guild.id, "xp_announce_channel", val)
        await interaction.response.defer()
        await self.view._refresh(interaction)


async def setup(bot: commands.Bot):
    await bot.add_cog(XpCog(bot))
    logger.info("XpCog loaded.")
