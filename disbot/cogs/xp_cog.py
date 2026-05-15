from __future__ import annotations

import logging
import random
import time

import discord
from discord.ext import commands
from utils import db
from utils import embeds as em
from utils.cooldowns import check_cooldown, format_remaining
from utils.helpers import _parse_member, post_log_embed
from utils.ui_constants import ECONOMY_COLOR, UTILITY_COLOR
from views.base import BaseView

logger = logging.getLogger("bot")

_XP_MENU_COMMANDS: list[tuple[str, str, str]] = [
    ("xpmenu", "!xpmenu", "Show this XP command menu."),
    ("rank", "!rank [@user] [xp|coins]", "Show XP/coin rank card for a user."),
    (
        "leaderboard",
        "!leaderboard [xp|coins]",
        "Show the top-10 XP or coin leaderboard.",
    ),
    (
        "xpconfig",
        "!xpconfig",
        "Configure XP gain range, cooldown, and announce channel (admin).",
    ),
    ("givexp", "!givexp <@user> <amount>", "Give XP to a user (admin only)."),
    ("resetxp", "!resetxp <@user>", "Reset a user's XP to zero (admin only)."),
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


async def _build_rank_embed(
    member: discord.Member,
    guild: discord.Guild,
    stat: str,
) -> discord.Embed:
    """Build the rank card embed for a member."""
    row = await db.get_xp(member.id, guild.id)
    level, current, needed = db.level_progress(row["xp"])

    all_xp = await db.fetchall(
        "SELECT user_id FROM xp WHERE guild_id=$1 ORDER BY xp DESC", (guild.id,)
    )
    all_coins = await db.fetchall(
        "SELECT user_id FROM xp WHERE guild_id=$1 ORDER BY coins DESC",
        (guild.id,),
    )
    xp_rank = next(
        (i + 1 for i, r in enumerate(all_xp) if r["user_id"] == member.id), "?"
    )
    co_rank = next(
        (i + 1 for i, r in enumerate(all_coins) if r["user_id"] == member.id), "?"
    )

    embed = discord.Embed(title=f"📊 {member.display_name}", color=UTILITY_COLOR)
    embed.set_thumbnail(url=member.display_avatar.url)

    if stat in ("both", "xp"):
        bar = _progress_bar(current, needed)
        embed.add_field(name="XP Rank", value=f"#{xp_rank}", inline=True)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="Total XP", value=str(row["xp"]), inline=True)
        embed.add_field(
            name="Progress",
            value=f"`{bar}` {current}/{needed} XP",
            inline=False,
        )
        embed.add_field(name="Messages", value=str(row["messages"]), inline=True)

    if stat in ("both", "coins"):
        embed.add_field(name="Coin Rank", value=f"#{co_rank}", inline=True)
        embed.add_field(name="🪙 Coins", value=str(row.get("coins", 0)), inline=True)

    return embed


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class _XpHubView(BaseView):
    """Interactive XP hub — shows rank card with quick admin actions."""

    def __init__(self, ctx: commands.Context):
        super().__init__(ctx.author, timeout=180)
        self.ctx = ctx

    async def build_embed(self) -> discord.Embed:
        embed = await _build_rank_embed(self.ctx.author, self.ctx.guild, "both")
        embed.title = f"🏆 XP Panel — {self.ctx.author.display_name}"
        is_admin = self.ctx.author.guild_permissions.administrator
        lines = ["Use the buttons below to switch stat views."]
        if is_admin:
            lines.append("Admin controls: ⚙️ Configure · 🎁 Give XP · 🔄 Reset XP")
        embed.set_footer(text=" · ".join(lines))
        # Show or hide admin buttons based on permissions
        for item in self.children:
            if hasattr(item, "_admin_only"):
                item.disabled = not is_admin
        return embed

    @discord.ui.button(label="📊 Both", style=discord.ButtonStyle.blurple, row=0)
    async def btn_both(self, interaction: discord.Interaction, _: discord.ui.Button):
        embed = await _build_rank_embed(self.ctx.author, self.ctx.guild, "both")
        embed.title = f"🏆 XP Panel — {self.ctx.author.display_name}"
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🏆 XP", style=discord.ButtonStyle.blurple, row=0)
    async def btn_xp(self, interaction: discord.Interaction, _: discord.ui.Button):
        embed = await _build_rank_embed(self.ctx.author, self.ctx.guild, "xp")
        embed.title = f"🏆 XP Panel — {self.ctx.author.display_name}"
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🪙 Coins", style=discord.ButtonStyle.blurple, row=0)
    async def btn_coins(self, interaction: discord.Interaction, _: discord.ui.Button):
        embed = await _build_rank_embed(self.ctx.author, self.ctx.guild, "coins")
        embed.title = f"🏆 XP Panel — {self.ctx.author.display_name}"
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⚙️ Configure", style=discord.ButtonStyle.grey, row=1)
    async def btn_config(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Administrator permission required.", ephemeral=True
            )
            return
        config_view = XpConfigView(self.ctx)
        config_view.message = self.message
        await interaction.response.edit_message(
            embed=await config_view.build_embed(), view=config_view
        )

    @discord.ui.button(label="🎁 Give XP", style=discord.ButtonStyle.grey, row=1)
    async def btn_givexp(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Administrator permission required.", ephemeral=True
            )
            return
        await interaction.response.send_modal(_GiveXpModal(self))

    @discord.ui.button(label="🔄 Reset XP", style=discord.ButtonStyle.danger, row=1)
    async def btn_resetxp(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Administrator permission required.", ephemeral=True
            )
            return
        await interaction.response.send_modal(_ResetXpModal(self))


