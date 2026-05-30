"""Moderation modals (S4.3 extraction).

Seven modals extracted from ``cogs/moderation_cog.py``, each spawned
by the corresponding ``ModPanelView`` button:

    _WarnModal           — warn a member (auto-timeout at threshold)
    _TimeoutModal        — timeout a member for N minutes
    _KickModal           — kick a member
    _BanModal            — ban a member
    _UnbanModal          — unban a member by ID
    _ModLogsModal        — view moderation log history for a member
    _ClearWarningsModal  — reset warning count for a member

Each modal performs:
  1. parse the target via ``utils.helpers._parse_member``
  2. run ``_can_act_on_interaction`` for hierarchy/owner safety
  3. perform the Discord-API action
  4. write to ``mod_logs`` via ``db.log_mod_action``
"""

from __future__ import annotations

from datetime import timedelta

import discord

from cogs.moderation._helpers import _can_act_on_interaction
from core.runtime.interaction_helpers import safe_defer, safe_followup
from utils import db
from utils.helpers import _parse_member
from utils.ui_constants import MOD_COLOR


class _WarnModal(discord.ui.Modal, title="Warn Member"):  # type: ignore[call-arg]
    member_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="User (mention, ID, or name)",
        max_length=100,
    )
    reason_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Reason",
        style=discord.TextStyle.paragraph,
        required=False,
        placeholder="No reason provided",
        max_length=500,
    )

    def __init__(self) -> None:
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.",
                ephemeral=True,
            )
            return
        reason = self.reason_input.value or "No reason provided"
        err = _can_act_on_interaction(interaction, member)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if not await safe_defer(interaction):
            return
        # Read through the canonical scalar resolver so coercion +
        # validation are centralised; a malformed stored value falls
        # back to the SettingSpec default instead of raising.
        from services.settings_resolution import resolve_value

        threshold = await resolve_value(
            interaction.guild_id,
            "moderation",
            "warn_threshold",
            3,
        )
        timeout_minutes = await resolve_value(
            interaction.guild_id,
            "moderation",
            "warn_timeout_minutes",
            10,
        )
        count = await db.add_warning(member.id, interaction.guild_id)
        await safe_followup(
            interaction,
            f"⚠️ {member.mention} warned ({count}/{threshold}). Reason: {reason}",
        )
        await db.log_mod_action(
            interaction.guild_id,
            "warn",
            member.id,
            interaction.user.id,
            reason,
        )
        if count >= threshold:
            try:
                until = discord.utils.utcnow() + timedelta(minutes=timeout_minutes)
                await member.timeout(until, reason=f"{threshold} warnings reached.")
                await safe_followup(
                    interaction,
                    f"⏳ {member.mention} timed out for {timeout_minutes} minutes "
                    f"({threshold} warnings).",
                )
                await db.clear_warnings(member.id, interaction.guild_id)
            except discord.Forbidden:
                await safe_followup(
                    interaction,
                    f"⚠️ {threshold} warnings reached but I lack permission to timeout.",
                    ephemeral=True,
                )


class _TimeoutModal(discord.ui.Modal, title="Timeout Member"):  # type: ignore[call-arg]
    member_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="User (mention, ID, or name)",
        max_length=100,
    )
    duration_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Duration (minutes)",
        placeholder="e.g. 30",
        max_length=10,
    )
    reason_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Reason",
        style=discord.TextStyle.paragraph,
        required=False,
        placeholder="No reason provided",
        max_length=500,
    )

    def __init__(self) -> None:
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.",
                ephemeral=True,
            )
            return
        if not self.duration_input.value.isdigit():
            await interaction.response.send_message(
                "❌ Duration must be a whole number of minutes.",
                ephemeral=True,
            )
            return
        duration = int(self.duration_input.value)
        reason = self.reason_input.value or "No reason provided"
        err = _can_act_on_interaction(interaction, member)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if not await safe_defer(interaction):
            return
        try:
            until = discord.utils.utcnow() + timedelta(minutes=duration)
            await member.timeout(until, reason=reason)
            await safe_followup(
                interaction,
                f"⏳ {member.mention} timed out for {duration} minute(s).",
            )
            await db.log_mod_action(
                interaction.guild_id,
                "timeout",
                member.id,
                interaction.user.id,
                f"{duration}m: {reason}",
            )
        except discord.Forbidden:
            await safe_followup(
                interaction,
                "❌ No permission to timeout that user.",
                ephemeral=True,
            )


