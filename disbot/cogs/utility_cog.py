from __future__ import annotations

import asyncio

import discord
from discord.ext import commands
from utils import embeds as em
from utils.ui_constants import INFO_COLOR, SUCCESS_COLOR, UTILITY_COLOR
from views.base import BaseView


async def _remind_later(
    user: discord.User,
    channel: discord.abc.Messageable,
    delay: float,
    message: str,
) -> None:
    await asyncio.sleep(delay)
    try:
        await channel.send(f"⏰ {user.mention} — Reminder: {message}")
    except Exception:
        pass


class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="utilitymenu")
    async def utility_menu(self, ctx):
        """Open the interactive utility panel."""
        view = _UtilityPanelView(ctx)
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
                color=SUCCESS_COLOR,
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
                color=INFO_COLOR,
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

    @commands.command(name="serverinfo", hidden=True)
    async def serverinfo(self, ctx):
        """Alias for !info server."""
        await ctx.invoke(self.info, target="server")

    @commands.command(name="userinfo", hidden=True)
    async def userinfo(self, ctx, member: discord.Member = None):
        """Alias for !info user [@member]."""
        await ctx.invoke(self.info, target="user", member=member)

    @commands.command(name="avatar", hidden=True)
    async def avatar(self, ctx, member: discord.Member = None):
        """Display a user's avatar."""
        member = member or ctx.author
        embed = discord.Embed(title=f"{member}'s Avatar", color=INFO_COLOR)
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
        asyncio.create_task(_remind_later(ctx.author, ctx.channel, time * 60, message))

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
            color=INFO_COLOR,
        )
        poll_msg = await ctx.send(embed=embed)
        for i in range(len(options)):
            await poll_msg.add_reaction(f"{i+1}\N{COMBINING ENCLOSING KEYCAP}")


# ---------------------------------------------------------------------------
# Utility Panel View
# ---------------------------------------------------------------------------


class _UtilityPanelView(BaseView):
    """Interactive utility panel — quick access to common utility actions."""

    def __init__(self, ctx: commands.Context):
        super().__init__(ctx.author, public=True, timeout=180)
        self.ctx = ctx

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🔧 Utility Panel",
            description=(
                "**🖥️ Server Info** — server statistics\n"
                "**👤 User Info** — your profile details\n"
                "**🖼️ Avatar** — display your avatar\n"
                "**📊 Poll** — create a reaction poll\n"
                "**🔔 Remind Me** — set a timed reminder\n"
                "**🔗 Invite** — generate a one-use server invite"
            ),
            color=UTILITY_COLOR,
        )
        embed.set_footer(text="Click an action below.")
        return embed

    @discord.ui.button(label="🖥️ Server Info", style=discord.ButtonStyle.blurple, row=0)
    async def serverinfo_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"{guild.name}",
            description="Server Information",
            color=INFO_COLOR,
        )
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Boost Level", value=str(guild.premium_tier), inline=True)
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
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="👤 User Info", style=discord.ButtonStyle.blurple, row=0)
    async def userinfo_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ):
        member = interaction.user
        embed = discord.Embed(
            title=f"User Info — {member}",
            color=SUCCESS_COLOR,
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
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🖼️ Avatar", style=discord.ButtonStyle.blurple, row=0)
    async def avatar_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        member = interaction.user
        embed = discord.Embed(title=f"{member}'s Avatar", color=INFO_COLOR)
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="📊 Poll", style=discord.ButtonStyle.grey, row=1)
    async def poll_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_PollModal(interaction.channel))

    @discord.ui.button(label="🔔 Remind Me", style=discord.ButtonStyle.grey, row=1)
    async def remind_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(
            _RemindModal(interaction.user, interaction.channel)
        )

    @discord.ui.button(label="🔗 Invite", style=discord.ButtonStyle.grey, row=1)
    async def invite_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not interaction.user.guild_permissions.create_instant_invite:
            await interaction.response.send_message(
                "❌ You need **Create Invite** permission.", ephemeral=True
            )
            return
        invite = await interaction.channel.create_invite(max_uses=1, unique=True)
        await interaction.response.send_message(
            f"🔗 One-use invite: {invite.url}", ephemeral=True
        )

    @discord.ui.button(label="↩ Overview", style=discord.ButtonStyle.secondary, row=2)
    async def overview_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ):
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


# ---------------------------------------------------------------------------
# Poll Modal
# ---------------------------------------------------------------------------


class _PollModal(discord.ui.Modal, title="Create Poll"):  # type: ignore[call-arg]
    question = discord.ui.TextInput(label="Poll question", max_length=200)
    options = discord.ui.TextInput(
        label="Options (one per line, 2–10)",
        style=discord.TextStyle.paragraph,
        placeholder="Option 1\nOption 2\nOption 3",
        max_length=500,
    )

    def __init__(self, channel: discord.abc.Messageable):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        opts = [o.strip() for o in self.options.value.split("\n") if o.strip()]
        if len(opts) < 2:
            await interaction.response.send_message(
                "❌ Need at least 2 options.", ephemeral=True
            )
            return
        if len(opts) > 10:
            await interaction.response.send_message(
                "❌ Max 10 options.", ephemeral=True
            )
            return
        embed = discord.Embed(
            title=f"Poll: {self.question.value}",
            description="\n".join(f"{i+1}. {opt}" for i, opt in enumerate(opts)),
            color=INFO_COLOR,
        )
        poll_msg = await self.channel.send(embed=embed)
        for i in range(len(opts)):
            await poll_msg.add_reaction(f"{i+1}\N{COMBINING ENCLOSING KEYCAP}")
        await interaction.response.send_message("✅ Poll created!", ephemeral=True)


# ---------------------------------------------------------------------------
# Remind Modal
# ---------------------------------------------------------------------------


class _RemindModal(discord.ui.Modal, title="Set Reminder"):  # type: ignore[call-arg]
    minutes = discord.ui.TextInput(
        label="Minutes from now", placeholder="30", max_length=5
    )
    message = discord.ui.TextInput(
        label="Reminder message",
        style=discord.TextStyle.paragraph,
        max_length=500,
    )

    def __init__(self, user: discord.User, channel: discord.abc.Messageable):
        super().__init__()
        self.user = user
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            t = int(self.minutes.value)
            if t <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Minutes must be a positive integer.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"⏳ Reminder set for **{t}** minute(s): {self.message.value}",
            ephemeral=True,
        )
        asyncio.create_task(
            _remind_later(self.user, self.channel, t * 60, self.message.value)
        )


async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
