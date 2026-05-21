"""Named cog-routing profiles.

The cog routing section already supports per-scope `set_cog_routing`
ops manually. This module layers named batch profiles on top so the
operator can express "Disable games outside game channels" or
"Disable moderation outside staff channels" with one click — the
profile builder fans out the appropriate enable/disable ops per
detected channel.

A *cog routing profile* is a pure builder that returns a list of
``SetupOperation(kind="set_cog_routing", ...)`` entries. The
existing dispatcher routes each through
``services.command_routing.set_policy`` at Final Review time.

Channel detection re-uses
:func:`views.setup.scan_panel.classify_channel_name` — the same
heuristic that powers cleanup profiles and channel recommendations.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import discord

from services.setup_operations import SetupOperation
from views.setup.scan_panel import classify_channel_name

ProfileBuilder = Callable[[discord.Guild], list[SetupOperation]]


@dataclass(frozen=True)
class CogRoutingProfile:
    """One named routing bundle."""

    slug: str
    display_name: str
    description: str
    builder: ProfileBuilder

    def to_operations(self, guild: discord.Guild) -> list[SetupOperation]:
        return self.builder(guild)


def _routing_op(
    *,
    scope_kind: str,
    scope_id: int | None,
    scope_name: str,
    cog_name: str,
    enabled: bool,
) -> SetupOperation:
    """Build a ``set_cog_routing`` op with the canonical metadata shape."""
    return SetupOperation(
        kind="set_cog_routing",
        subsystem="cog_routing",
        target_id=scope_id,
        target_name=scope_name,
        target_kind=scope_kind,
        value=cog_name,
        metadata={
            "enabled": "true" if enabled else "false",
        },
    )


def _channels_matching(guild: discord.Guild, tag: str) -> list[discord.TextChannel]:
    matches: list[discord.TextChannel] = []
    for channel in guild.text_channels:
        if tag in classify_channel_name(channel.name or ""):
            matches.append(channel)
    return matches


def _build_games_in_game_channels(guild: discord.Guild) -> list[SetupOperation]:
    """Disable the ``games`` cog at guild scope; re-enable it in each
    detected game channel (``likely_game`` tag).
    """
    ops: list[SetupOperation] = [
        _routing_op(
            scope_kind="guild",
            scope_id=guild.id,
            scope_name=guild.name,
            cog_name="games",
            enabled=False,
        ),
    ]
    for channel in _channels_matching(guild, "likely_game"):
        ops.append(
            _routing_op(
                scope_kind="channel",
                scope_id=channel.id,
                scope_name=channel.name,
                cog_name="games",
                enabled=True,
            ),
        )
    return ops


def _build_economy_in_economy_channels(
    guild: discord.Guild,
) -> list[SetupOperation]:
    """Disable the ``economy`` cog at guild scope; re-enable on each
    detected economy / game channel.
    """
    ops: list[SetupOperation] = [
        _routing_op(
            scope_kind="guild",
            scope_id=guild.id,
            scope_name=guild.name,
            cog_name="economy",
            enabled=False,
        ),
    ]
    seen: set[int] = set()
    for tag in ("likely_game", "likely_mining"):
        for channel in _channels_matching(guild, tag):
            if channel.id in seen:
                continue
            seen.add(channel.id)
            ops.append(
                _routing_op(
                    scope_kind="channel",
                    scope_id=channel.id,
                    scope_name=channel.name,
                    cog_name="economy",
                    enabled=True,
                ),
            )
    return ops


def _build_moderation_to_staff(guild: discord.Guild) -> list[SetupOperation]:
    """Disable the ``moderation`` cog at guild scope; re-enable on each
    detected staff / admin / mod channel.
    """
    ops: list[SetupOperation] = [
        _routing_op(
            scope_kind="guild",
            scope_id=guild.id,
            scope_name=guild.name,
            cog_name="moderation",
            enabled=False,
        ),
    ]
    seen: set[int] = set()
    for tag in ("likely_mod", "likely_admin", "likely_mod_log"):
        for channel in _channels_matching(guild, tag):
            if channel.id in seen:
                continue
            seen.add(channel.id)
            ops.append(
                _routing_op(
                    scope_kind="channel",
                    scope_id=channel.id,
                    scope_name=channel.name,
                    cog_name="moderation",
                    enabled=True,
                ),
            )
    return ops


def _build_recommended_by_name(guild: discord.Guild) -> list[SetupOperation]:
    """Compound profile: apply games + economy + moderation routing in one go.

    Stages the union of the three single-cog profiles' op lists.
    Each op is unique on ``(cog_name, scope_kind, scope_id)`` since
    the three builders touch different cog names, so no dedup is
    required across profiles — only the per-channel dedup inside
    each builder applies.
    """
    ops: list[SetupOperation] = []
    ops.extend(_build_games_in_game_channels(guild))
    ops.extend(_build_economy_in_economy_channels(guild))
    ops.extend(_build_moderation_to_staff(guild))
    return ops


PROFILES: dict[str, CogRoutingProfile] = {
    "games_in_game_channels": CogRoutingProfile(
        slug="games_in_game_channels",
        display_name="Games → game channels only",
        description=(
            "Disable the games cog at guild scope and re-enable it on "
            "each detected `likely_game` channel."
        ),
        builder=_build_games_in_game_channels,
    ),
    "economy_in_economy_channels": CogRoutingProfile(
        slug="economy_in_economy_channels",
        display_name="Economy → economy/game channels only",
        description=(
            "Disable the economy cog at guild scope and re-enable on "
            "channels matching the game/mining classifiers."
        ),
        builder=_build_economy_in_economy_channels,
    ),
    "moderation_to_staff": CogRoutingProfile(
        slug="moderation_to_staff",
        display_name="Moderation → staff channels only",
        description=(
            "Disable the moderation cog at guild scope and re-enable "
            "on detected mod / admin / staff channels."
        ),
        builder=_build_moderation_to_staff,
    ),
    "recommended_by_name": CogRoutingProfile(
        slug="recommended_by_name",
        display_name="Recommended (all cogs by channel name)",
        description=(
            "Apply games / economy / moderation routing in one pass — "
            "each cog disabled at guild scope and re-enabled only in "
            "channels whose name matches its intent."
        ),
        builder=_build_recommended_by_name,
    ),
}


def known_profile_slugs() -> frozenset[str]:
    return frozenset(PROFILES.keys())


def get_profile(slug: str) -> CogRoutingProfile | None:
    return PROFILES.get(slug)


def apply_profile(slug: str, guild: discord.Guild) -> list[SetupOperation]:
    """Return the op list for ``slug``; raises ``KeyError`` on unknown."""
    profile = PROFILES.get(slug)
    if profile is None:
        raise KeyError(f"unknown cog routing profile slug {slug!r}")
    return profile.to_operations(guild)


__all__ = [
    "PROFILES",
    "CogRoutingProfile",
    "ProfileBuilder",
    "apply_profile",
    "get_profile",
    "known_profile_slugs",
]
