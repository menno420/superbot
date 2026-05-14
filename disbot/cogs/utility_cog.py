from __future__ import annotations

import asyncio

import discord
from discord.ext import commands
from utils import embeds as em
from utils.helpers import CogMenuView

_UTILITY_MENU_COMMANDS: list[tuple[str, str, str]] = [
    ("utilitymenu", "!utilitymenu", "Show this utility command menu."),
    (
        "info",
        "!info [server|user] [@user]",
        "Server or user info (defaults to server).",
    ),
    ("avatar", "!avatar [@user]", "Display a user's full-size avatar."),
    (
        "poll",
        "!poll <question> opt1 opt2…",
        "Create a reaction poll with up to 10 options.",
    ),
    ("clear", "!clear [amount]", "Purge up to 100 messages (default: 5)."),
    ("invite", "!invite", "Generate a one-use server invite link."),
    (
        "remind",
        "!remind <minutes> <message>",
        "Set a reminder (bot DMs/pings you after delay).",
    ),
]


class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="utilitymenu")
    async def utility_menu(self, ctx):
        """Show a quick-reference menu for all utility commands."""
        view = CogMenuView(ctx, "🔧 Utility Commands", _UTILITY_MENU_COMMANDS)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg

    @commands.command(name="clear", aliases=["purge"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 5):
        """Purge messages. Max 100."""
        if amount <= 0:
            await ctx.send(
                embed=em.error("Please specify a number greater than 0."),
                delete_after=5,
            )
            return
        if amount > 100:
            await ctx.send(
                embed=em.error("You can only clear up to 100 messages at a time."),
                delete_after=5,
            )
            return
        deleted = await ctx.channel.purge(limit=amount)
        msg = await ctx.send(f"Cleared {len(deleted)} messages.")
        await msg.delete(delay=5)

    @commands.command(name="info")
    async def info(self, ctx, target: str = "server", member: discord.Member = None):
        """Show server or user info.  !info [server|user] [@mention]"""
        if target.lower() in ("user", "u") or member:
            member = member or ctx.author
            embed = discord.Embed(
                title=f"User Info — {member}",
                color=discord.Color.green(),
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Username", value=member.name, inline=True)
            embed.add_field(name="User ID", value=str(member.id), inline=True)
            embed.add_field(
                name="Joined Server",
                value=member.joined_at.strftime("%Y-%m-%d"),
                inline=True,
            )
            embed.add_field(
                name="Joined Discord",
                value=member.created_at.strftime("%Y-%m-%d"),
                inline=True,
            )
            embed.add_field(
                name="Status", value=str(member.status).capitalize(), inline=True
            )
            embed.add_field(
                name="Activity",
                value=member.activity.name if member.activity else "None",
                inline=True,
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
        else:
            guild = ctx.guild
            embed = discord.Embed(
                title=f"{guild.name}",
                description="Server Information",
                color=discord.Color.blue(),
            )
            embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
            embed.add_field(name="Members", value=str(guild.member_count), inline=True)
            embed.add_field(
                name="Boost Level", value=str(guild.premium_tier), inline=True
            )
            embed.add_field(
                name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True
            )
            embed.add_field(
                name="Text Channels", value=str(len(guild.text_channels)), inline=True
            )
            embed.add_field(
                name="Voice Channels", value=str(len(guild.voice_channels)), inline=True
            )
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
        await ctx.send(embed=embed)

    # Keep !serverinfo and !userinfo as thin aliases for backwards compatibility
    @commands.command(name="serverinfo")
    async def serverinfo(self, ctx):
        """Alias for !info server."""
        await ctx.invoke(self.info, target="server")

    @commands.command(name="userinfo")
    async def userinfo(self, ctx, member: discord.Member = None):
        """Alias for !info user [@member]."""
        await ctx.invoke(self.info, target="user", member=member)

    @commands.command(name="avatar")
    async def avatar(self, ctx, member: discord.Member = None):
        """Display a user's avatar."""
        member = member or ctx.author
        embed = discord.Embed(title=f"{member}'s Avatar", color=discord.Color.blue())
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="remind")
    async def remind(self, ctx, time: int, *, message: str):
        """Set a reminder.  !remind <minutes> <message>"""
        if time <= 0:
            await ctx.send(
                embed=em.error("Please specify a time greater than 0 minutes.")
            )
            return
        await ctx.send(f"⏳ Reminder set for **{time}** minute(s): {message}")
        task = asyncio.create_task(self._remind_after(ctx, time * 60, message))

    async def _remind_after(
        self, ctx: commands.Context, delay: float, message: str
    ) -> None:
        await asyncio.sleep(delay)
        try:
            await ctx.send(f"⏰ {ctx.author.mention} — Reminder: {message}")
        except Exception:
            pass

    @commands.command(name="invite")
    @commands.has_permissions(create_instant_invite=True)
    async def invite(self, ctx):
        """Generate a one-use server invite."""
        invite = await ctx.channel.create_invite(max_uses=1, unique=True)
        await ctx.send(f"Here is your invite link (valid for 1 use): {invite.url}")

    @commands.command(name="poll")
    async def poll(self, ctx, question: str, *options):
        """Create a simple reaction poll."""
        if len(options) < 2:
            await ctx.send(embed=em.error("You need at least two options for a poll."))
            return
        if len(options) > 10:
            await ctx.send(embed=em.error("You can only provide up to 10 options."))
            return
        embed = discord.Embed(
            title=f"Poll: {question}",
            description="\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options)),
            color=discord.Color.blue(),
        )
        poll_msg = await ctx.send(embed=embed)
        for i in range(len(options)):
            await poll_msg.add_reaction(f"{i+1}\N{COMBINING ENCLOSING KEYCAP}")


async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
