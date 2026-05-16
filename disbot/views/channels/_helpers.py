"""Shared helpers for the channel-management panel views.

Hosts the name/category presets, the cross-panel ``_ChannelSelect``
widget (used by both delete and restrict flows), and the
``_build_channel_options`` factory.

Kept underscore-prefixed because these are implementation details of
the channel subsystem — production code should depend on the public
``views.channels`` re-exports instead.
"""

from __future__ import annotations

import discord

from utils.helpers import safe_select_emoji

# Keyword presets shown in the dropdown menus
_NAME_PRESETS = [
    "general",
    "gaming",
    "announcements",
    "events",
    "tournament",
    "support",
    "bot-commands",
    "vc-lounge",
]
_CATEGORY_PRESETS = [
    "Gaming",
    "Community",
    "Events",
    "Tournaments",
    "Staff",
]


def _build_channel_options(guild: discord.Guild) -> list[discord.SelectOption]:
    """Return up to 25 SelectOptions for all text + voice channels, sorted by name."""
    channels = sorted(
        [
            ch
            for ch in guild.channels
            if isinstance(ch, (discord.TextChannel, discord.VoiceChannel))
        ],
        key=lambda c: c.name,
    )
    options = []
    for ch in channels[:25]:
        emoji = safe_select_emoji(
            "🔊" if isinstance(ch, discord.VoiceChannel) else "💬",
        )
        cat_label = ch.category.name if ch.category else "No category"
        options.append(
            discord.SelectOption(
                label=ch.name[:100],
                value=str(ch.id),
                description=f"{cat_label}"[:100],
                emoji=emoji,
            ),
        )
    return options


class _ChannelSelect(discord.ui.Select):
    """Generic channel select used by Delete and Restrict sub-panels.

    The parent view must define ``selected_channel_id`` and
    ``selected_channel_name`` attributes plus a ``build_embed()``
    method — the callback writes both fields and refreshes the
    embed.
    """

    def __init__(
        self,
        options: list[discord.SelectOption],
        parent_view,
        *,
        placeholder: str,
    ):
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )
        self._parent = parent_view

    async def callback(self, interaction: discord.Interaction):
        self._parent.selected_channel_id = int(self.values[0])  # type: ignore[attr-defined]
        # Resolve the display name from the options list
        chosen_opt = next((o for o in self.options if o.value == self.values[0]), None)
        self._parent.selected_channel_name = (  # type: ignore[attr-defined]
            chosen_opt.label if chosen_opt else self.values[0]
        )
        try:
            await interaction.response.edit_message(
                embed=self._parent.build_embed(),
                view=self._parent,  # type: ignore[attr-defined, arg-type]
            )
        except discord.HTTPException:
            if not interaction.response.is_done():
                await interaction.response.defer()
