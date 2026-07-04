"""Scope select + preset picker hand-off (PR-C).

After the operator clicks Channel / Category from
:class:`views.ai.behavior.chooser.BehaviorChooserView`, the matching
select view here surfaces a native discord channel/category select.
On submit, the chosen target is handed to
:class:`views.ai.behavior.preset_picker.PresetPickerView`.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

logger = logging.getLogger("bot.views.ai.behavior.scope_picker")

_TIMEOUT_SECONDS = 180


def _admin(user: Any) -> bool:
    # Canonical admin gate — honours the platform owner (config.BOT_OWNER_USER_ID).
    from views.base import member_is_admin

    return member_is_admin(user)


# ---------------------------------------------------------------------------
# Channel
# ---------------------------------------------------------------------------


class _BehaviorChannelSelect(discord.ui.ChannelSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a channel…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        picked: Any = self.values[0]
        if interaction.guild is not None:
            from core.runtime import guild_resources

            full = guild_resources.resolve_channel(
                interaction.guild,
                channel_id=picked.id,
                kind="text",
            )
            if full is not None:
                picked = full

        from views.ai.behavior.preset_picker import (
            PresetPickerView,
            build_preset_picker_embed,
        )

        view = PresetPickerView(
            scope="channel",
            target_id=picked.id,
            target_label=getattr(picked, "mention", f"<#{picked.id}>"),
        )
        await interaction.response.send_message(
            embed=await build_preset_picker_embed(
                scope_label=f"channel {picked.mention}",
            ),
            view=view,
            ephemeral=True,
        )


class BehaviorChannelSelectView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=_TIMEOUT_SECONDS)
        self.add_item(_BehaviorChannelSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not _admin(interaction.user):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return False
        return True


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------


class _BehaviorCategorySelect(discord.ui.ChannelSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a category…",
            channel_types=[discord.ChannelType.category],
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        picked: Any = self.values[0]
        # Categories don't have ``.mention``; show name.
        label = getattr(picked, "name", str(picked.id))

        from views.ai.behavior.preset_picker import (
            PresetPickerView,
            build_preset_picker_embed,
        )

        view = PresetPickerView(
            scope="category",
            target_id=picked.id,
            target_label=label,
        )
        await interaction.response.send_message(
            embed=await build_preset_picker_embed(scope_label=f"category **{label}**"),
            view=view,
            ephemeral=True,
        )


class BehaviorCategorySelectView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=_TIMEOUT_SECONDS)
        self.add_item(_BehaviorCategorySelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not _admin(interaction.user):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return False
        return True


__all__ = ["BehaviorCategorySelectView", "BehaviorChannelSelectView"]
