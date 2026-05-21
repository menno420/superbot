"""NumberSettingModal — S6 edit widget for ``int`` / ``float`` SettingSpecs.

Pops a one-input :class:`discord.ui.Modal` so the operator types a
new value.  ``on_submit`` coerces the input, runs the spec's
validator (via the pipeline), writes through
:class:`services.settings_mutation.SettingsMutationPipeline`, and
sends an ephemeral confirmation.

Allowlisted in ``tests/unit/invariants/test_settings_cog_read_only.py``.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.views.settings.edit_number")


class NumberSettingModal(discord.ui.Modal):
    """Free-form numeric input for ``int`` / ``float`` settings."""

    def __init__(
        self,
        subsystem: str,
        setting_name: str,
        value_type: type,
        current_value,
        default_value,
        parent_message: discord.Message | None = None,
    ) -> None:
        super().__init__(
            title=f"Edit {subsystem}.{setting_name}"[:45],
            timeout=180,
        )
        self.subsystem = subsystem
        self.setting_name = setting_name
        self.value_type = value_type
        self.parent_message = parent_message
        self.input: discord.ui.TextInput = discord.ui.TextInput(
            label=f"New value (type: {value_type.__name__})"[:45],
            placeholder=(f"current={current_value!r} · default={default_value!r}")[
                :100
            ],
            default=str(current_value) if current_value is not None else "",
            required=True,
            max_length=64,
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw = self.input.value.strip()
        from services.settings_mutation import (
            SettingsCoercionError,
            SettingsMutationError,
            SettingsMutationPipeline,
            SettingsValidationError,
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
                raw,
                interaction.user,
            )
        except (SettingsCoercionError, SettingsValidationError) as exc:
            await interaction.response.send_message(
                f"❌ {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return
        except SettingsMutationError as exc:
            await interaction.response.send_message(
                f"❌ {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.exception(
                "NumberSettingModal: pipeline raised for %s.%s",
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
            f"= `{result.new_value!r}` (was `{result.old_value!r}`).",
            ephemeral=True,
        )
        await _refresh_parent(interaction, self.subsystem, self.parent_message)


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
            "NumberSettingModal: parent-message refresh failed: %s",
            exc,
        )


__all__ = ["NumberSettingModal"]
