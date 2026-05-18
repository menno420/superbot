"""BooleanSettingToggle — S6 edit widget for ``bool`` SettingSpecs.

Single-click toggle that reads the current value via S3's resolver
and writes the inverted value via S4's
:class:`services.settings_mutation.SettingsMutationPipeline`.

Lives under the S5 read-only-invariant allowlist: this is one of
the five edit-flow files permitted to import the mutation pipeline.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.views.settings.edit_boolean")


async def toggle_setting(
    interaction: discord.Interaction,
    subsystem: str,
    setting_name: str,
    parent_message: discord.Message | None = None,
) -> None:
    """Read the current value and write the inverted value.

    Sends an ephemeral confirmation on success and best-effort
    refreshes the parent subsystem-view embed.  Errors from the
    mutation pipeline are reported ephemerally.
    """
    from services.settings_mutation import (
        SettingsMutationError,
        SettingsMutationPipeline,
    )
    from services.settings_resolution import resolve_setting

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "❌ Toggle requires a guild context.",
            ephemeral=True,
        )
        return

    resolution = await resolve_setting(guild.id, subsystem, setting_name)
    if resolution is None:
        await interaction.response.send_message(
            f"❌ Unknown setting `{subsystem}.{setting_name}`.",
            ephemeral=True,
        )
        return

    new_value = not bool(resolution.value)
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
            f"❌ `{type(exc).__name__}`: {exc}",
            ephemeral=True,
        )
        return
    except Exception as exc:  # noqa: BLE001 — defensive
        logger.exception(
            "BooleanSettingToggle: pipeline raised for %s.%s",
            subsystem,
            setting_name,
        )
        await interaction.response.send_message(
            f"❌ Unexpected error: {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"✅ Toggled `{subsystem}.{setting_name}` → `{result.new_value!r}`.",
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
    except Exception as exc:  # noqa: BLE001 — soft-fail; user already confirmed
        logger.debug(
            "BooleanSettingToggle: parent-message refresh failed: %s",
            exc,
        )


__all__ = ["toggle_setting"]