class _GiveXpModal(discord.ui.Modal, title="Give XP"):  # type: ignore[call-arg]
    member_input = discord.ui.TextInput(label="User (mention or ID)", max_length=100)
    amount_input = discord.ui.TextInput(
        label="XP amount", placeholder="e.g. 100", max_length=10
    )

    def __init__(self, hub: _XpHubView):
        super().__init__()
        self._hub = hub

    async def on_submit(self, interaction: discord.Interaction):
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.", ephemeral=True
            )
            return
        try:
            amount = int(self.amount_input.value)
            if amount <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Amount must be a positive integer.", ephemeral=True
            )
            return
        new_xp, new_level, _ = await db.add_xp(
            member.id, interaction.guild_id, amount, 0
        )
        await interaction.response.send_message(
            f"✅ Gave **{amount}** XP to {member.mention}. "
            f"Now **{new_xp}** XP (Level **{new_level}**).",
            ephemeral=True,
        )


class _ResetXpModal(discord.ui.Modal, title="Reset XP"):  # type: ignore[call-arg]
    member_input = discord.ui.TextInput(label="User (mention or ID)", max_length=100)
    confirm_input = discord.ui.TextInput(
        label='Type "CONFIRM" to reset', placeholder="CONFIRM", max_length=10
    )

    def __init__(self, hub: _XpHubView):
        super().__init__()
        self._hub = hub

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirm_input.value.strip().upper() != "CONFIRM":
            await interaction.response.send_message(
                "❌ Reset cancelled — type CONFIRM to proceed.", ephemeral=True
            )
            return
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.", ephemeral=True
            )
            return
        await db.execute(
            "DELETE FROM xp WHERE user_id=$1 AND guild_id=$2",
            (member.id, interaction.guild_id),
        )
        await interaction.response.send_message(
            f"✅ Reset XP for {member.mention}.", ephemeral=True
        )


class XpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="xpmenu")
    async def xp_menu(self, ctx: commands.Context):
        """Open the XP panel showing your rank and quick admin actions."""
        view = _XpHubView(ctx)
        embed = await view.build_embed()
        msg = await ctx.send(embed=embed, view=view)
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
                color=ECONOMY_COLOR,
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
                color=ECONOMY_COLOR,
            )
            await post_log_embed(self.bot, guild_id, log_embed)

            # XP threshold role assignment
            try:
                xp_roles = await db.get_xp_threshold_roles(guild_id)
                for role_cfg in xp_roles:
                    if role_cfg["level_required"] <= new_level:
                        discord_role = discord.utils.get(
                            message.guild.roles, name=role_cfg["role_name"]
                        )
                        if discord_role and discord_role not in message.author.roles:
                            try:
                                await message.author.add_roles(
                                    discord_role,
                                    reason=f"XP level-up: reached level {new_level}",
                                )
                                logger.info(
                                    "XP role assigned: %s → %s (level %d)",
                                    message.author.display_name,
                                    discord_role.name,
                                    new_level,
                                )
                            except (
                                discord.Forbidden,
                                discord.HTTPException,
                            ) as role_err:
                                logger.warning(
                                    "Could not assign XP role %s to %s: %s",
                                    discord_role.name,
                                    message.author.display_name,
                                    role_err,
                                )
            except Exception:
                logger.error(
                    "XP role assignment check failed for guild %d",
                    guild_id,
                    exc_info=True,
                )

    # ------------------------------------------------------------------ commands

    @commands.command(name="rank")
    async def rank(self, ctx: commands.Context, *args):
        """Show XP/coin rank.  !rank [user] [xp|coins|both]"""
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

        embed = await _build_rank_embed(member, ctx.guild, stat)
        view = _RankView(member, ctx.guild, stat)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="givexp")
    @commands.has_permissions(administrator=True)
    async def givexp(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Give XP to a user (admin only)."""
        if amount <= 0:
            await ctx.send(embed=em.error("Amount must be positive."), delete_after=5)
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
            "DELETE FROM xp WHERE user_id=$1 AND guild_id=$2", (member.id, ctx.guild.id)
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
# Rank navigation view
# ---------------------------------------------------------------------------


class _RankView(discord.ui.View):
    """Navigation dropdown for the rank card — lets users switch stat views."""

    def __init__(
        self,
        member: discord.Member,
        guild: discord.Guild,
        current_stat: str,
    ):
        super().__init__(timeout=120)
        self.member = member
        self.guild = guild
        self.message: discord.Message | None = None
        self.add_item(_RankSelect(self, current_stat))

    async def on_timeout(self) -> None:
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass


class _RankSelect(discord.ui.Select):
    def __init__(self, rank_view: _RankView, current_stat: str):
        options = [
            discord.SelectOption(
                label="Both (XP & Coins)",
                value="both",
                emoji="📊",
                default=(current_stat == "both"),
            ),
            discord.SelectOption(
                label="XP",
                value="xp",
                emoji="🏆",
                default=(current_stat == "xp"),
            ),
            discord.SelectOption(
                label="Coins",
                value="coins",
                emoji="🪙",
                default=(current_stat == "coins"),
            ),
        ]
        super().__init__(
            placeholder="Switch stat view…",
            options=options,
            min_values=1,
            max_values=1,
        )
        self._rank_view = rank_view

    async def callback(self, interaction: discord.Interaction) -> None:
        stat = self.values[0]
        for opt in self.options:
            opt.default = opt.value == stat
        embed = await _build_rank_embed(
            self._rank_view.member, self._rank_view.guild, stat
        )
        await interaction.response.edit_message(embed=embed, view=self.view)


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

        embed = discord.Embed(
            title="⚙️ XP Configuration", color=UTILITY_COLOR
        )
        embed.add_field(name="XP per message", value=f"{xp_min}–{xp_max}", inline=True)
        embed.add_field(name="Cooldown", value=f"{cooldown}s", inline=True)
        embed.add_field(name="Level-up channel", value=channel_str, inline=True)
        embed.set_footer(text="Click a button below to change a setting.")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "This panel isn't for you.", ephemeral=True
            )
            return False
        return True

    _run_checks = interaction_check

    async def _refresh(self, interaction: discord.Interaction):
        await interaction.message.edit(embed=await self.build_embed(), view=self)

    @discord.ui.button(label="XP Range", style=discord.ButtonStyle.blurple, row=0)
    async def btn_xp_range(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ):
        await interaction.response.send_modal(_XpRangeModal(self))

    @discord.ui.button(label="Cooldown", style=discord.ButtonStyle.blurple, row=0)
    async def btn_cooldown(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ):
        await interaction.response.send_modal(_XpCooldownModal(self))

    @discord.ui.button(
        label="Level-up Channel", style=discord.ButtonStyle.blurple, row=0
    )
    async def btn_channel(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_XpChannelModal(self))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass


class _XpRangeModal(discord.ui.Modal, title="Set XP Range"):  # type: ignore[call-arg]
    xp_min = discord.ui.TextInput(
        label="Min XP per message", placeholder="15", max_length=4
    )
    xp_max = discord.ui.TextInput(
        label="Max XP per message", placeholder="25", max_length=4
    )

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


class _XpCooldownModal(discord.ui.Modal, title="Set XP Cooldown"):  # type: ignore[call-arg]
    seconds = discord.ui.TextInput(
        label="Cooldown in seconds", placeholder="60", max_length=5
    )

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


class _XpChannelModal(discord.ui.Modal, title="Level-up Announcement Channel"):  # type: ignore[call-arg]
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
