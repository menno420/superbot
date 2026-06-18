"""Reusable text-channel picker.

Discord caps a ``Select`` at 25 options.  :func:`attach_channel_select`
attaches a *windowed* channel picker to a host view — any-length channel
iterable is paginated (◀/▶ nav past 25) instead of front-truncated, so the
tail is never silently dropped (the #1040 class).  It is the embedded sibling
of :class:`views.paginated_select.PaginatedSelectView`, built on
:func:`views.paginated_select.attach_windowed_select`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable

import discord

from views.paginated_select import SelectWindow, attach_windowed_select

# Async callback signature: (interaction, selected_channel_id) -> None.
OnSelect = Callable[[discord.Interaction, int], Awaitable[None]]


def attach_channel_select(
    view: discord.ui.View,
    channels: Iterable[discord.abc.GuildChannel],
    on_select: OnSelect,
    *,
    placeholder: str = "Select a channel…",
    select_row: int | None = None,
    nav_row: int | None = None,
) -> SelectWindow:
    """Attach a windowed single text/voice-channel picker to ``view``.

    Parameters
    ----------
    channels:
        Any iterable of channels; paginated past 25 (never truncated).
    on_select:
        Awaitable invoked with ``(interaction, channel_id)`` once the user
        picks.  The callback must reply to or defer the interaction.
    select_row / nav_row:
        Optional explicit action-rows so an embedding host can fit the select
        and its ◀/▶ nav into its own 5-row budget.
    """
    options = [
        discord.SelectOption(label=f"#{ch.name}"[:100], value=str(ch.id))
        for ch in channels
    ]

    async def _dispatch(interaction: discord.Interaction, values: list[str]) -> None:
        try:
            channel_id = int(values[0])
        except (IndexError, ValueError):
            await interaction.response.send_message(
                "Invalid selection.",
                ephemeral=True,
            )
            return
        await on_select(interaction, channel_id)

    return attach_windowed_select(
        view,
        options,
        _dispatch,
        placeholder=placeholder,
        min_values=1,
        max_values=1,
        select_row=select_row,
        nav_row=nav_row,
    )
