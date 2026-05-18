"""Shared resource-lookup helpers for selector / panel code.

Hosts the generic channel + role primitives that several panel cogs
share. Phase 0 of the platform roadmap pulled these out of
``views/channels/_helpers.py`` and ``views/roles/_helpers.py`` so they
can be consumed independently of either subsystem's panel module —
preparing the ground for Phase 2c's ``core/resources/`` runtime, which
will absorb them as the canonical resource discovery surface.

Underscore-prefixed because these are internal to the selector layer —
production code should depend on the public ``views.selectors`` re-exports
(or, after Phase 2c, on ``core.resources.discovery``).
"""

from __future__ import annotations

import discord

from utils.helpers import normalize_name, safe_select_emoji


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


def _find_role_normalized(
    guild: discord.Guild,
    name: str,
) -> discord.Role | None:
    """Case-insensitive, space-insensitive role lookup."""
    key = normalize_name(name)
    return discord.utils.find(lambda r: normalize_name(r.name) == key, guild.roles)
