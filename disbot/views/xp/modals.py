"""XP modals (S4.2-followup extraction, PR #5 pipeline migration).

Five modals extracted from ``cogs/xp_cog.py``:

  _GiveXpModal       — admin "give XP" form (spawned from _XpHubView)
  _ResetXpModal      — admin "reset XP" form (spawned from _XpHubView)
  _XpRangeModal      — XP min/max per message (XpConfigView)
  _XpCooldownModal   — XP gain cooldown seconds (XpConfigView)
  _XpChannelModal    — level-up announcement channel id (XpConfigView)

The three config modals (range / cooldown / channel) write through
:class:`services.settings_mutation.SettingsMutationPipeline` since
PR #5.  The pipeline handles audit, the per-key SettingSpec-lane
cache invalidation, and event emission — each scalar value lands
with a row in ``settings_mutation_audit``.

After every successful pipeline write, the helper also calls
:func:`utils.guild_config_accessors.invalidate_xp_config` to drop the
legacy composite ``XpConfig`` cache that the XP ``on_message`` hot
path consumes.  The pipeline's own invalidation covers the per-key
SettingSpec lane only; the composite cache is owned by
``guild_config_accessors`` and must be poked separately until the
hot path migrates to SettingSpec reads.

The ``_GiveXpModal`` and ``_ResetXpModal`` flows are unchanged: they
use ``xp_service.award`` / ``xp_service.reset`` which are domain
services, not legacy-KV writes, so the pipeline is not involved.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from core.runtime.interaction_helpers import safe_defer
from services import xp_service
from utils.guild_config_accessors import invalidate_xp_config
from utils.helpers import _parse_member

if TYPE_CHECKING:
    from views.xp.config_panel import XpConfigView
    from views.xp.main_panel import _XpHubView

logger = logging.getLogger("bot.views.xp.modals")


# ---------------------------------------------------------------------------
# Shared pipeline helper
# ---------------------------------------------------------------------------


async def _set_xp_setting_via_pipeline(
    interaction: discord.Interaction,
    name: str,
    value: object,
) -> bool:
    """Write a single ``(xp, name)`` value through SettingsMutationPipeline.

    Returns True on success.  On failure sends an ephemeral message
    describing the error and returns False so the caller can short-
    circuit before refreshing the parent view.
    """
    from services.settings_mutation import (
        SettingsCoercionError,
        SettingsMutationError,
        SettingsMutationPipeline,
        SettingsValidationError,
    )

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "❌ XP config requires a guild context.",
            ephemeral=True,
        )
        return False
    try:
        await SettingsMutationPipeline().set_value(
            guild,
            "xp",
            name,
            value,
            interaction.user,
        )
    except (SettingsCoercionError, SettingsValidationError) as exc:
        await interaction.response.send_message(
            f"❌ {exc}",
            ephemeral=True,
        )
        return False
    except SettingsMutationError as exc:
        await interaction.response.send_message(
            f"❌ {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return False
    except Exception as exc:  # noqa: BLE001 — defensive
        logger.exception(
            "XP modal pipeline write failed for xp.%s",
            name,
        )
        await interaction.response.send_message(
            f"❌ Unexpected error: {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return False
    # The pipeline invalidates the per-key SettingSpec lane via
    # ``invalidate_setting_value``.  The legacy composite
    # ``XpConfig`` accessor used by the XP on_message hot path is a
    # separate cache; drop it explicitly so the next message read
    # sees the new value without waiting for the TTL.
    invalidate_xp_config(guild.id)
    return True


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
            actor_type="admin",
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
        except ValueError:
            await interaction.response.send_message(
                "❌ Both values must be integers.",
                ephemeral=True,
            )
            return
        if mx < mn:
            await interaction.response.send_message(
                "❌ Max must be ≥ min.",
                ephemeral=True,
            )
            return
        # The xp_min / xp_max SettingSpecs each enforce
        # _validate_positive_int via the pipeline; per-field errors
        # surface as ephemerals from _set_xp_setting_via_pipeline.
        if not await _set_xp_setting_via_pipeline(interaction, "xp_min", mn):
            return
        if not await _set_xp_setting_via_pipeline(interaction, "xp_max", mx):
            return
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
        except ValueError:
            await interaction.response.send_message(
                "❌ Cooldown must be an integer.",
                ephemeral=True,
            )
            return
        if not await _set_xp_setting_via_pipeline(interaction, "xp_cooldown", val):
            return
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
        # The xp_announce_channel SettingSpec's validator enforces
        # "empty or numeric"; surface any failure as an ephemeral and
        # bail before touching the parent view.
        val = self.channel_id.value.strip()
        if not await _set_xp_setting_via_pipeline(
            interaction,
            "xp_announce_channel",
            val,
        ):
            return
        if not await safe_defer(interaction):
            return
        await self.view._refresh(interaction)
