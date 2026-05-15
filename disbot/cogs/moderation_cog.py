from __future__ import annotations

import logging
import re
from datetime import timedelta

import discord
from discord import Member
from discord.ext import commands
from utils import db

logger = logging.getLogger("bot")


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


class _WarnModal(discord.ui.Modal, title="Warn Member"):  # type: ignore[call-arg]
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
        threshold = int(
            await db.get_setting(interaction.guild_id, "warn_threshold", "3")
        )
        timeout_minutes = int(
            await db.get_setting(interaction.guild_id, "warn_timeout_minutes", "10")
        )
        count = await db.add_warning(member.id, interaction.guild_id)
        await interaction.response.send_message(
            f"⚠️ {member.mention} warned ({count}/{threshold}). Reason: {reason}",
            ephemeral=False,
        )
        await db.log_mod_action(
            interaction.guild_id, "warn", member.id, interaction.user.id, reason
        )
        if count >= threshold:
            try:
                until = discord.utils.utcnow() + timedelta(minutes=timeout_minutes)
                await member.timeout(until, reason=f"{threshold} warnings reached.")
                await interaction.followup.send(
                    f"⏳ {member.mention} timed out for {timeout_minutes} minutes "
                    f"({threshold} warnings)."
                )
                await db.clear_warnings(member.id, interaction.guild_id)
            except discord.Forbidden:
                await interaction.followup.send(
                    f"⚠️ {threshold} warnings reached but I lack permission to timeout.",
                    ephemeral=True,
                )


class _TimeoutModal(discord.ui.Modal, title="Timeout Member"):  # type: ignore[call-arg]
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


class _KickModal(discord.ui.Modal, title="Kick Member"):  # type: ignore[call-arg]
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


class _BanModal(discord.ui.Modal, title="Ban Member"):  # type: ignore[call-arg]
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


class _UnbanModal(discord.ui.Modal, title="Unban Member"):  # type: ignore[call-arg]
    user_id_input = discord.ui.TextInput(
        label="User ID", placeholder="Right-click user → Copy ID", max_length=20
    )

    def __init__(self, cog: "ModerationCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        raw = self.user_id_input.value.strip()
        if not raw.isdigit():
            await interaction.followup.send("❌ Please enter a valid numeric user ID.")
            return
        user_id = int(raw)
        try:
            user = await interaction.client.fetch_user(user_id)
        except discord.NotFound:
            await interaction.followup.send(f"❌ No user found with ID `{user_id}`.")
            return
        except discord.HTTPException as e:
            await interaction.followup.send(f"❌ Failed to fetch user: {e}")
            return
        try:
            await interaction.guild.unban(user)
            await interaction.followup.send(f"✅ {user.mention} unbanned.")
            await db.log_mod_action(
                interaction.guild_id, "unban", user.id, interaction.user.id, ""
            )
        except discord.NotFound:
            await interaction.followup.send(f"❌ User `{user_id}` is not banned.")
        except discord.Forbidden:
            await interaction.followup.send("❌ No permission to unban.")
        except discord.HTTPException as e:
            await interaction.followup.send(f"❌ Failed to unban: {e}")


class _ModLogsModal(discord.ui.Modal, title="View Mod Logs"):  # type: ignore[call-arg]
    member_input = discord.ui.TextInput(
        label="User (mention, ID, or name)", max_length=100
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
        logs = await db.get_mod_logs(member.id, interaction.guild_id, limit=10)
        embed = discord.Embed(
            title=f"📋 Mod Logs — {member.display_name}",
            color=discord.Color.orange(),
        )
        if not logs:
            embed.description = "No moderation history found."
        else:
            for entry in logs:
                embed.add_field(
                    name=f"{entry['action'].upper()} — {entry['timestamp']}",
                    value=f"By <@{entry['moderator_id']}> | {entry['reason']}",
                    inline=False,
                )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class _ClearWarningsModal(discord.ui.Modal, title="Clear Warnings"):  # type: ignore[call-arg]
    member_input = discord.ui.TextInput(
        label="User (mention, ID, or name)", max_length=100
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
        await db.clear_warnings(member.id, interaction.guild_id)
        await db.log_mod_action(
            interaction.guild_id, "clearwarnings", member.id, interaction.user.id, ""
        )
        await interaction.response.send_message(
            f"✅ Warnings cleared for {member.mention}.", ephemeral=True
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
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
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

    @discord.ui.button(label="📋 Mod Logs", style=discord.ButtonStyle.grey, row=1)
    async def modlogs_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_ModLogsModal(self.cog))

    @discord.ui.button(label="⬛ Clear Warnings", style=discord.ButtonStyle.grey, row=2)
    async def clearwarn_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ):
        await interaction.response.send_modal(_ClearWarningsModal(self.cog))


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
        """Warn a user. Auto-timeouts at the configured threshold (default: 3)."""
        err = self._can_act_on(ctx, member)
        if err:
            await ctx.send(err)
            return
        threshold = int(await db.get_setting(ctx.guild.id, "warn_threshold", "3"))
        timeout_minutes = int(
            await db.get_setting(ctx.guild.id, "warn_timeout_minutes", "10")
        )
        count = await db.add_warning(member.id, ctx.guild.id)
        await ctx.send(
            f"⚠️ {member.mention} warned ({count}/{threshold}). Reason: {reason}"
        )
        await self.log_action(ctx, "warn", member, reason)
        if count >= threshold:
            try:
                until = discord.utils.utcnow() + timedelta(minutes=timeout_minutes)
                await member.timeout(until, reason=f"{threshold} warnings reached.")
                await ctx.send(
                    f"⏳ {member.mention} timed out for {timeout_minutes} minutes "
                    f"({threshold} warnings)."
                )
                await db.clear_warnings(member.id, ctx.guild.id)
            except discord.Forbidden:
                await ctx.send(
                    f"⚠️ Reached {threshold} warnings but I lack permission to timeout this user."
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
    async def unban(self, ctx, user_id: int):
        """Unban a user by their Discord user ID."""
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound:
            await ctx.send(f"❌ No user found with ID `{user_id}`.")
            return
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to fetch user: {e}")
            return
        try:
            await ctx.guild.unban(user)
            await ctx.send(f"✅ {user.mention} unbanned.")
            await self.log_action(ctx, "unban", user)
        except discord.NotFound:
            await ctx.send(f"❌ User `{user_id}` is not banned.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unban.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to unban: {e}")

    @commands.command(name="clearwarnings")
    @commands.has_permissions(manage_roles=True)
    async def clearwarnings(self, ctx, member: Member):
        """Clear all warnings for a member."""
        await db.clear_warnings(member.id, ctx.guild.id)
        await ctx.send(f"✅ Warnings cleared for {member.mention}.")
        await self.log_action(ctx, "clearwarnings", member)

    @commands.command(name="modlogs")
    @commands.has_permissions(manage_roles=True)
    async def modlogs(self, ctx, member: Member):
        """Show moderation log history for a member."""
        logs = await db.get_mod_logs(member.id, ctx.guild.id, limit=10)
        embed = discord.Embed(
            title=f"📋 Mod Logs — {member.display_name}",
            color=discord.Color.orange(),
        )
        if not logs:
            embed.description = "No moderation history found."
        else:
            for entry in logs:
                embed.add_field(
                    name=f"{entry['action'].upper()} — {entry['timestamp']}",
                    value=f"By <@{entry['moderator_id']}> | {entry['reason']}",
                    inline=False,
                )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
