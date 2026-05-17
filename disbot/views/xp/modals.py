"""XP modals (S4.2-followup extraction).

Five modals extracted from ``cogs/xp_cog.py``:

  _GiveXpModal       — admin "give XP" form (spawned from _XpHubView)
  _ResetXpModal      — admin "reset XP" form (spawned from _XpHubView)
  _XpRangeModal      — XP min/max per message (XpConfigView)
  _XpCooldownModal   — XP gain cooldown seconds (XpConfigView)
  _XpChannelModal    — level-up announcement channel id (XpConfigView)

The three config modals call back into their owning ``XpConfigView``
to refresh the panel after a successful write.  They each invoke
``invalidate_xp_config`` so the F-1 cache picks up the new value on
the next ``on_message`` hot-path read.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from core.runtime.interaction_helpers import safe_defer
from services import xp_service
from utils import db
from utils.guild_config_accessors import invalidate_xp_config
from utils.helpers import _parse_member
from utils.settings_keys import XP_ANNOUNCE_CHANNEL, XP_COOLDOWN, XP_MAX, XP_MIN

if TYPE_CHECKING:
    from views.xp.config_panel import XpConfigView
    from views.xp.main_panel import _XpHubView


class _GiveXpModal(discord.ui.Modal, title="Give XP"):  # type: ignore[call-arg]
    member_input = discord.ui.TextInput(label="User (mention or ID)", max_length=100)  # type: ignore[var-annotated]
    amount_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="XP amount",
        placeholder="e.g. 100",
        max_length=10,
    )

    def __init__(self, hub: _XpHubView):
        super().__init__()
        self._hub = hub

    async def on_submit(self, interaction: discord.Interaction):
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.",
                ephemeral=True,
            )
            return
        try:
            amount = int(self.amount_input.value)
            if amount <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Amount must be a positive integer.",
                ephemeral=True,
            )
            return
        result = await xp_service.award(
            guild_id=interaction.guild_id,
            user_id=member.id,
            amount=amount,
            source="admin:modal_grant",
        )
        await interaction.response.send_message(
            f"✅ Gave **{amount}** XP to {member.mention}. "
            f"Now **{result.new_xp}** XP (Level **{result.new_level}**).",
            ephemeral=True,
        )


class _ResetXpModal(discord.ui.Modal, title="Reset XP"):  # type: ignore[call-arg]
    member_input = discord.ui.TextInput(label="User (mention or ID)", max_length=100)  # type: ignore[var-annotated]
    confirm_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label='Type "CONFIRM" to reset',
        placeholder="CONFIRM",
        max_length=10,
    )

    def __init__(self, hub: _XpHubView):
        super().__init__()
        self._hub = hub

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirm_input.value.strip().upper() != "CONFIRM":
            await interaction.response.send_message(
                "❌ Reset cancelled — type CONFIRM to proceed.",
                ephemeral=True,
            )
            return
        member = _parse_member(interaction.guild, self.member_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.",
                ephemeral=True,
            )
            return
        await xp_service.reset(
            guild_id=interaction.guild_id,
            user_id=member.id,
            source="admin:modal_reset",
            actor_id=interaction.user.id,
        )
        await interaction.response.send_message(
            f"✅ Reset XP for {member.mention}.",
            ephemeral=True,
        )


class _XpRangeModal(discord.ui.Modal, title="Set XP Range"):  # type: ignore[call-arg]
    xp_min = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Min XP per message",
        placeholder="15",
        max_length=4,
    )
    xp_max = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Max XP per message",
        placeholder="25",
        max_length=4,
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
        await db.set_setting(gid, XP_MIN, str(mn))
        await db.set_setting(gid, XP_MAX, str(mx))
        invalidate_xp_config(gid)
        if not await safe_defer(interaction):
            return
        await self.view._refresh(interaction)


class _XpCooldownModal(discord.ui.Modal, title="Set XP Cooldown"):  # type: ignore[call-arg]
    seconds = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Cooldown in seconds",
        placeholder="60",
        max_length=5,
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
                "Must be a non-negative integer.",
                ephemeral=True,
            )
            return
        gid = self.view.ctx.guild.id
        await db.set_setting(gid, XP_COOLDOWN, str(val))
        invalidate_xp_config(gid)
        if not await safe_defer(interaction):
            return
        await self.view._refresh(interaction)


class _XpChannelModal(discord.ui.Modal, title="Level-up Announcement Channel"):  # type: ignore[call-arg]
    channel_id = discord.ui.TextInput(  # type: ignore[var-annotated]
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
                "Enter a valid numeric channel ID, or leave blank.",
                ephemeral=True,
            )
            return
        gid = self.view.ctx.guild.id
        await db.set_setting(gid, XP_ANNOUNCE_CHANNEL, val)
        invalidate_xp_config(gid)
        if not await safe_defer(interaction):
            return
        await self.view._refresh(interaction)
