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

Each action modal performs:
  1. parse the target via ``utils.helpers._parse_member``
  2. run ``_can_act_on_interaction`` for hierarchy/owner safety
  3. ``safe_defer`` (slow-path ACK), then dispatch the action through
     ``services.moderation_service`` — the single audited writer that
     appends the ``mod_logs`` row, emits the ``audit.action_recorded``
     companion, and fires ``EVT_MOD_ACTION``.  No direct Discord-API
     mutation or ``mod_logs`` write happens here (pinned by
     ``tests/unit/invariants/test_no_direct_moderation_writes.py``).

``_ModLogsModal`` is a read-only lookup and keeps its direct
``db.get_mod_logs`` read.
"""

from __future__ import annotations

from datetime import timedelta

import discord

from cogs.moderation._helpers import (
    _can_act_on_interaction,
    _sweepable_channel,
    render_cleanup_outcome_line,
    render_warn_outcome_lines,
)
from core.runtime.interaction_helpers import safe_defer, safe_followup
from services import moderation_service
from services.moderation_service import ReasonRequiredError
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
        # The service owns require_reason enforcement and the escalation ladder
        # (threshold → configured action, reset on success); the modal just
        # renders the returned WarnOutcome — same shape as the !warn command.
        try:
            outcome = await moderation_service.warn(
                member,
                reason=reason,
                actor_id=interaction.user.id,
            )
        except ReasonRequiredError as exc:
            await safe_followup(interaction, f"❌ {exc}", ephemeral=True)
            return
        for line in render_warn_outcome_lines(member.mention, reason, outcome):
            await safe_followup(interaction, line)


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
            # Preserve the surface's historical mod_logs reason shape
            # ("30m: reason") until moderation config models duration.
            await moderation_service.timeout(
                member,
                until=until,
                reason=f"{duration}m: {reason}",
                actor_id=interaction.user.id,
            )
            await safe_followup(
                interaction,
                f"⏳ {member.mention} timed out for {duration} minute(s).",
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
            outcome = await moderation_service.kick(
                member,
                reason=reason,
                actor_id=interaction.user.id,
                channel=_sweepable_channel(interaction.channel),
            )
            await safe_followup(
                interaction,
                f"👢 {member.mention} kicked. Reason: {reason}",
            )
            cleanup_line = render_cleanup_outcome_line(member.mention, outcome)
            if cleanup_line:
                await safe_followup(interaction, cleanup_line)
        except ReasonRequiredError as exc:
            await safe_followup(interaction, f"❌ {exc}", ephemeral=True)
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
            outcome = await moderation_service.ban(
                interaction.guild,
                member,
                reason=reason,
                actor_id=interaction.user.id,
                channel=_sweepable_channel(interaction.channel),
            )
            await safe_followup(
                interaction,
                f"🚫 {member.mention} banned. Reason: {reason}",
            )
            cleanup_line = render_cleanup_outcome_line(member.mention, outcome)
            if cleanup_line:
                await safe_followup(interaction, cleanup_line)
        except ReasonRequiredError as exc:
            await safe_followup(interaction, f"❌ {exc}", ephemeral=True)
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
            await moderation_service.unban(
                interaction.guild,
                user,
                reason="",
                actor_id=interaction.user.id,
            )
            await interaction.followup.send(f"✅ {user.mention} unbanned.")
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
        await moderation_service.clear_warnings(
            interaction.guild_id,
            member.id,
            actor_id=interaction.user.id,
        )
        await safe_followup(
            interaction,
            f"✅ Warnings cleared for {member.mention}.",
            ephemeral=True,
        )
