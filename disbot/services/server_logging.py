"""Server-logging foundation — Phase 2 PR-11.

Per-guild service that subscribes to the catalogued event
``moderation.action_taken`` and posts a structured embed to a
configured log channel.  Two channel slots:

* ``logging.mod_channel``     — non-``auto_delete:*`` actions.
* ``logging.cleanup_channel`` — ``auto_delete:*`` rule-based actions.
  Falls back to the mod channel if unset.

If ``logging.auto_create_channels`` is enabled and the configured
channel id is missing or invalid, the service calls
``core.runtime.guild_resources.ensure_channel`` to create a default
channel (``bot-mod-log`` / ``bot-cleanup-log``).  Auto-creation is
**OFF** by default so a fresh install does not surprise an admin with
spontaneous channels.

Fail-safe rules (every send path catches its own exceptions and
increments a counter):

* the event bus already swallows handler exceptions, so a logging
  failure cannot crash the source moderation/cleanup action;
* missing channel, missing permissions, Discord HTTP errors, and
  auto-create failures all count their own bucket without
  re-raising.

Diagnostics counters are exposed via ``services.diagnostics_service``
under the name ``"server_logging"``.  Counter shape is stable so
``!platform consistency`` (PR-10) can read it without parsing
internals.

Default policy: **logging is OFF**.  Operators opt in per-guild via
the keys declared in ``utils.settings_keys.logging``.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any

import discord

from core.events import bus
from utils import db
from utils.settings_keys import logging as _log_keys

logger = logging.getLogger("bot.server_logging")

EVT_MOD_ACTION = "moderation.action_taken"

# ---------------------------------------------------------------------------
# Counters (module-level; reset only via _reset_for_tests)
# ---------------------------------------------------------------------------

_COUNTERS: dict[str, int] = {
    "sent_total": 0,
    "skipped_disabled": 0,
    "skipped_no_guild": 0,
    "missing_channel": 0,
    "created_channel": 0,
    "permission_error": 0,
    "send_error": 0,
    "auto_create_error": 0,
    "subscriber_errors": 0,
}


def _bump(name: str) -> None:
    _COUNTERS[name] = _COUNTERS.get(name, 0) + 1


def counters_snapshot() -> dict[str, Any]:
    """Stable counter snapshot for diagnostics consumers."""
    return {
        "counters": dict(_COUNTERS),
        "subscribed_events": [EVT_MOD_ACTION],
    }


def _reset_for_tests() -> None:
    global _BOT, _SUBSCRIBED
    for k in list(_COUNTERS):
        _COUNTERS[k] = 0
    _BOT = None
    # Note: bus subscription is intentionally NOT cleared — tests that
    # need to exercise the subscriber call it directly and assert on
    # counters; the bus binding is registered once per process.


# ---------------------------------------------------------------------------
# Config accessors
# ---------------------------------------------------------------------------

_TRUE_LITERALS = frozenset({"1", "true", "yes", "on", "enabled"})


def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in _TRUE_LITERALS


async def is_enabled(guild_id: int) -> bool:
    """Return True if server logging is enabled for *guild_id*."""
    raw = await db.get_setting(guild_id, _log_keys.LOGGING_ENABLED, "")
    return _truthy(raw)


async def auto_create_enabled(guild_id: int) -> bool:
    """Return True if auto-creation of missing log channels is enabled."""
    raw = await db.get_setting(guild_id, _log_keys.LOGGING_AUTO_CREATE_CHANNELS, "")
    return _truthy(raw)


def _channel_kind_for_action(action: str) -> str:
    """Route the action to the mod or cleanup channel slot."""
    if action.startswith("auto_delete"):
        return "cleanup"
    return "mod"


# ---------------------------------------------------------------------------
# Channel resolution / provisioning
# ---------------------------------------------------------------------------


async def resolve_log_channel(
    guild: discord.Guild,
    kind: str,
) -> discord.TextChannel | None:
    """Resolve the configured log channel for *kind* (``"mod"`` / ``"cleanup"``).

    Resolution order (S7b):

    1. ``logging.<kind>_channel`` binding — the canonical store going
       forward.  Set/cleared by :class:`BindingMutationPipeline` via
       :class:`cogs.logging.select_view.LogChannelSelectView`.
    2. ``logging_<kind>_channel`` legacy scalar — transitional
       fallback for guilds that configured logging before S7b.  Will
       be removed once the binding-backfill helper lands.
    3. For ``kind == "cleanup"`` only: fall back to the mod channel
       (via the same two-step lookup against the mod binding then
       the mod legacy scalar).

    Returns ``None`` if no source resolves to a current TextChannel.
    """
    # core.runtime imports stay function-local to avoid re-entering
    # partially-loaded core.runtime during startup.
    from core.runtime.bindings import get_binding
    from core.runtime.guild_resources import resolve_settings_channel
    from core.runtime.subsystem_schema import BindingKind

    primary_binding = "mod_channel" if kind == "mod" else "cleanup_channel"
    primary_legacy = (
        _log_keys.LOGGING_MOD_CHANNEL
        if kind == "mod"
        else _log_keys.LOGGING_CLEANUP_CHANNEL
    )

    # 1. Try the primary binding.
    try:
        binding = await get_binding(
            guild.id,
            "logging",
            primary_binding,
            expected_kind=BindingKind.CHANNEL,
        )
    except Exception as exc:  # noqa: BLE001 — read must never crash logging
        logger.warning(
            "resolve_log_channel: get_binding(%r) failed: %s",
            primary_binding,
            exc,
        )
        binding = None  # fall through to legacy
    if binding is not None and binding.target_id is not None:
        ch = guild.get_channel(binding.target_id)
        if isinstance(ch, discord.TextChannel):
            return ch

    # 2. Try the primary legacy scalar (transitional fallback).
    legacy = await resolve_settings_channel(guild, primary_legacy)
    if isinstance(legacy, discord.TextChannel):
        return legacy

    # 3. Cleanup falls back to the mod channel (both binding + legacy).
    if kind == "cleanup":
        try:
            mod_binding = await get_binding(
                guild.id,
                "logging",
                "mod_channel",
                expected_kind=BindingKind.CHANNEL,
            )
        except Exception as exc:  # noqa: BLE001 — read must never crash
            logger.warning(
                "resolve_log_channel: get_binding(mod_channel fallback) failed: %s",
                exc,
            )
            mod_binding = None
        if mod_binding is not None and mod_binding.target_id is not None:
            ch = guild.get_channel(mod_binding.target_id)
            if isinstance(ch, discord.TextChannel):
                return ch
        mod_legacy = await resolve_settings_channel(
            guild,
            _log_keys.LOGGING_MOD_CHANNEL,
        )
        if isinstance(mod_legacy, discord.TextChannel):
            return mod_legacy

    return None


async def ensure_log_channel(
    guild: discord.Guild,
    kind: str,
) -> discord.TextChannel | None:
    """Resolve or create the log channel for *kind*.

    Returns the existing/created text channel, or ``None`` if creation
    fails (caller may not have ``manage_channels`` permission, or
    Discord rejected the request).  Counters increment to surface the
    cause.
    """
    from core.runtime.guild_resources import ensure_channel

    existing = await resolve_log_channel(guild, kind)
    if existing is not None:
        return existing
    fallback_name = (
        _log_keys.DEFAULT_CLEANUP_CHANNEL_NAME
        if kind == "cleanup"
        else _log_keys.DEFAULT_MOD_CHANNEL_NAME
    )
    try:
        created = await ensure_channel(guild, fallback_name, kind="text")
    except discord.Forbidden:
        _bump("permission_error")
        logger.warning(
            "server_logging: missing manage_channels permission to create "
            "%r log channel %r in guild %d",
            kind,
            fallback_name,
            guild.id,
        )
        return None
    except discord.HTTPException as exc:
        _bump("auto_create_error")
        logger.warning(
            "server_logging: HTTP error creating %r log channel in guild %d: %s",
            kind,
            guild.id,
            exc,
        )
        return None
    except Exception as exc:  # noqa: BLE001 — fail-safe wrapper
        _bump("auto_create_error")
        logger.warning(
            "server_logging: unexpected error creating %r log channel in guild %d: %s",
            kind,
            guild.id,
            exc,
            exc_info=True,
        )
        return None
    if isinstance(created, discord.TextChannel):
        _bump("created_channel")
        return created
    return None


# ---------------------------------------------------------------------------
# Embed builder
# ---------------------------------------------------------------------------

# Distinct colour per action so dashboards (and human eyes) can
# triangulate at a glance.  Unknown actions fall back to dark_grey.
_ACTION_COLOR: dict[str, discord.Color] = {
    "warn": discord.Color.gold(),
    "timeout": discord.Color.orange(),
    "kick": discord.Color.dark_orange(),
    "ban": discord.Color.red(),
    "unban": discord.Color.green(),
    "clear_warnings": discord.Color.blurple(),
    "auto_delete": discord.Color.dark_grey(),
}

_ACTION_ICON: dict[str, str] = {
    "warn": "⚠️",
    "timeout": "⏳",
    "kick": "👢",
    "ban": "🔨",
    "unban": "🕊️",
    "clear_warnings": "🧹",
    "auto_delete": "🗑️",
}


def _root_action(action: str) -> str:
    """``"auto_delete:cleanup.prohibited_words" → "auto_delete"`` etc."""
    return action.split(":", 1)[0]


# Defensive caps so a malformed event payload cannot push the embed
# past Discord's 25-field / 6000-char limits.  Target / Actor / Guild
# / Reason already use 4 slots; capping extras at 6 keeps comfortable
# headroom for future fields without re-tuning.
_MAX_EXTRA_FIELDS = 6
_EXTRA_VALUE_CAP = 500


def format_log_embed(
    *,
    action: str,
    guild_id: int,
    target_id: int,
    actor_id: int | None,
    reason: str,
    extras: dict[str, Any] | None = None,
) -> discord.Embed:
    """Render a moderation/cleanup payload as a Discord embed.

    Unknown actions render with the generic dark-grey style so
    subscribers never blank-render a new moderation action type the
    service hasn't seen.  ``extras`` is capped at
    :data:`_MAX_EXTRA_FIELDS` slots and each value is truncated to
    :data:`_EXTRA_VALUE_CAP` chars; if more keys are supplied, a
    single ``"... truncated"`` field reports the count so the embed
    stays under Discord's 25-field / 6000-char limits.
    """
    root = _root_action(action)
    color = _ACTION_COLOR.get(root, discord.Color.dark_grey())
    icon = _ACTION_ICON.get(root, "•")
    title = f"{icon} {action}"
    embed = discord.Embed(
        title=title,
        color=color,
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    embed.add_field(name="Target", value=f"<@{target_id}> (`{target_id}`)", inline=True)
    actor_display = f"<@{actor_id}>" if actor_id else "system"
    embed.add_field(name="Actor", value=actor_display, inline=True)
    embed.add_field(name="Guild", value=str(guild_id), inline=True)
    if reason:
        embed.add_field(name="Reason", value=reason[:1000], inline=False)
    if extras:
        items = list(extras.items())
        for k, v in items[:_MAX_EXTRA_FIELDS]:
            embed.add_field(
                name=str(k)[:256],
                value=str(v)[:_EXTRA_VALUE_CAP],
                inline=False,
            )
        if len(items) > _MAX_EXTRA_FIELDS:
            dropped = len(items) - _MAX_EXTRA_FIELDS
            embed.add_field(
                name="… truncated",
                value=f"{dropped} extra field(s) omitted to stay under embed limits.",
                inline=False,
            )
    return embed


# ---------------------------------------------------------------------------
# Send + handler
# ---------------------------------------------------------------------------


async def log_event(
    guild: discord.Guild,
    *,
    action: str,
    target_id: int,
    actor_id: int | None,
    reason: str,
    extras: dict[str, Any] | None = None,
) -> bool:
    """Send a structured log embed for *action* to the routed channel.

    Returns True if the embed was sent; False on any other outcome.
    Every failure path is fail-safe: counters bump, the caller never
    sees the exception, and the next event proceeds normally.
    """
    if not await is_enabled(guild.id):
        _bump("skipped_disabled")
        return False

    kind = _channel_kind_for_action(action)
    channel = await resolve_log_channel(guild, kind)
    if channel is None and await auto_create_enabled(guild.id):
        channel = await ensure_log_channel(guild, kind)
    if channel is None:
        _bump("missing_channel")
        return False

    embed = format_log_embed(
        action=action,
        guild_id=guild.id,
        target_id=target_id,
        actor_id=actor_id,
        reason=reason,
        extras=extras,
    )
    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        _bump("permission_error")
        logger.warning(
            "server_logging: missing send permission in #%s (guild %d)",
            channel.name,
            guild.id,
        )
        return False
    except discord.HTTPException as exc:
        _bump("send_error")
        logger.warning(
            "server_logging: HTTP error sending to #%s (guild %d): %s",
            channel.name,
            guild.id,
            exc,
        )
        return False
    except Exception as exc:  # noqa: BLE001 — fail-safe wrapper
        _bump("send_error")
        logger.warning(
            "server_logging: unexpected error sending to #%s (guild %d): %s",
            channel.name,
            guild.id,
            exc,
            exc_info=True,
        )
        return False
    _bump("sent_total")
    return True


async def _on_moderation_action(
    *,
    guild_id: int,
    target_id: int,
    actor_id: int | None,
    action: str,
    reason: str,
    **extras: Any,
) -> None:
    """Bus subscriber for ``moderation.action_taken``.

    Resolves the bot's view of the guild from the bot reference
    captured at ``setup(bot)`` time, then delegates to
    :func:`log_event`.  Any unexpected exception is caught + counted;
    the event bus itself also swallows handler exceptions, so this is
    a belt-and-braces safety net keeping ``subscriber_errors`` honest
    independently of the bus's own error log.
    """
    try:
        bot = _BOT
        if bot is None:
            _bump("skipped_no_guild")
            return
        guild = bot.get_guild(guild_id)
        if guild is None:
            _bump("skipped_no_guild")
            return
        await log_event(
            guild,
            action=action,
            target_id=target_id,
            actor_id=actor_id,
            reason=reason,
            extras=extras or None,
        )
    except Exception as exc:  # noqa: BLE001 — fail-safe subscriber
        _bump("subscriber_errors")
        logger.exception(
            "server_logging: subscriber raised %s — counted and swallowed.",
            type(exc).__name__,
            exc_info=exc,
        )


# ---------------------------------------------------------------------------
# Setup / diagnostics registration
# ---------------------------------------------------------------------------

# Captured at setup(bot); used by the bus subscriber to resolve guilds
# from guild_id payloads.  Module-level so subscribers don't have to
# rely on a global registry.  Tests can call _reset_for_tests() or
# pass a fake bot via setup() directly.  Typed as ``Any`` (not
# ``commands.Bot``) to avoid importing discord.ext.commands at module
# load and to let tests pass MagicMock without satisfying the full
# Bot interface.
_BOT: Any = None
_SUBSCRIBED = False


def setup(bot: object | None = None) -> None:
    """Register the bus subscriber + capture the bot reference.

    Idempotent.  Called once from ``bot1.py`` after ``runtime.setup()``
    so the captured bot reference matches the live event loop.
    """
    global _SUBSCRIBED, _BOT
    _BOT = bot
    if _SUBSCRIBED:
        return
    bus.on(EVT_MOD_ACTION, _on_moderation_action)
    _SUBSCRIBED = True
    logger.info(
        "server_logging: subscribed to %r (default per-guild policy: OFF)",
        EVT_MOD_ACTION,
    )


def _register_diagnostics() -> None:
    from services import diagnostics_service

    diagnostics_service.register("server_logging", counters_snapshot)


_register_diagnostics()


__all__ = [
    "EVT_MOD_ACTION",
    "auto_create_enabled",
    "counters_snapshot",
    "ensure_log_channel",
    "format_log_embed",
    "is_enabled",
    "log_event",
    "resolve_log_channel",
    "setup",
]
