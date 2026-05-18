"""Channel-specific resource operations.

Thin layer on top of :mod:`core.resources.discovery` that adds
channel-specific predicates and selector-friendly conversions.  Phase
2c selectors consume this module instead of inlining channel-iteration
logic.

The bulk of the actual enumeration lives in
:func:`core.resources.discovery.list_channels`; this module's job is
to bundle the *patterns* (filter by type, build SelectOptions, locate
by intent) that several call sites historically duplicated.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

import discord

from core.resources.discovery import (
    channel_to_snapshot,
    list_channels,
    resolve_resource,
    validate_resource,
)
from core.resources.status import ResourceStatus
from core.resources.types import ChannelResource, ResourceKind
from utils.helpers import safe_select_emoji

# Channel-type predicates re-exported for callers that need named filters.
TEXT_TYPES: frozenset[str] = frozenset({"text", "news"})
VOICE_TYPES: frozenset[str] = frozenset({"voice", "stage"})


def list_text_channels(guild: discord.Guild) -> list[ChannelResource]:
    """Return snapshots of every text-like channel in ``guild``."""
    return [ch for ch in list_channels(guild) if ch.channel_type in TEXT_TYPES]


def list_voice_channels(guild: discord.Guild) -> list[ChannelResource]:
    """Return snapshots of every voice-like channel in ``guild``."""
    return [ch for ch in list_channels(guild) if ch.channel_type in VOICE_TYPES]


def filter_channels(
    guild: discord.Guild,
    predicate: Callable[[ChannelResource], bool],
) -> list[ChannelResource]:
    """Enumerate channels matching ``predicate``.

    Equivalent to a comprehension over :func:`list_channels`, but the
    named helper keeps call sites idiomatic.
    """
    return [ch for ch in list_channels(guild) if predicate(ch)]


def get_channel(
    guild: discord.Guild,
    channel_id: int,
) -> ChannelResource | None:
    """Look up a single channel by ID, returning a snapshot."""
    resource = resolve_resource(guild, ResourceKind.CHANNEL, channel_id)
    if isinstance(resource, ChannelResource):
        return resource
    return None


async def status_for(
    guild: discord.Guild,
    channel_id: int,
    *,
    persist: bool = True,
) -> ResourceStatus:
    """Validate a single channel and return its current status."""
    return await validate_resource(
        guild,
        ResourceKind.CHANNEL,
        channel_id,
        persist=persist,
    )


# ---------------------------------------------------------------------------
# Selector helpers — absorbed from views/selectors/_resource_helpers
# ---------------------------------------------------------------------------


def build_select_options(
    guild: discord.Guild,
    *,
    include_voice: bool = True,
    limit: int = 25,
) -> list[discord.SelectOption]:
    """Build up to ``limit`` :class:`discord.SelectOption` items, name-sorted.

    Replacement for the legacy ``_build_channel_options`` helper.  By
    default both text and voice channels are included (matching the
    legacy behavior); pass ``include_voice=False`` for text-only
    pickers.
    """
    channels: Iterable[discord.abc.GuildChannel] = (
        ch
        for ch in guild.channels
        if isinstance(ch, discord.TextChannel)
        or (include_voice and isinstance(ch, discord.VoiceChannel))
    )
    sorted_channels = sorted(channels, key=lambda c: c.name)
    options: list[discord.SelectOption] = []
    for ch in sorted_channels[:limit]:
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


__all__ = [
    "TEXT_TYPES",
    "VOICE_TYPES",
    "build_select_options",
    "channel_to_snapshot",
    "filter_channels",
    "get_channel",
    "list_channels",
    "list_text_channels",
    "list_voice_channels",
    "status_for",
]
