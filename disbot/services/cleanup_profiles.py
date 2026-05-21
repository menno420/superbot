"""Named cleanup profiles.

A *profile* is a curated bundle of cleanup-policy operations
(:class:`services.setup_operations.SetupOperation` of kind
``set_cleanup_policy``) for one named intent. Where
:mod:`services.cleanup_levels` provides the four atomic levels
(Off / Light / Standard / Strict), profiles stack scoped overrides
on top of a guild-wide default to express compound rules like
"Strict everywhere I expect command spam, Off everywhere
moderators need their context preserved".

PR 7 will surface these profiles as a section-card button row /
batch picker. For now this module is a pure catalogue with builder
functions — sections / tests can call ``apply_profile(slug, guild)``
to materialise the op list.

Builders are deterministic and side-effect-free: same guild + same
channel set → same op order. They never call Discord write APIs
themselves; ops are staged through
:func:`services.setup_draft.append` by the caller.

Channel detection re-uses :func:`views.setup.scan_panel.classify_channel_name`
which is already the canonical name-heuristic surface for the
wizard. Adding new patterns there is the right place to broaden
detection — profiles inherit the improvement automatically.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import discord

from services.cleanup_levels import known_level_names
from services.setup_operations import SetupOperation
from views.setup.scan_panel import classify_channel_name

ProfileBuilder = Callable[[discord.Guild], list[SetupOperation]]


@dataclass(frozen=True)
class CleanupProfile:
    """One named cleanup bundle."""

    slug: str
    display_name: str
    description: str
    builder: ProfileBuilder

    def to_operations(self, guild: discord.Guild) -> list[SetupOperation]:
        return self.builder(guild)


def _guild_policy(guild: discord.Guild, level: str) -> SetupOperation:
    """Stage a ``set_cleanup_policy`` op at guild scope."""
    return SetupOperation(
        kind="set_cleanup_policy",
        subsystem="cleanup",
        target_id=guild.id,
        target_name=guild.name,
        target_kind="guild",
        value=level,
    )


def _channel_policy(channel: discord.TextChannel, level: str) -> SetupOperation:
    """Stage a ``set_cleanup_policy`` op at channel scope."""
    return SetupOperation(
        kind="set_cleanup_policy",
        subsystem="cleanup",
        target_id=channel.id,
        target_name=channel.name,
        target_kind="channel",
        value=level,
    )


def _is_bot_channel(channel: discord.TextChannel) -> bool:
    return "likely_bot_cmd" in classify_channel_name(channel.name or "")


def _is_moderation_channel(channel: discord.TextChannel) -> bool:
    tags = classify_channel_name(channel.name or "")
    return bool(
        {"likely_mod", "likely_admin", "likely_mod_log"} & set(tags),
    )


def _build_uniform(level: str) -> ProfileBuilder:
    """Builder that sets one cleanup level at guild scope only."""
    if level not in known_level_names():
        raise ValueError(f"unknown cleanup level {level!r}")

    def _builder(guild: discord.Guild) -> list[SetupOperation]:
        return [_guild_policy(guild, level)]

    return _builder


def _build_silent_bot(guild: discord.Guild) -> list[SetupOperation]:
    """Strict cleanup on detected bot channels; Light elsewhere.

    Falls back to guild-only Light when no bot channels are detected,
    so the profile remains useful on servers without obvious naming
    conventions.
    """
    ops: list[SetupOperation] = [_guild_policy(guild, "Light")]
    for channel in guild.text_channels:
        if _is_bot_channel(channel):
            ops.append(_channel_policy(channel, "Strict"))
    return ops


def _build_moderation_safe(guild: discord.Guild) -> list[SetupOperation]:
    """Standard everywhere except detected moderation channels (Off).

    Mod / admin / staff channels keep their context (no aggressive
    deletion). Everywhere else gets Standard cleanup.
    """
    ops: list[SetupOperation] = [_guild_policy(guild, "Standard")]
    for channel in guild.text_channels:
        if _is_moderation_channel(channel):
            ops.append(_channel_policy(channel, "Off"))
    return ops


PROFILES: dict[str, CleanupProfile] = {
    "off": CleanupProfile(
        slug="off",
        display_name="Off",
        description="Disable cleanup everywhere. The server keeps every command prompt.",
        builder=_build_uniform("Off"),
    ),
    "light": CleanupProfile(
        slug="light",
        display_name="Light",
        description="Delete invalid command prompts after 10s. Failed commands stay.",
        builder=_build_uniform("Light"),
    ),
    "standard": CleanupProfile(
        slug="standard",
        display_name="Standard",
        description="Delete invalid and failed command prompts after 5s.",
        builder=_build_uniform("Standard"),
    ),
    "strict": CleanupProfile(
        slug="strict",
        display_name="Strict",
        description="Aggressively delete invalid and failed prompts after 2s.",
        builder=_build_uniform("Strict"),
    ),
    "silent_bot": CleanupProfile(
        slug="silent_bot",
        display_name="Silent bot channel",
        description=(
            "Strict cleanup on detected bot/command channels, Light "
            "everywhere else. Keeps command spam out of bot channels "
            "without hiding evidence elsewhere."
        ),
        builder=_build_silent_bot,
    ),
    "moderation_safe": CleanupProfile(
        slug="moderation_safe",
        display_name="Moderation safe",
        description=(
            "Standard cleanup everywhere, but Off on detected mod / "
            "admin / staff channels so moderation context and evidence "
            "are preserved."
        ),
        builder=_build_moderation_safe,
    ),
}


def known_profile_slugs() -> frozenset[str]:
    return frozenset(PROFILES.keys())


def get_profile(slug: str) -> CleanupProfile | None:
    return PROFILES.get(slug)


def apply_profile(slug: str, guild: discord.Guild) -> list[SetupOperation]:
    """Return the op list for ``slug``; raises ``KeyError`` on unknown."""
    profile = PROFILES.get(slug)
    if profile is None:
        raise KeyError(f"unknown cleanup profile slug {slug!r}")
    return profile.to_operations(guild)


__all__ = [
    "PROFILES",
    "CleanupProfile",
    "ProfileBuilder",
    "apply_profile",
    "get_profile",
    "known_profile_slugs",
]
