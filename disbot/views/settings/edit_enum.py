"""Enum-setting edit widget for ``str`` settings with ``allowed_values``.

Discord modals can only host text inputs (no Select component), so
the enum widget is a follow-up *view* with a single Select.  The
flow is:

  1. Operator picks a setting in the SubsystemSettingsView's edit
     dropdown.
  2. The dispatcher sees ``SettingSpec.allowed_values`` is non-empty
     and replies with an ephemeral message hosting the view built by
     :func:`build_enum_select_view`.
  3. Operator picks the new value from the enum select.
  4. The select's callback writes via
     :class:`services.settings_mutation.SettingsMutationPipeline`
     and confirms ephemerally.

The view is the shared :class:`views.paginated_select.PaginatedSelectView`
(``BaseView``-based, windowed): an enum with more than 25 allowed values is
paginated instead of front-truncated at Discord's 25-option cap (the #1040
silent-drop class flagged by ``scripts/check_consistency.py``).

Allowlisted in ``tests/unit/invariants/test_settings_cog_read_only.py``.
"""

from __future__ import annotations

import logging

import discord

from views.paginated_select import PaginatedSelectView

logger = logging.getLogger("bot.views.settings.edit_enum")


def build_enum_select_view(
    author: discord.Member | discord.User,
    subsystem: str,
    setting_name: str,
    allowed_values: tuple,
    current_value,
    parent_message: discord.Message | None = None,
) -> PaginatedSelectView:
    """Build the windowed enum-select view for one ``allowed_values`` setting.

    The select lists every allowed value (paginated when it exceeds 25); the
    current value is pre-marked.  Picking a value writes through the audited
    settings mutation pipeline and refreshes the parent panel.
    """
    options: list[discord.SelectOption] = []
    for value in allowed_values:
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

    async def _on_select(
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        new_value = values[0]
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
                "EnumSettingSelect: pipeline raised for %s.%s",
                subsystem,
                setting_name,
            )
            await interaction.response.send_message(
                f"❌ Unexpected error: {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ Updated `{subsystem}.{setting_name}` = `{result.new_value!r}`.",
            ephemeral=True,
        )
        await _refresh_parent(interaction, subsystem, parent_message)

    return PaginatedSelectView(
        author,
        options,
        _on_select,
        placeholder=f"Pick a new value for {setting_name}…",
        min_values=1,
        max_values=1,
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


__all__ = ["build_enum_select_view"]