class _KickModal(discord.ui.Modal, title="Kick Member"):  # type: ignore[call-arg]
    member_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="User (mention, ID, or name)",
        max_length=100,
    )
    reason_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Reason",
        style=discord.TextStyle.paragraph,
        required=False,
        placeholder="No reason provided",
        max_length=500,
    )

    def __init__(self) -> None:
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.",
                ephemeral=True,
            )
            return
        reason = self.reason_input.value or "No reason provided"
        err = _can_act_on_interaction(interaction, member)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if not await safe_defer(interaction):
            return
        try:
            await member.kick(reason=reason)
            await safe_followup(
                interaction,
                f"👢 {member.mention} kicked. Reason: {reason}",
            )
            await db.log_mod_action(
                interaction.guild_id,
                "kick",
                member.id,
                interaction.user.id,
                reason,
            )
        except discord.Forbidden:
            await safe_followup(
                interaction,
                "❌ No permission to kick that user.",
                ephemeral=True,
            )


class _BanModal(discord.ui.Modal, title="Ban Member"):  # type: ignore[call-arg]
    member_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="User (mention, ID, or name)",
        max_length=100,
    )
    reason_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Reason",
        style=discord.TextStyle.paragraph,
        required=False,
        placeholder="No reason provided",
        max_length=500,
    )

    def __init__(self) -> None:
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.",
                ephemeral=True,
            )
            return
        reason = self.reason_input.value or "No reason provided"
        err = _can_act_on_interaction(interaction, member)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if not await safe_defer(interaction):
            return
        try:
            await member.ban(reason=reason)
            await safe_followup(
                interaction,
                f"🚫 {member.mention} banned. Reason: {reason}",
            )
            await db.log_mod_action(
                interaction.guild_id,
                "ban",
                member.id,
                interaction.user.id,
                reason,
            )
        except discord.Forbidden:
            await safe_followup(
                interaction,
                "❌ No permission to ban that user.",
                ephemeral=True,
            )


class _UnbanModal(discord.ui.Modal, title="Unban Member"):  # type: ignore[call-arg]
    user_id_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="User ID",
        placeholder="Right-click user → Copy ID",
        max_length=20,
    )

    def __init__(self) -> None:
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        if not await safe_defer(interaction, ephemeral=True):
            return
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
                interaction.guild_id,
                "unban",
                user.id,
                interaction.user.id,
                "",
            )
        except discord.NotFound:
            await interaction.followup.send(f"❌ User `{user_id}` is not banned.")
        except discord.Forbidden:
            await interaction.followup.send("❌ No permission to unban.")
        except discord.HTTPException as e:
            await interaction.followup.send(f"❌ Failed to unban: {e}")


class _ModLogsModal(discord.ui.Modal, title="View Mod Logs"):  # type: ignore[call-arg]
    member_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="User (mention, ID, or name)",
        max_length=100,
    )

    def __init__(self) -> None:
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.",
                ephemeral=True,
            )
            return
        if not await safe_defer(interaction, ephemeral=True):
            return
        logs = await db.get_mod_logs(member.id, interaction.guild_id, limit=10)
        embed = discord.Embed(
            title=f"📋 Mod Logs — {member.display_name}",
            color=MOD_COLOR,
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
        await safe_followup(interaction, embed=embed, ephemeral=True)


class _ClearWarningsModal(discord.ui.Modal, title="Clear Warnings"):  # type: ignore[call-arg]
    member_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="User (mention, ID, or name)",
        max_length=100,
    )

    def __init__(self) -> None:
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.",
                ephemeral=True,
            )
            return
        if not await safe_defer(interaction, ephemeral=True):
            return
        await db.clear_warnings(member.id, interaction.guild_id)
        await db.log_mod_action(
            interaction.guild_id,
            "clearwarnings",
            member.id,
            interaction.user.id,
            "",
        )
        await safe_followup(
            interaction,
            f"✅ Warnings cleared for {member.mention}.",
            ephemeral=True,
        )
