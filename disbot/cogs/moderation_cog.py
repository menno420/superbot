from __future__ import annotations

import logging
import re
from datetime import timedelta

import discord
from discord import Member
from discord.ext import commands
from utils import db
from utils.helpers import CogMenuView

logger = logging.getLogger("bot")

_MOD_MENU_COMMANDS: list[tuple[str, str, str]] = [
    ("modmenu", "!modmenu", "Show the moderation action panel."),
    ("warn", "!warn <@user> [reason]", "Issue a warning to a member."),
    ("timeout", "!timeout <@user> <minutes> [reason]", "Temporarily mute a member."),
    ("kick", "!kick <@user> [reason]", "Kick a member from the server."),
    ("ban", "!ban <@user> [reason]", "Ban a member from the server."),
    ("unban", "!unban <user#0000>", "Unban a previously banned user."),
]


def _parse_member(guild: discord.Guild, text: str) -> discord.Member | None:
    """Resolve a member from a mention, ID, or username string."""
    text = text.strip()
    mention_match = re.match(r"<@!?(\d+)>", text)
    if mention_match:
        return guild.get_member(int(mention_match.group(1)))
    if text.isdigit():
        return guild.get_member(int(text))
    return discord.utils.find(
        lambda m: m.name == text or m.display_name == text, guild.members
    )


# ---------------------------------------------------------------------------
# Modals
# ---------------------------------------------------------------------------


class _WarnModal(discord.ui.Modal, title="Warn Member"):
    member_input = discord.ui.TextInput(
        label="User (mention, ID, or name)", max_length=100
    )
    reason_input = discord.ui.TextInput(
        label="Reason",
        style=discord.TextStyle.paragraph,
        required=False,
        placeholder="No reason provided",
        max_length=500,
    )

    def __init__(self, cog: "ModerationCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.", ephemeral=True
            )
            return
        reason = self.reason_input.value or "No reason provided"
        err = self.cog._can_act_on_interaction(interaction, member)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return
        count = await db.add_warning(member.id, interaction.guild_id)
        await interaction.response.send_message(
            f"⚠️ {member.mention} warned ({count}/3). Reason: {reason}", ephemeral=False
        )
        await db.log_mod_action(
            interaction.guild_id, "warn", member.id, interaction.user.id, reason
        )
        if count >= 3:
            try:
                until = discord.utils.utcnow() + timedelta(minutes=10)
                await member.timeout(until, reason="3 warnings reached.")
                await interaction.followup.send(
                    f"⏳ {member.mention} timed out for 10 minutes (3 warnings)."
                )
                await db.clear_warnings(member.id, interaction.guild_id)
            except discord.Forbidden:
                await interaction.followup.send(
                    "⚠️ 3 warnings reached but I lack permission to timeout.",
                    ephemeral=True,
                )


class _TimeoutModal(discord.ui.Modal, title="Timeout Member"):
    member_input = discord.ui.TextInput(
        label="User (mention, ID, or name)", max_length=100
    )
    duration_input = discord.ui.TextInput(
        label="Duration (minutes)", placeholder="e.g. 30", max_length=10
    )
    reason_input = discord.ui.TextInput(
        label="Reason",
        style=discord.TextStyle.paragraph,
        required=False,
        placeholder="No reason provided",
        max_length=500,
    )

    def __init__(self, cog: "ModerationCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.", ephemeral=True
            )
            return
        if not self.duration_input.value.isdigit():
            await interaction.response.send_message(
                "❌ Duration must be a whole number of minutes.", ephemeral=True
            )
            return
        duration = int(self.duration_input.value)
        reason = self.reason_input.value or "No reason provided"
        err = self.cog._can_act_on_interaction(interaction, member)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return
        try:
            until = discord.utils.utcnow() + timedelta(minutes=duration)
            await member.timeout(until, reason=reason)
            await interaction.response.send_message(
                f"⏳ {member.mention} timed out for {duration} minute(s)."
            )
            await db.log_mod_action(
                interaction.guild_id,
                "timeout",
                member.id,
                interaction.user.id,
                f"{duration}m: {reason}",
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ No permission to timeout that user.", ephemeral=True
            )


