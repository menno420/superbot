"""Reusable text-channel picker.

Discord caps Select options at 25.  Callers pass any-length channel
iterable and the selector truncates with a documented footer.  When
adoption demands paging, an embedded page-cursor selector is the
right extension (Phase D follow-up).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import Any

import discord

# Async callback signature: (interaction, selected_channel_id) -> None.
OnSelect = Callable[[discord.Interaction, int], Awaitable[None]]


class ChannelSelector(discord.ui.Select):
    """Select widget listing up to 25 text channels.

    Parameters
    ----------
    channels:
        Any iterable of ``discord.TextChannel``.  Truncated to 25
        entries (Discord's hard cap on Select options).
    on_select:
        Awaitable invoked with ``(interaction, channel_id)`` once the
        user picks.  Default-emits nothing; the caller must reply or
        defer.
    placeholder:
        Optional placeholder string.  Defaults to "Select a channel…".
    custom_id:
        Optional ``custom_id``.  Defaults to a non-persistent value;
        for persistent panels pass an explicit ``<subsystem>:<action>``
        string.
    """

    def __init__(
        self,
        channels: Iterable[discord.TextChannel],
        on_select: OnSelect,
        *,
        placeholder: str = "Select a channel…",
        custom_id: str | None = None,
        row: int | None = None,
    ) -> None:
        bounded = list(channels)[:25]
        options = [
            discord.SelectOption(label=f"#{ch.name}"[:100], value=str(ch.id))
            for ch in bounded
        ]
        # dict[str, Any] (not object) so **kwargs unpacks into Select.__init__
        # without mypy demanding str|int|list|bool per declared param.
        kwargs: dict[str, Any] = {
            "placeholder": placeholder,
            "options": options,
            "min_values": 1,
            "max_values": 1,
        }
        if custom_id is not None:
            kwargs["custom_id"] = custom_id
        if row is not None:
            kwargs["row"] = row
        super().__init__(**kwargs)
        self._on_select = on_select

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            channel_id = int(self.values[0])
        except (IndexError, ValueError):
            await interaction.response.send_message(
                "Invalid selection.",
                ephemeral=True,
            )
            return
        await self._on_select(interaction, channel_id)
