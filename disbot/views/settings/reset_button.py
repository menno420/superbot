"""ResetSettingButton — S6 reset widget for any scalar SettingSpec.

A reset is functionally ``set_value(spec.default)`` but is recorded
as a deliberate operator action.  The audit row shows the
prev/new values regardless; a future mutation_type extension may
distinguish ``reset_value`` from ``set_value`` so dashboards can
filter.

Allowlisted in ``tests/unit/invariants/test_settings_cog_read_only.py``.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.views.settings.reset_button")


async def reset_setting(
    interaction: discord.Interaction,
    subsystem: str,
    setting_name: str,
    parent_message: discord.Message | None = None,
) -> None:
    """Reset ``(subsystem, setting_name)`` to its declared default.

    Sends an ephemeral confirmation on success and best-effort
    refreshes the parent subsystem-view embed.
    """
    from core.runtime.subsystem_schema import get_schema
    from services.settings_mutation import (
        SettingsMutationError,
        SettingsMutationPipeline,
    )

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "❌ Reset requires a guild context.",
            ephemeral=True,
        )
        return

    schema = get_schema(subsystem)
    spec = None
    if schema is not None:
        for s in schema.settings:
            if s.name == setting_name:
                spec = s
                break
    if spec is None:
        await interaction.response.send_message(
            f"❌ Unknown setting `{subsystem}.{setting_name}`.",
            ephemeral=True,
        )
        return

    try:
        result = await SettingsMutationPipeline().set_value(
            guild,
            subsystem,
            setting_name,
            spec.default,
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
            "ResetSettingButton: pipeline raised for %s.%s",
            subsystem,
            setting_name,
        )
        await interaction.response.send_message(
            f"❌ Unexpected error: {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"✅ Reset `{subsystem}.{setting_name}` to default = `{result.new_value!r}`.",
        ephemeral=True,
    )
    await _refresh_parent(interaction, subsystem, parent_message)


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
        logger.debug("ResetSettingButton: parent-message refresh failed: %s", exc)


__all__ = ["reset_setting"]