class _KickModal(discord.ui.Modal, title="Kick Member"):
    member_input = discord.ui.TextInput(
        label="User (mention, ID, or name)", max_length=100
    )
    reason_input = discord.ui.TextInput(
        label="Reason",
        style=discord.TextStyle.paragraph,
        required=False,
        placeholder="No reason provided",
        max_length=500,
    )

    def __init__(self, cog: "ModerationCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.", ephemeral=True
            )
            return
        reason = self.reason_input.value or "No reason provided"
        err = self.cog._can_act_on_interaction(interaction, member)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(
                f"👢 {member.mention} kicked. Reason: {reason}"
            )
            await db.log_mod_action(
                interaction.guild_id, "kick", member.id, interaction.user.id, reason
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ No permission to kick that user.", ephemeral=True
            )


class _BanModal(discord.ui.Modal, title="Ban Member"):
    member_input = discord.ui.TextInput(
        label="User (mention, ID, or name)", max_length=100
    )
    reason_input = discord.ui.TextInput(
        label="Reason",
        style=discord.TextStyle.paragraph,
        required=False,
        placeholder="No reason provided",
        max_length=500,
    )

    def __init__(self, cog: "ModerationCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.", ephemeral=True
            )
            return
        reason = self.reason_input.value or "No reason provided"
        err = self.cog._can_act_on_interaction(interaction, member)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(
                f"🚫 {member.mention} banned. Reason: {reason}"
            )
            await db.log_mod_action(
                interaction.guild_id, "ban", member.id, interaction.user.id, reason
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ No permission to ban that user.", ephemeral=True
            )


