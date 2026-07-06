"""RoleSettingSelectView — S7 edit widget for role-typed settings.

Dispatched when a ``SettingSpec`` declares ``input_hint="role"``.
The setting's value_type is ``str`` and the underlying value is the
numeric Discord role ID (or ``""`` to clear).  The widget renders a
native :class:`discord.ui.RoleSelect` so the operator picks a role
by name instead of typing an ID.

Mirrors the channel-select widget's flow:

  1. Operator picks a setting in the SubsystemSettingsView's edit
     dropdown.
  2. The dispatcher sees ``SettingSpec.input_hint == "role"`` and
     replies with an ephemeral message hosting a
     :class:`RoleSettingSelectView`.
  3. Operator picks the role from the native role select OR clicks
     "Clear" to remove the binding.
  4. The callback writes through
     :class:`services.settings_mutation.SettingsMutationPipeline`.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.views.settings.edit_role")


async def _write_role_value(
    interaction: discord.Interaction,
    subsystem: str,
    setting_name: str,
    new_value: str,
    parent_message: discord.Message | None,
) -> None:
    """Shared write path for select + clear callbacks."""
    from services.settings_mutation import (
        SettingsMutationError,
        SettingsMutationPipeline,
    )

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "❌ Edit requires a guild context.",
            ephemeral=True,
        )
        return
    try:
        result = await SettingsMutationPipeline().set_value(
            guild,
            subsystem,
            setting_name,
            new_value,
            interaction.user,
        )
    except SettingsMutationError as exc:
        await interaction.response.send_message(
            f"❌ {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return
    except Exception as exc:  # noqa: BLE001 — defensive
        logger.exception(
            "RoleSettingSelect: pipeline raised for %s.%s",
            subsystem,
            setting_name,
        )
        await interaction.response.send_message(
            f"❌ Unexpected error: {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return

    if new_value:
        await interaction.response.send_message(
            f"✅ Updated `{subsystem}.{setting_name}` = <@&{new_value}> "
            f"(was `{result.old_value!r}`).",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            f"✅ Cleared `{subsystem}.{setting_name}` (was `{result.old_value!r}`).",
            ephemeral=True,
        )
    await _refresh_parent(interaction, subsystem, parent_message)


class _RolePickSelect(discord.ui.RoleSelect):
    """Native role select."""

    def __init__(
        self,
        subsystem: str,
        setting_name: str,
        parent_message: discord.Message | None,
    ) -> None:
        super().__init__(
            placeholder="Pick a role…",
            min_values=1,
            max_values=1,
            row=0,
        )
        self.subsystem = subsystem
        self.setting_name = setting_name
        self.parent_message = parent_message

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        await _write_role_value(
            interaction,
            self.subsystem,
            self.setting_name,
            str(picked.id),
            self.parent_message,
        )


class _ClearRoleButton(discord.ui.Button):
    """Clear the role binding by writing the empty string."""

    def __init__(
        self,
        subsystem: str,
        setting_name: str,
        parent_message: discord.Message | None,
    ) -> None:
        super().__init__(
            label="Clear",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        self.subsystem = subsystem
        self.setting_name = setting_name
        self.parent_message = parent_message

    async def callback(self, interaction: discord.Interaction) -> None:
        await _write_role_value(
            interaction,
            self.subsystem,
            self.setting_name,
            "",
            self.parent_message,
        )


# Extends discord.ui.View directly (not BaseView): specialized lifecycle —
# an ephemeral, pipeline-gated follow-up posted only after the parent panel
# already authorized the actor, so it needs neither BaseView's invoker
# interaction_check nor its on_timeout message-edit (the ephemeral message
# is auto-dismissed by Discord).
class RoleSettingSelectView(discord.ui.View):
    """Ephemeral follow-up view hosting the role select + clear button."""

    def __init__(
        self,
        subsystem: str,
        setting_name: str,
        parent_message: discord.Message | None = None,
    ) -> None:
        super().__init__(timeout=180)
        self.add_item(_RolePickSelect(subsystem, setting_name, parent_message))
        self.add_item(_ClearRoleButton(subsystem, setting_name, parent_message))


async def _refresh_parent(
    interaction: discord.Interaction,
    subsystem: str,
    parent_message: discord.Message | None,
) -> None:
    if parent_message is None:
        return
    try:
        from views.settings.subsystem_view import build_subsystem_embed

        embed = await build_subsystem_embed(interaction, subsystem)
        await parent_message.edit(embed=embed)
    except Exception as exc:  # noqa: BLE001 — soft-fail
        logger.debug(
            "RoleSettingSelect: parent-message refresh failed: %s",
            exc,
        )


__all__ = ["RoleSettingSelectView"]
