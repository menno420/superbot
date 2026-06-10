"""Announce a newly-detected BTD6 version to each guild's chosen channel.

Subscribes (once) to ``btd6.version_detected`` — emitted by
:mod:`services.btd6_patch_service` when patch-notes ingestion writes a
version strictly newer than the previously-stored latest — and posts an
embed to every guild that configured an announcement channel
(``BTD6_VERSION_ANNOUNCEMENT_CHANNEL``).

This module also *owns* that setting's read/write (mirroring
:mod:`services.btd6_ct_team_service` for ``BTD6_CT_GROUP_ID``) so no raw
key string leaks into cogs.

Channel source precedence (Settings Phase 2 / Q-0064): the first-class
``btd6.version_announce_channel`` **binding** wins when bound (set through
the canonical binding flow with a native channel selector); the legacy KV
pointer written by ``!btd6ops announcechannel`` is the fallback lane.
Write-path convergence (retiring the KV lane) is settings Phase 3
territory — until then the typed command keeps working and warns when a
binding shadows it.

The subscribe-once + captured-bot pattern mirrors
:mod:`services.server_logging`: ``setup(bot)`` is called from
``BTD6Cog.cog_load`` and is idempotent across cog reloads, so a reload can
never double-register the handler (and thus never double-post).
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from core.events import bus
from services.btd6_patch_service import EVT_BTD6_VERSION_DETECTED
from utils import db
from utils.btd6.context_footer import append_context_footer
from utils.settings_keys import BTD6_VERSION_ANNOUNCEMENT_CHANNEL

logger = logging.getLogger("bot.services.btd6_version_announce")

_BOT: Any = None
_SUBSCRIBED = False


# ---------------------------------------------------------------------------
# Setting read/write (this module owns BTD6_VERSION_ANNOUNCEMENT_CHANNEL)
# ---------------------------------------------------------------------------


async def binding_channel_id(guild_id: int) -> int | None:
    """The ``btd6.version_announce_channel`` binding target, or ``None``.

    Settings Phase 2 (Q-0064): a bound channel takes precedence over the
    legacy KV pointer. Read failures degrade to ``None`` (the KV lane
    keeps working) — one guild's bad binding row must not kill
    announcements platform-wide.
    """
    from core.runtime.bindings import get_binding

    try:
        value = await get_binding(guild_id, "btd6", "version_announce_channel")
    except Exception:  # noqa: BLE001 — degrade to the legacy KV lane
        logger.warning(
            "btd6 announce: binding read failed for guild %s; "
            "falling back to the legacy KV pointer",
            guild_id,
            exc_info=True,
        )
        return None
    return value.target_id


async def get_channel_id(guild_id: int) -> str:
    """The *effective* announcement channel id for ``guild_id`` (``""`` unset).

    Binding-first (see the module docstring's precedence note); the legacy
    ``BTD6_VERSION_ANNOUNCEMENT_CHANNEL`` KV pointer is the fallback.
    """
    bound = await binding_channel_id(guild_id)
    if bound is not None:
        return str(bound)
    return await db.get_setting(guild_id, BTD6_VERSION_ANNOUNCEMENT_CHANNEL, "")


async def set_channel(guild_id: int, channel_id: int) -> None:
    """Persist ``channel_id`` as the guild's BTD6 version-announcement channel."""
    await db.set_setting(
        guild_id,
        BTD6_VERSION_ANNOUNCEMENT_CHANNEL,
        str(int(channel_id)),
    )


async def clear_channel(guild_id: int) -> None:
    """Forget the guild's announcement channel (disables the announcement)."""
    await db.set_setting(guild_id, BTD6_VERSION_ANNOUNCEMENT_CHANNEL, "")


# ---------------------------------------------------------------------------
# Subscription lifecycle
# ---------------------------------------------------------------------------


def setup(bot: Any) -> None:
    """Capture the bot ref and subscribe to ``btd6.version_detected`` once."""
    global _BOT, _SUBSCRIBED
    _BOT = bot
    if _SUBSCRIBED:
        return
    bus.on(EVT_BTD6_VERSION_DETECTED, _on_version_detected)
    _SUBSCRIBED = True


def _reset_for_tests() -> None:
    global _BOT, _SUBSCRIBED
    bus.off(EVT_BTD6_VERSION_DETECTED, _on_version_detected)
    _BOT = None
    _SUBSCRIBED = False


# ---------------------------------------------------------------------------
# Event handler + posting
# ---------------------------------------------------------------------------


def _build_embed(
    version: str,
    previous_version: str | None,
    title: str | None,
    url: str | None,
) -> discord.Embed:
    embed = discord.Embed(
        title=f"🐵 Bloons TD 6 — Update v{version}",
        description=title or f"A new BTD6 update (v{version}) is live!",
        color=discord.Color.green(),
    )
    if previous_version:
        embed.add_field(name="Previous", value=f"v{previous_version}", inline=True)
    embed.add_field(name="Now live", value=f"v{version}", inline=True)
    if isinstance(url, str) and url.startswith("http"):
        embed.add_field(
            name="Update notes",
            value=f"[Read on Steam]({url})",
            inline=False,
        )
    return append_context_footer(embed, "btd6_version_announce:global")


async def _on_version_detected(
    *,
    version: str,
    previous_version: str | None = None,
    title: str | None = None,
    url: str | None = None,
    published_at: Any = None,  # noqa: ARG001 — part of the event payload contract
    **_extra: Any,
) -> None:
    """Post the version announcement to every guild that configured a channel."""
    bot = _BOT
    if bot is None:
        return
    ver = str(version or "").strip()
    if not ver:
        return
    embed = _build_embed(ver, previous_version, title, url)
    posted = 0
    for guild in list(getattr(bot, "guilds", []) or []):
        channel = await _resolve_channel(guild)
        if channel is None:
            continue
        if await _send(channel, embed):
            posted += 1
    logger.info("btd6 version %s announced to %d channel(s)", ver, posted)


async def _resolve_channel(
    guild: Any,
) -> discord.TextChannel | discord.Thread | None:
    # Lazy import keeps this service free of a core.runtime import at load.
    from core.runtime.guild_resources import resolve_settings_channel

    # Binding-first (Q-0064): a bound version_announce_channel wins.
    bound = await binding_channel_id(guild.id)
    if bound is not None:
        getter = getattr(guild, "get_channel_or_thread", None) or guild.get_channel
        channel = getter(bound)
        if isinstance(channel, (discord.TextChannel, discord.Thread)):
            return channel
        logger.warning(
            "btd6 announce: bound channel %s not found/usable in guild %s; "
            "announcement skipped (fix or clear the binding)",
            bound,
            getattr(guild, "id", "?"),
        )
        return None

    try:
        channel = await resolve_settings_channel(
            guild,
            BTD6_VERSION_ANNOUNCEMENT_CHANNEL,
        )
    except Exception:  # noqa: BLE001 — one guild's bad config can't abort the rest
        logger.warning(
            "btd6 announce: channel resolve failed for guild %s",
            getattr(guild, "id", "?"),
            exc_info=True,
        )
        return None
    if isinstance(channel, (discord.TextChannel, discord.Thread)):
        return channel
    return None


async def _send(
    channel: discord.TextChannel | discord.Thread,
    embed: discord.Embed,
) -> bool:
    try:
        await channel.send(embed=embed)
        return True
    except discord.Forbidden:
        logger.warning(
            "btd6 announce: missing send permission in channel %s",
            getattr(channel, "id", "?"),
        )
    except discord.HTTPException:
        logger.warning(
            "btd6 announce: HTTP error sending to channel %s",
            getattr(channel, "id", "?"),
            exc_info=True,
        )
    except Exception:  # noqa: BLE001 — never raise into the event bus
        logger.warning(
            "btd6 announce: unexpected error sending to channel %s",
            getattr(channel, "id", "?"),
            exc_info=True,
        )
    return False


__all__ = [
    "clear_channel",
    "get_channel_id",
    "set_channel",
    "setup",
]
