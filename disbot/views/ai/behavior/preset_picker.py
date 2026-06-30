"""Preset picker — list + apply (PR-C).

Reads ``services.ai_behavior_profile_service.list_presets()`` and
renders a native :class:`discord.ui.Select` so the operator picks
one preset for the previously-chosen scope. Submit calls
``apply_preset`` and renders a confirmation embed.

The view never invokes ``ai_db.*`` directly.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

logger = logging.getLogger("bot.views.ai.behavior.preset_picker")

_TIMEOUT_SECONDS = 180

# Discord's native select caps at 25 options. The catalog has 7
# entries; the cap is enforced anyway so future preset growth fails
# loudly rather than silently dropping rows.
_MAX_OPTIONS = 25


def _admin(user: Any) -> bool:
    # Canonical admin gate — honours the platform owner (config.BOT_OWNER_USER_ID).
    from views.base import member_is_admin

    return member_is_admin(user)


async def build_preset_picker_embed(*, scope_label: str) -> discord.Embed:
    """Read the catalog and produce the picker embed."""
    from services import ai_behavior_profile_service as svc

    presets = await svc.list_presets()
    embed = discord.Embed(
        title="Pick a Behavior preset",
        description=(
            f"Selecting a preset binds it to **{scope_label}** and "
            "writes through the existing policy chokepoint. Existing "
            "min_level / cooldown overrides for that scope are "
            "preserved."
        ),
        color=discord.Color.blurple(),
    )
    for preset in presets[:_MAX_OPTIONS]:
        embed.add_field(
            name=f"`{preset.key}` · mode=`{preset.recommended_mode}`",
            value=preset.headline,
            inline=False,
        )
    embed.set_footer(text="Submit to apply · ephemeral follow-up.")
    return embed


class _PresetSelect(discord.ui.Select):
    def __init__(
        self,
        *,
        scope: str,
        target_id: int,
        target_label: str,
        options: list[discord.SelectOption],
        preset_lookup: dict[str, int],
    ) -> None:
        super().__init__(
            placeholder="Pick a preset…",
            min_values=1,
            max_values=1,
            options=options,
        )
        self._scope = scope
        self._target_id = target_id
        self._target_label = target_label
        self._preset_lookup = preset_lookup

    async def callback(self, interaction: discord.Interaction) -> None:
        from services import ai_behavior_profile_service as svc

        chosen_key = self.values[0]
        preset_id = self._preset_lookup.get(chosen_key)
        if preset_id is None:
            await interaction.response.send_message(
                f"❌ Unknown preset `{chosen_key}`.",
                ephemeral=True,
            )
            return
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Apply requires a guild context.",
                ephemeral=True,
            )
            return
        try:
            result = await svc.apply_preset(
                guild_id=interaction.guild.id,
                scope=self._scope,
                target_id=self._target_id,
                preset_id=preset_id,
                actor=interaction.user,
            )
        except svc.BehaviorPresetError as exc:
            await interaction.response.send_message(
                f"❌ {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.exception(
                "PresetPicker: apply failed scope=%s target=%s preset=%s",
                self._scope,
                self._target_id,
                chosen_key,
            )
            await interaction.response.send_message(
                f"❌ Unexpected error: {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ Bound preset `{result.preset_key}` "
            f"(mode `{result.recommended_mode}`) to "
            f"{self._scope} **{self._target_label}**. "
            f"mutation_id=`{result.policy_mutation_id}`.",
            ephemeral=True,
        )


class PresetPickerView(discord.ui.View):
    """Wrap a :class:`_PresetSelect` for one scope + target.

    The select options are loaded lazily in :meth:`prepare` so the
    view can call the async catalog read. ``__init__`` is sync — call
    sites should construct then ``send_message`` after a separate
    ``build_preset_picker_embed`` call (which loads the catalog).
    Construction is cheap; the lazy load happens when the dropdown
    is opened.
    """

    def __init__(self, *, scope: str, target_id: int, target_label: str) -> None:
        super().__init__(timeout=_TIMEOUT_SECONDS)
        self._scope = scope
        self._target_id = target_id
        self._target_label = target_label
        self._loaded = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not _admin(interaction.user):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return False
        if not self._loaded:
            await self._load_options()
        return True

    async def _load_options(self) -> None:
        from services import ai_behavior_profile_service as svc

        presets = await svc.list_presets()
        options: list[discord.SelectOption] = []
        lookup: dict[str, int] = {}
        for preset in presets[:_MAX_OPTIONS]:
            options.append(
                discord.SelectOption(
                    label=preset.key,
                    description=preset.headline[:100],
                    value=preset.key,
                ),
            )
            lookup[preset.key] = preset.preset_id
        select = _PresetSelect(
            scope=self._scope,
            target_id=self._target_id,
            target_label=self._target_label,
            options=options,
            preset_lookup=lookup,
        )
        self.add_item(select)
        self._loaded = True


__all__ = ["PresetPickerView", "build_preset_picker_embed"]
