"""NumericPresetsView — S7 edit widget for int/float settings with presets.

Dispatched when a ``SettingSpec`` declares
``input_hint="numeric_presets"``.  The spec's ``presets`` tuple lists
suggested values; the widget renders one button per preset plus an
"Override…" button that opens the existing free-form modal so the
operator can still type a custom value.

Mirrors the channel/role widgets' write path — each preset button
calls :class:`services.settings_mutation.SettingsMutationPipeline`
with the preset value, then reports success/failure ephemerally.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.views.settings.edit_number_presets")


async def _write_preset_value(
    interaction: discord.Interaction,
    subsystem: str,
    setting_name: str,
    value: object,
    parent_message: discord.Message | None,
) -> None:
    """Shared write path for every preset button."""
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
            value,
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
            "NumericPresets: pipeline raised for %s.%s",
            subsystem,
            setting_name,
        )
        await interaction.response.send_message(
            f"❌ Unexpected error: {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"✅ Updated `{subsystem}.{setting_name}` = `{result.new_value!r}` "
        f"(was `{result.old_value!r}`).",
        ephemeral=True,
    )
    await _refresh_parent(interaction, subsystem, parent_message)


class _PresetButton(discord.ui.Button):
    """One button per preset value."""

    def __init__(
        self,
        subsystem: str,
        setting_name: str,
        value: object,
        parent_message: discord.Message | None,
        is_current: bool,
        row: int,
    ) -> None:
        # Discord button labels are bounded; coerce + truncate.
        label = str(value)[:80] or "(unset)"
        super().__init__(
            label=label,
            # Highlight the current value in primary; rest stay secondary.
            style=(
                discord.ButtonStyle.primary
                if is_current
                else discord.ButtonStyle.secondary
            ),
            row=row,
        )
        self.subsystem = subsystem
        self.setting_name = setting_name
        self.value = value
        self.parent_message = parent_message

    async def callback(self, interaction: discord.Interaction) -> None:
        await _write_preset_value(
            interaction,
            self.subsystem,
            self.setting_name,
            self.value,
            self.parent_message,
        )


class _OverrideButton(discord.ui.Button):
    """Opens the free-form ``NumberSettingModal`` for a custom value."""

    def __init__(
        self,
        subsystem: str,
        setting_name: str,
        value_type: type,
        current_value: object,
        default_value: object,
        parent_message: discord.Message | None,
        row: int,
    ) -> None:
        super().__init__(
            label="Override…",
            style=discord.ButtonStyle.grey,
            row=row,
        )
        self.subsystem = subsystem
        self.setting_name = setting_name
        self.value_type = value_type
        self.current_value = current_value
        self.default_value = default_value
        self.parent_message = parent_message

    async def callback(self, interaction: discord.Interaction) -> None:
        # Reuse the existing free-form numeric modal.
        from views.settings.edit_number import NumberSettingModal

        modal = NumberSettingModal(
            self.subsystem,
            self.setting_name,
            self.value_type,
            self.current_value,
            self.default_value,
            self.parent_message,
        )
        await interaction.response.send_modal(modal)


# Extends discord.ui.View directly (not BaseView): specialized lifecycle —
# an ephemeral, pipeline-gated follow-up posted only after the parent panel
# already authorized the actor, so it needs neither BaseView's invoker
# interaction_check nor its on_timeout message-edit (the ephemeral message
# is auto-dismissed by Discord).
class NumericPresetsView(discord.ui.View):
    """Ephemeral follow-up view: preset buttons + override.

    Presets render two-per-row up to four rows (Discord's component
    limit is 5 rows of 5 buttons, and the override button takes one
    slot).  When the spec declares more presets than fit, the surplus
    is dropped with a WARNING — the override button is always
    available so no value is unreachable.
    """

    _MAX_PRESET_BUTTONS = 19  # 4 rows × 5 = 20 buttons; reserve one for override
    _BUTTONS_PER_ROW = 5

    def __init__(
        self,
        subsystem: str,
        setting_name: str,
        value_type: type,
        current_value: object,
        default_value: object,
        presets: tuple,
        parent_message: discord.Message | None = None,
    ) -> None:
        super().__init__(timeout=180)
        bounded = list(presets)
        if len(bounded) > self._MAX_PRESET_BUTTONS:
            logger.warning(
                "NumericPresets: %s.%s declares %d presets — only the "
                "first %d render; remaining values reachable via Override.",
                subsystem,
                setting_name,
                len(bounded),
                self._MAX_PRESET_BUTTONS,
            )
            bounded = bounded[: self._MAX_PRESET_BUTTONS]
        for idx, preset in enumerate(bounded):
            self.add_item(
                _PresetButton(
                    subsystem=subsystem,
                    setting_name=setting_name,
                    value=preset,
                    parent_message=parent_message,
                    is_current=preset == current_value,
                    row=idx // self._BUTTONS_PER_ROW,
                ),
            )
        # Override sits below the preset rows.
        override_row = (len(bounded) - 1) // self._BUTTONS_PER_ROW + 1 if bounded else 0
        # Cap at row 4 — Discord's last row.
        override_row = min(override_row, 4)
        self.add_item(
            _OverrideButton(
                subsystem=subsystem,
                setting_name=setting_name,
                value_type=value_type,
                current_value=current_value,
                default_value=default_value,
                parent_message=parent_message,
                row=override_row,
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
    except Exception as exc:  # noqa: BLE001 — soft-fail
        logger.debug(
            "NumericPresets: parent-message refresh failed: %s",
            exc,
        )


__all__ = ["NumericPresetsView"]