class _UnbanModal(discord.ui.Modal, title="Unban Member"):
    username_input = discord.ui.TextInput(label="Username (exact)", max_length=200)

    def __init__(self, cog: "ModerationCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            bans = [entry async for entry in interaction.guild.bans()]
        except discord.Forbidden:
            await interaction.followup.send("❌ No permission to view the ban list.")
            return
        for entry in bans:
            if entry.user.name == self.username_input.value:
                await interaction.guild.unban(entry.user)
                await interaction.followup.send(f"✅ {entry.user.mention} unbanned.")
                await db.log_mod_action(
                    interaction.guild_id,
                    "unban",
                    entry.user.id,
                    interaction.user.id,
                    "",
                )
                return
        await interaction.followup.send(
            f"❌ No banned user found with name `{self.username_input.value}`."
        )


# ---------------------------------------------------------------------------
# Moderation action panel view
# ---------------------------------------------------------------------------


class _ModPanelView(discord.ui.View):
    """Interactive moderation panel with quick-action modal buttons."""

    def __init__(self, cog: "ModerationCog"):
        super().__init__(timeout=180)
        self.cog = cog
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "❌ You need Moderate Members permission.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass

    @discord.ui.button(label="⚠️ Warn", style=discord.ButtonStyle.primary, row=0)
    async def warn_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(_WarnModal(self.cog))

    @discord.ui.button(label="⏳ Timeout", style=discord.ButtonStyle.primary, row=0)
    async def timeout_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(_TimeoutModal(self.cog))

    @discord.ui.button(label="👢 Kick", style=discord.ButtonStyle.danger, row=0)
    async def kick_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(_KickModal(self.cog))

    @discord.ui.button(label="🚫 Ban", style=discord.ButtonStyle.danger, row=1)
    async def ban_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(_BanModal(self.cog))

    @discord.ui.button(label="✅ Unban", style=discord.ButtonStyle.success, row=1)
    async def unban_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(_UnbanModal(self.cog))


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _can_act_on(self, ctx, member: Member) -> str | None:
        if member == ctx.guild.owner:
            return "❌ You cannot perform this action on the server owner."
        if member.top_role >= ctx.author.top_role:
            return "❌ You cannot perform this action on someone with an equal or higher role."
        if member.top_role >= ctx.guild.me.top_role:
            return "❌ I cannot perform this action — that member has a higher role than me."
        return None

    def _can_act_on_interaction(
        self, interaction: discord.Interaction, member: Member
    ) -> str | None:
        if member == interaction.guild.owner:
            return "❌ You cannot perform this action on the server owner."
        actor = interaction.guild.get_member(interaction.user.id)
        if actor and member.top_role >= actor.top_role:
            return "❌ You cannot perform this action on someone with an equal or higher role."
        if member.top_role >= interaction.guild.me.top_role:
            return "❌ I cannot perform this action — that member has a higher role than me."
        return None

    async def log_action(
        self, ctx, action: str, member, reason: str = "No reason provided"
    ):
        await db.log_mod_action(ctx.guild.id, action, member.id, ctx.author.id, reason)
        logger.info(
            "MOD | %s | %s | by %s | %s", action.upper(), member, ctx.author, reason
        )

    # ------------------------------------------------------------------
    # Moderation panel (action-first interactive UI)
    # ------------------------------------------------------------------

    @commands.command(name="modmenu")
    @commands.has_permissions(moderate_members=True)
    async def mod_menu(self, ctx):
        """Show the interactive moderation action panel."""
        embed = discord.Embed(
            title="🔨 Moderation Panel",
            description=(
                "Click a button to take a moderation action.\n"
                "You'll be prompted to enter the user and reason."
            ),
            color=discord.Color.red(),
        )
        embed.add_field(
            name="⚠️ Warn", value="Issue a warning (auto-timeout at 3)", inline=True
        )
        embed.add_field(
            name="⏳ Timeout", value="Temporarily mute for N minutes", inline=True
        )
        embed.add_field(name="👢 Kick", value="Remove from server", inline=True)
        embed.add_field(name="🚫 Ban", value="Permanently ban", inline=True)
        embed.add_field(name="✅ Unban", value="Lift a ban by username", inline=True)
        view = _ModPanelView(self)
        view.message = await ctx.send(embed=embed, view=view)

    # ------------------------------------------------------------------
    # Traditional text commands (kept for direct use)
    # ------------------------------------------------------------------

    @commands.command(name="warn")
    @commands.has_permissions(manage_roles=True)
    async def warn(self, ctx, member: Member, *, reason="No reason provided"):
        """Warn a user. Three warnings result in a 10-minute timeout."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return
        count = await db.add_warning(member.id, ctx.guild.id)
        await ctx.send(f"⚠️ {member.mention} warned ({count}/3). Reason: {reason}")
        await self.log_action(ctx, "warn", member, reason)
        if count >= 3:
            try:
                until = discord.utils.utcnow() + timedelta(minutes=10)
                await member.timeout(until, reason="3 warnings reached.")
                await ctx.send(
                    f"⏳ {member.mention} timed out for 10 minutes (3 warnings)."
                )
                await db.clear_warnings(member.id, ctx.guild.id)
            except discord.Forbidden:
                await ctx.send(
                    "⚠️ Reached 3 warnings but I lack permission to timeout this user."
                )

    @commands.command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: Member, duration: int):
        """Timeout a member for a given number of minutes."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return
        try:
            until = discord.utils.utcnow() + timedelta(minutes=duration)
            await member.timeout(until, reason=f"Timeout by {ctx.author}")
            await ctx.send(f"⏳ {member.mention} timed out for {duration} minute(s).")
            await self.log_action(ctx, "timeout", member, f"{duration} minutes")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to timeout that user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to timeout: {e}")

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: Member, *, reason="No reason provided"):
        """Kick a member from the server."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return
        try:
            await member.kick(reason=reason)
            await ctx.send(f"👢 {member.mention} kicked. Reason: {reason}")
            await self.log_action(ctx, "kick", member, reason)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick that user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to kick: {e}")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: Member, *, reason="No reason provided"):
        """Ban a member from the server."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return
        try:
            await member.ban(reason=reason)
            await ctx.send(f"🚫 {member.mention} banned. Reason: {reason}")
            await self.log_action(ctx, "ban", member, reason)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban that user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to ban: {e}")

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member_name: str):
        """Unban a user by their username."""
        try:
            bans = [entry async for entry in ctx.guild.bans()]
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to view the ban list.")
            return
        for entry in bans:
            if entry.user.name == member_name:
                await ctx.guild.unban(entry.user)
                await ctx.send(f"✅ {entry.user.mention} unbanned.")
                await self.log_action(ctx, "unban", entry.user)
                return
        await ctx.send(f"❌ No banned user found with name `{member_name}`.")


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
