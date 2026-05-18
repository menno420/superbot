"""EnumSettingSelectView — S6 edit widget for ``str`` settings with
``allowed_values``.

Discord modals can only host text inputs (no Select component), so
the enum widget is a follow-up *view* with a single Select.  The
flow is:

  1. Operator picks a setting in the SubsystemSettingsView's edit
     dropdown.
  2. The dispatcher sees ``SettingSpec.allowed_values`` is non-empty
     and replies with an ephemeral message that hosts an
     :class:`EnumSettingSelectView`.
  3. Operator picks the new value from the enum select.
  4. The select's callback writes via
     :class:`services.settings_mutation.SettingsMutationPipeline`
     and confirms ephemerally.

Allowlisted by the S5/S6 read-only invariant scan.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.views.settings.edit_enum")


class _EnumSelect(discord.ui.Select):
    def __init__(
        self,
        subsystem: str,
        setting_name: str,
        allowed_values: tuple,
        current_value,
        parent_message: discord.Message | None,
    ) -> None:
        self.subsystem = subsystem
        self.setting_name = setting_name
        self.parent_message = parent_message
        # Discord caps a Select at 25 options.
        options: list[discord.SelectOption] = []
        for value in allowed_values[:25]:
            label = str(value)[:100]
            is_current = value == current_value
            options.append(
                discord.SelectOption(
                    label=label,
                    value=label,
                    default=is_current,
                    description="current" if is_current else None,
                ),
            )
        super().__init__(
            placeholder=f"Pick a new value for {setting_name}…"[:150],
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        new_value = self.values[0]
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
                self.subsystem,
                self.setting_name,
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
                "EnumSettingSelect: pipeline raised for %s.%s",
                self.subsystem,
                self.setting_name,
            )
            await interaction.response.send_message(
                f"❌ Unexpected error: {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ Updated `{self.subsystem}.{self.setting_name}` "
            f"= `{result.new_value!r}`.",
            ephemeral=True,
        )
        await _refresh_parent(interaction, self.subsystem, self.parent_message)


class EnumSettingSelectView(discord.ui.View):
    """Ephemeral follow-up view hosting the enum-select widget."""

    def __init__(
        self,
        subsystem: str,
        setting_name: str,
        allowed_values: tuple,
        current_value,
        parent_message: discord.Message | None = None,
    ) -> None:
        super().__init__(timeout=180)
        self.add_item(
            _EnumSelect(
                subsystem,
                setting_name,
                allowed_values,
                current_value,
                parent_message,
            ),
        )


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
    except Exception as exc:  # noqa: BLE001
        logger.debug("EnumSettingSelect: parent-message refresh failed: %s", exc)


__all__ = ["EnumSettingSelectView"]
