"""TextSettingModal — S6 edit widget for free-form ``str`` SettingSpecs.

Used for string settings whose ``SettingSpec.allowed_values`` is
empty.  Settings that declare ``allowed_values`` are routed to the
:mod:`views.settings.edit_enum` widget instead.

Allowlisted in ``tests/unit/invariants/test_settings_cog_read_only.py``.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.views.settings.edit_text")


class TextSettingModal(discord.ui.Modal):
    """Free-form text input for ``str`` settings without ``allowed_values``."""

    def __init__(
        self,
        subsystem: str,
        setting_name: str,
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
        self.parent_message = parent_message
        # Multi-line text supports longer values (templates, hint strings).
        self.input: discord.ui.TextInput = discord.ui.TextInput(
            label="New value (text)",
            placeholder=(f"current={current_value!r} · default={default_value!r}")[
                :100
            ],
            default=str(current_value) if current_value else "",
            required=False,
            max_length=2000,
            style=discord.TextStyle.paragraph,
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw = self.input.value
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
                raw,
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
                "TextSettingModal: pipeline raised for %s.%s",
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
        logger.debug("TextSettingModal: parent-message refresh failed: %s", exc)


__all__ = ["TextSettingModal"]
