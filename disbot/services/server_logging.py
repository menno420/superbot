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
# Phase 9c.1 — subscribe to the generic audit-trail event emitted by
# mutation pipelines. RolloutMutationPipeline is the pilot publisher;
# other pipelines (SettingsMutationPipeline, BindingMutationPipeline,
# ResourceProvisioningPipeline, GovernanceMutationPipeline) add their
# audit emits in Phase 9c.2.
EVT_AUDIT_ACTION_RECORDED = "audit.action_recorded"

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
    # Phase 9c.1 — per-route bucket for the audit subscriber. Other
    # route buckets (debug_sent / info_sent / warning_sent / error_sent)
    # land alongside their respective subscribers in Phase 9c.3/9c.4.
    "audit_sent": 0,
    # server-management PR10 — optional public moderation log (separate
    # subscriber; moderator-name-redacted; gated by the moderation policy).
    "mod_public_sent": 0,
    "mod_public_skipped": 0,
    # Server event logging v1 (Q-0109) — passive Discord-event handlers
    # (message edits/deletes, member joins/leaves, role changes). Share the
    # existing permission_error / send_error buckets for delivery failures.
    "event_sent": 0,
    "event_skipped_disabled": 0,
    # Completion cert punch #1 — event suppressed because its channel or
    # subject id is on the guild's ignore list.
    "event_skipped_ignored": 0,
    "event_missing_channel": 0,
}


def _bump(name: str) -> None:
    _COUNTERS[name] = _COUNTERS.get(name, 0) + 1


def counters_snapshot() -> dict[str, Any]:
    """Stable counter snapshot for diagnostics consumers."""
    return {
        "counters": dict(_COUNTERS),
        "subscribed_events": [EVT_MOD_ACTION, EVT_AUDIT_ACTION_RECORDED],
    }


def _reset_for_tests() -> None:
    global _BOT, _SUBSCRIBED
    for k in list(_COUNTERS):
        _COUNTERS[k] = 0
    _BOT = None
    # Tear the bus subscription down too, so a test that called setup()
    # cannot leak _on_audit_action / _on_moderation_action onto the
    # process-global bus for every later test (the leak surfaced under
    # parallel xdist scheduling: the orphaned subscriber fired on another
    # test's audit.action_recorded emit and skewed its delivery stats).
    # setup() re-registers cleanly because we also drop the _SUBSCRIBED
    # latch; tests that call the subscriber directly are unaffected.
    if _SUBSCRIBED:
        bus.off(EVT_MOD_ACTION, _on_moderation_action)
        bus.off(EVT_MOD_ACTION, _on_moderation_action_public)
        bus.off(EVT_AUDIT_ACTION_RECORDED, _on_audit_action)
    _SUBSCRIBED = False


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


# Phase 9a — route table mapping public ``kind`` tokens to the
# ``logging.<binding>`` slot they read from. Severity and audit routes
# fall back through ``_ROUTE_FALLBACK`` to ``mod`` when their own
# binding is unset; ``mod`` itself is terminal.
_ROUTE_TO_BINDING: dict[str, str] = {
    "mod": "mod_channel",
    "cleanup": "cleanup_channel",
    "debug": "debug_channel",
    "info": "info_channel",
    "warning": "warning_channel",
    "error": "error_channel",
    "audit": "audit_channel",
    # Server event logging v1 (Q-0109) — passive Discord-event routes.
    # ``events`` is the combined "everything" channel (single-channel
    # mode); the three per-category routes fall back to it.
    "events": "events_channel",
    "message_log": "message_channel",
    "member_log": "member_channel",
    "role_log": "role_channel",
}

# Server event logging v1 — maps an event category (from
# ``services.server_logging_config``) to its per-category route kind. The
# combined route (``events``) is selected directly when routing mode is
# ``combined``; in ``per_category`` mode these per-category kinds are used,
# and each falls back to ``events`` (see ``_ROUTE_FALLBACK``) when its own
# channel is unset.
_CATEGORY_TO_ROUTE: dict[str, str] = {
    "messages": "message_log",
    "members": "member_log",
    "roles": "role_log",
}

# Auto-create channel names per route kind. Routes absent from this map
# (the Phase-9a severity/audit routes) keep their historical behaviour of
# defaulting to the mod-log name via ``ensure_log_channel``'s ``.get``
# fallback — only the new event routes opt into purpose-built names.
_KIND_DEFAULT_CHANNEL_NAME: dict[str, str] = {
    "mod": _log_keys.DEFAULT_MOD_CHANNEL_NAME,
    "cleanup": _log_keys.DEFAULT_CLEANUP_CHANNEL_NAME,
    "events": _log_keys.DEFAULT_EVENTS_CHANNEL_NAME,
    "message_log": _log_keys.DEFAULT_MESSAGE_LOG_CHANNEL_NAME,
    "member_log": _log_keys.DEFAULT_MEMBER_LOG_CHANNEL_NAME,
    "role_log": _log_keys.DEFAULT_ROLE_LOG_CHANNEL_NAME,
}

# Per-route fallback. ``cleanup`` historically falls back to ``mod``
# (pre-Phase-9a behaviour preserved). Severity + audit routes also
# fall back to ``mod`` so a guild that has only configured the mod
# channel still gets every event delivered somewhere.
_ROUTE_FALLBACK: dict[str, str | None] = {
    "mod": None,
    "cleanup": "mod",
    "debug": "mod",
    "info": "mod",
    "warning": "mod",
    "error": "mod",
    "audit": "mod",
    # Event routes terminate at the combined ``events`` channel, NOT at
    # ``mod`` — passive-event noise (deletes, joins) must never spill into
    # the moderation-action channel. ``events`` itself is terminal: when
    # unset, the event simply isn't logged (fail-safe).
    "events": None,
    "message_log": "events",
    "member_log": "events",
    "role_log": "events",
}


async def resolve_log_channel(
    guild: discord.Guild,
    kind: str,
) -> discord.TextChannel | None:
    """Resolve the configured log channel for *kind*.

    Recognised ``kind`` values:

    * Sources (pre-Phase 9): ``"mod"``, ``"cleanup"``.
    * Severity routes (Phase 9a): ``"debug"``, ``"info"``,
      ``"warning"``, ``"error"``.
    * Audit route (Phase 9a): ``"audit"``.

    Resolution order for any route:

    1. ``logging.<route>_channel`` binding — the canonical store.
       Set/cleared by :class:`BindingMutationPipeline` via
       :class:`cogs.logging.select_view.LogChannelSelectView`.
    2. Legacy scalar fallback — only ``"mod"`` and ``"cleanup"`` have
       legacy scalars (``LOGGING_MOD_CHANNEL`` /
       ``LOGGING_CLEANUP_CHANNEL``). Severity / audit routes are new
       in Phase 9a and never had a legacy scalar.
    3. Source-tier fallback — every non-``"mod"`` route ultimately
       falls back to ``"mod"`` (via this function called recursively),
       so a guild that has only configured the mod channel still
       receives every event somewhere.

    Returns ``None`` if no source resolves to a current TextChannel
    and the fallback chain is exhausted.

    Unknown ``kind`` values return ``None`` after logging a warning —
    callers can pass new tokens through without raising, but no
    channel will be returned until the route table is extended.
    """
    # core.runtime imports stay function-local to avoid re-entering
    # partially-loaded core.runtime during startup.
    from core.runtime.bindings import get_binding
    from core.runtime.guild_resources import resolve_settings_channel
    from core.runtime.subsystem_schema import BindingKind

    binding_name = _ROUTE_TO_BINDING.get(kind)
    if binding_name is None:
        logger.warning(
            "resolve_log_channel: unknown kind %r — returning None. "
            "Add it to _ROUTE_TO_BINDING to enable lookup.",
            kind,
        )
        return None

    # 1. Try the route's own binding.
    try:
        binding = await get_binding(
            guild.id,
            "logging",
            binding_name,
            expected_kind=BindingKind.CHANNEL,
        )
    except Exception as exc:  # noqa: BLE001 — read must never crash logging
        logger.warning(
            "resolve_log_channel: get_binding(%r) failed: %s",
            binding_name,
            exc,
        )
        binding = None  # fall through to legacy / fallback
    if binding is not None and binding.target_id is not None:
        ch = guild.get_channel(binding.target_id)
        if isinstance(ch, discord.TextChannel):
            return ch

    # 2. Legacy scalar (mod/cleanup only — severity/audit are new in
    # Phase 9a and have no pre-existing scalar).
    if kind == "mod":
        legacy = await resolve_settings_channel(guild, _log_keys.LOGGING_MOD_CHANNEL)
        if isinstance(legacy, discord.TextChannel):
            return legacy
    elif kind == "cleanup":
        legacy = await resolve_settings_channel(
            guild,
            _log_keys.LOGGING_CLEANUP_CHANNEL,
        )
        if isinstance(legacy, discord.TextChannel):
            return legacy

    # 3. Source-tier fallback. ``_ROUTE_FALLBACK`` is acyclic and
    # terminates at ``"mod"`` (fallback=None), so a single recursive
    # call is bounded.
    fallback = _ROUTE_FALLBACK.get(kind)
    if fallback is not None and fallback != kind:
        return await resolve_log_channel(guild, fallback)

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
    fallback_name = _KIND_DEFAULT_CHANNEL_NAME.get(
        kind,
        _log_keys.DEFAULT_MOD_CHANNEL_NAME,
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
    # Canonical token emitted by moderation_service.clear_warnings (one word,
    # matches the historical mod_logs rows); "clear_warnings" kept as a
    # back-compat alias for any older payloads.
    "clearwarnings": discord.Color.blurple(),
    "clear_warnings": discord.Color.blurple(),
    "auto_delete": discord.Color.dark_grey(),
    # Post-moderation message sweep (server-management PR10) — moderator-
    # initiated, distinct from the system auto_delete tier.
    "post_action_cleanup": discord.Color.teal(),
}

_ACTION_ICON: dict[str, str] = {
    "warn": "⚠️",
    "timeout": "⏳",
    "kick": "👢",
    "ban": "🔨",
    "unban": "🕊️",
    "clearwarnings": "🧹",
    "clear_warnings": "🧹",
    "auto_delete": "🗑️",
    "post_action_cleanup": "🧽",
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


def format_public_log_embed(
    *,
    action: str,
    target_id: int,
    reason: str,
) -> discord.Embed:
    """Render the **public** moderation-log embed (server-management PR10).

    Deliberately narrower than :func:`format_log_embed`: it shows the action,
    the affected member, and the reason — but **never the acting moderator**
    (the maintainer's choice for the public surface) nor the internal guild id.
    The staff mod-log keeps the full record.
    """
    root = _root_action(action)
    embed = discord.Embed(
        title=f"{_ACTION_ICON.get(root, '•')} {action}",
        color=_ACTION_COLOR.get(root, discord.Color.dark_grey()),
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    embed.add_field(name="Member", value=f"<@{target_id}> (`{target_id}`)", inline=True)
    if reason:
        embed.add_field(name="Reason", value=reason[:1000], inline=False)
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


def format_audit_embed(
    *,
    mutation_id: str,
    subsystem: str,
    mutation_type: str,
    target: str,
    scope: str,
    guild_id: int | None,
    prev_value: str | None,
    new_value: str | None,
    actor_id: int | None,
    actor_type: str,
    occurred_at: str,
) -> discord.Embed:
    """Render an ``audit.action_recorded`` payload as a Discord embed.

    Phase 9c.1 — generic audit-trail rendering. The payload contract
    matches what :func:`services.rollout_mutation._emit_audit_event`
    sends; future publishers (other mutation pipelines) MUST use the
    same field names.
    """
    embed = discord.Embed(
        title=f"📋 {mutation_type}",
        description=(
            f"`{subsystem}` · scope `{scope}`"
            + (f" · guild `{guild_id}`" if guild_id is not None else "")
        ),
        color=discord.Color.dark_teal(),
    )
    embed.add_field(name="Target", value=f"`{target}`", inline=True)
    actor_display = f"<@{actor_id}>" if actor_id else f"`{actor_type}`"
    embed.add_field(name="Actor", value=actor_display, inline=True)
    embed.add_field(name="Actor type", value=f"`{actor_type}`", inline=True)
    embed.add_field(
        name="Previous",
        value=f"`{prev_value}`" if prev_value is not None else "*(none)*",
        inline=True,
    )
    embed.add_field(
        name="New",
        value=f"`{new_value}`" if new_value is not None else "*(cleared)*",
        inline=True,
    )
    embed.add_field(name="Mutation ID", value=f"`{mutation_id}`", inline=False)
    embed.set_footer(text=f"Recorded at {occurred_at}")
    return embed


async def log_audit_event(
    guild: discord.Guild,
    *,
    mutation_id: str,
    subsystem: str,
    mutation_type: str,
    target: str,
    scope: str,
    guild_id: int | None,
    prev_value: str | None,
    new_value: str | None,
    actor_id: int | None,
    actor_type: str,
    occurred_at: str,
) -> bool:
    """Send a structured audit embed to the routed audit channel.

    Resolution: ``resolve_log_channel(guild, "audit")`` — which tries
    ``logging.audit_channel`` first, then falls back to
    ``logging.mod_channel`` per the Phase 9a route table.

    Returns True if delivered, False on any other outcome. Every
    failure path is fail-safe and counted.
    """
    if not await is_enabled(guild.id):
        _bump("skipped_disabled")
        return False

    channel = await resolve_log_channel(guild, "audit")
    if channel is None and await auto_create_enabled(guild.id):
        channel = await ensure_log_channel(guild, "audit")
    if channel is None:
        _bump("missing_channel")
        return False

    embed = format_audit_embed(
        mutation_id=mutation_id,
        subsystem=subsystem,
        mutation_type=mutation_type,
        target=target,
        scope=scope,
        guild_id=guild_id,
        prev_value=prev_value,
        new_value=new_value,
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=occurred_at,
    )
    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        _bump("permission_error")
        logger.warning(
            "server_logging audit: missing send permission in #%s (guild %d)",
            channel.name,
            guild.id,
        )
        return False
    except discord.HTTPException as exc:
        _bump("send_error")
        logger.warning(
            "server_logging audit: HTTP error sending to #%s (guild %d): %s",
            channel.name,
            guild.id,
            exc,
        )
        return False
    except Exception as exc:  # noqa: BLE001 — fail-safe wrapper
        _bump("send_error")
        logger.warning(
            "server_logging audit: unexpected error sending to #%s (guild %d): %s",
            channel.name,
            guild.id,
            exc,
            exc_info=True,
        )
        return False
    _bump("audit_sent")
    return True


async def _on_audit_action(
    *,
    mutation_id: str,
    subsystem: str,
    mutation_type: str,
    target: str,
    scope: str,
    guild_id: int | None,
    prev_value: str | None,
    new_value: str | None,
    actor_id: int | None,
    actor_type: str,
    occurred_at: str,
    **_extras: Any,
) -> None:
    """Bus subscriber for ``audit.action_recorded``.

    Resolves the guild via the captured bot reference and delegates to
    :func:`log_audit_event`. Global-scope mutations (``guild_id=None``)
    are silently skipped — they have no guild-specific channel to
    render into.

    Extra payload fields are accepted via ``**_extras`` so the bus
    contract stays loose: future publishers can add fields without
    breaking this subscriber.

    The bus already swallows handler exceptions; the try/except below
    keeps the ``subscriber_errors`` counter honest independently.
    """
    try:
        if guild_id is None:
            _bump("skipped_no_guild")
            return
        bot = _BOT
        if bot is None:
            _bump("skipped_no_guild")
            return
        guild = bot.get_guild(guild_id)
        if guild is None:
            _bump("skipped_no_guild")
            return
        await log_audit_event(
            guild,
            mutation_id=mutation_id,
            subsystem=subsystem,
            mutation_type=mutation_type,
            target=target,
            scope=scope,
            guild_id=guild_id,
            prev_value=prev_value,
            new_value=new_value,
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=occurred_at,
        )
    except Exception as exc:  # noqa: BLE001 — fail-safe subscriber
        _bump("subscriber_errors")
        logger.exception(
            "server_logging audit subscriber raised %s — counted and swallowed.",
            type(exc).__name__,
            exc_info=exc,
        )


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


# Only disciplinary actions can ever surface on the public log — the pre-filter
# that lets the public subscriber skip unban / clearwarnings / post-action
# sweep / system auto-deletes before reading any config.
_PUBLIC_ELIGIBLE_ACTIONS = frozenset({"warn", "timeout", "kick", "ban"})


async def maybe_log_public(
    guild: discord.Guild,
    *,
    action: str,
    target_id: int,
    reason: str,
) -> bool:
    """Post the redacted public-moderation embed when the guild opts in.

    Gated solely by the moderation policy (``public_log_actions`` selects which
    actions, ``public_log_channel`` names the destination) — **independent of
    the ``logging.enabled`` staff master switch**, since an operator who
    configures a public channel clearly wants it.  Best-effort, fail-safe, and
    counted; never raises into the bus.
    """
    from services import moderation_config

    policy = await moderation_config.load_policy(guild.id)
    if not moderation_config.public_log_includes(action, policy):
        _bump("mod_public_skipped")
        return False
    channel = guild.get_channel(policy.public_log_channel_id)
    if not isinstance(channel, discord.TextChannel):
        _bump("mod_public_skipped")  # channel unset or stale/invalid
        return False
    embed = format_public_log_embed(action=action, target_id=target_id, reason=reason)
    try:
        await channel.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException) as exc:
        _bump("send_error")
        logger.warning(
            "server_logging public: could not send to #%s (guild %d): %s",
            getattr(channel, "name", "?"),
            guild.id,
            exc,
        )
        return False
    _bump("mod_public_sent")
    return True


async def _on_moderation_action_public(
    *,
    guild_id: int,
    target_id: int,
    action: str,
    reason: str,
    **_extras: Any,
) -> None:
    """Bus subscriber for the optional PUBLIC moderation log.

    Registered separately from :func:`_on_moderation_action` so the staff-log
    path is untouched.  ``actor_id`` is intentionally swallowed into
    ``_extras`` — the public surface never names the moderator.  Non-
    disciplinary actions are skipped before any config read.
    """
    try:
        if _root_action(action) not in _PUBLIC_ELIGIBLE_ACTIONS:
            return
        bot = _BOT
        if bot is None:
            return
        guild = bot.get_guild(guild_id)
        if guild is None:
            return
        await maybe_log_public(
            guild,
            action=action,
            target_id=target_id,
            reason=reason,
        )
    except Exception as exc:  # noqa: BLE001 — fail-safe subscriber
        _bump("subscriber_errors")
        logger.exception(
            "server_logging public subscriber raised %s — counted and swallowed.",
            type(exc).__name__,
            exc_info=exc,
        )


# ---------------------------------------------------------------------------
# Server event logging v1 (Q-0109) — passive Discord-event handlers
# ---------------------------------------------------------------------------
#
# The passive layer: when a tracked Discord event fires (message
# edit/delete, member join/leave, role change), the LoggingCog listener
# delegates here. Each handler loads the per-guild EventLoggingPolicy,
# gates on the master switch + its category flag, resolves the routed
# channel, and posts a structured embed — fully fail-safe (an error counts
# a bucket and returns; it never raises into the gateway, so a logging
# fault can't block legitimate activity).

# Discord embed field-value limit; content/role lists are truncated to it.
_EVENT_VALUE_CAP = 1024


def _truncate(text: str, cap: int = _EVENT_VALUE_CAP) -> str:
    """Truncate ``text`` to ``cap`` chars with an ellipsis if over."""
    if len(text) <= cap:
        return text
    return text[: cap - 1] + "…"


def _relative_ts(when: datetime.datetime | None) -> str | None:
    """Render a Discord ``<t:...:R>`` relative timestamp, or ``None``."""
    if when is None:
        return None
    return f"<t:{int(when.timestamp())}:R>"


def format_message_delete_embed(message: discord.Message) -> discord.Embed:
    """Render a deleted message as a log embed (author · channel · content)."""
    embed = discord.Embed(
        title="🗑️ Message deleted",
        color=discord.Color.red(),
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    author = message.author
    embed.add_field(
        name="Author",
        value=f"<@{author.id}> (`{author.id}`)",
        inline=True,
    )
    embed.add_field(
        name="Channel",
        value=getattr(message.channel, "mention", "*(unknown)*"),
        inline=True,
    )
    content = message.content or ""
    embed.add_field(
        name="Content",
        value=_truncate(content) if content else "*(no text content)*",
        inline=False,
    )
    if message.attachments:
        names = "\n".join(a.filename for a in message.attachments)
        embed.add_field(name="Attachments", value=_truncate(names), inline=False)
    return embed


def format_message_edit_embed(
    before: discord.Message,
    after: discord.Message,
) -> discord.Embed:
    """Render a message edit as a log embed (before/after + jump link)."""
    embed = discord.Embed(
        title="✏️ Message edited",
        color=discord.Color.gold(),
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    author = after.author
    embed.add_field(
        name="Author",
        value=f"<@{author.id}> (`{author.id}`)",
        inline=True,
    )
    embed.add_field(
        name="Channel",
        value=getattr(after.channel, "mention", "*(unknown)*"),
        inline=True,
    )
    embed.add_field(
        name="Before",
        value=_truncate(before.content) if before.content else "*(empty)*",
        inline=False,
    )
    embed.add_field(
        name="After",
        value=_truncate(after.content) if after.content else "*(empty)*",
        inline=False,
    )
    jump = getattr(after, "jump_url", None)
    if jump:
        embed.add_field(name="Jump", value=f"[Go to message]({jump})", inline=False)
    return embed


def format_member_join_embed(member: discord.Member) -> discord.Embed:
    """Render a member join as a log embed (member · account age · count)."""
    embed = discord.Embed(
        title="📥 Member joined",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    embed.add_field(
        name="Member",
        value=f"<@{member.id}> (`{member.id}`)",
        inline=True,
    )
    created = _relative_ts(getattr(member, "created_at", None))
    if created:
        embed.add_field(name="Account created", value=created, inline=True)
    count = getattr(member.guild, "member_count", None)
    if count is not None:
        embed.add_field(name="Member count", value=str(count), inline=True)
    return embed


def format_member_leave_embed(member: discord.Member) -> discord.Embed:
    """Render a member departure as a log embed (member · joined · roles)."""
    embed = discord.Embed(
        title="📤 Member left",
        color=discord.Color.dark_orange(),
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    # Show the username too — a mention of a departed member often won't
    # resolve to a name in the client.
    embed.add_field(
        name="Member",
        value=f"{member} — <@{member.id}> (`{member.id}`)",
        inline=False,
    )
    joined = _relative_ts(getattr(member, "joined_at", None))
    if joined:
        embed.add_field(name="Joined", value=joined, inline=True)
    held = [r for r in getattr(member, "roles", []) if not r.is_default()]
    if held:
        embed.add_field(
            name="Roles held",
            value=_truncate(", ".join(r.mention for r in held)),
            inline=False,
        )
    return embed


def format_role_change_embed(
    member: discord.Member,
    added: list[discord.Role],
    removed: list[discord.Role],
) -> discord.Embed:
    """Render a member's role grants/revocations as a log embed."""
    embed = discord.Embed(
        title="🎭 Roles updated",
        color=discord.Color.blurple(),
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    embed.add_field(
        name="Member",
        value=f"<@{member.id}> (`{member.id}`)",
        inline=False,
    )
    if added:
        embed.add_field(
            name="➕ Added",
            value=_truncate(", ".join(r.mention for r in added)),
            inline=False,
        )
    if removed:
        embed.add_field(
            name="➖ Removed",
            value=_truncate(", ".join(r.mention for r in removed)),
            inline=False,
        )
    return embed


async def resolve_event_channel(
    guild: discord.Guild,
    category: str,
    *,
    per_category: bool,
) -> discord.TextChannel | None:
    """Resolve the destination channel for an event ``category``.

    ``per_category`` False → the combined ``events`` route. True → the
    category's own route (``message_log`` / ``member_log`` / ``role_log``),
    which the route table falls back to ``events`` for when its own channel
    is unset. Returns ``None`` when nothing resolves (event not logged).
    """
    if per_category:
        kind = _CATEGORY_TO_ROUTE.get(category)
        if kind is None:
            return None
    else:
        kind = "events"
    return await resolve_log_channel(guild, kind)


async def _post_event_embed(
    guild: discord.Guild,
    category: str,
    *,
    per_category: bool,
    embed: discord.Embed,
) -> bool:
    """Resolve the routed channel and send ``embed`` — fail-safe + counted."""
    channel = await resolve_event_channel(guild, category, per_category=per_category)
    if channel is None and await auto_create_enabled(guild.id):
        kind = _CATEGORY_TO_ROUTE[category] if per_category else "events"
        channel = await ensure_log_channel(guild, kind)
    if channel is None:
        _bump("event_missing_channel")
        return False
    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        _bump("permission_error")
        logger.warning(
            "server_logging event: missing send permission in #%s (guild %d)",
            channel.name,
            guild.id,
        )
        return False
    except discord.HTTPException as exc:
        _bump("send_error")
        logger.warning(
            "server_logging event: HTTP error sending to #%s (guild %d): %s",
            channel.name,
            guild.id,
            exc,
        )
        return False
    except Exception as exc:  # noqa: BLE001 — fail-safe wrapper
        _bump("send_error")
        logger.warning(
            "server_logging event: unexpected error sending to #%s (guild %d): %s",
            channel.name,
            guild.id,
            exc,
            exc_info=True,
        )
        return False
    _bump("event_sent")
    return True


async def _log_event_if_enabled(
    guild: discord.Guild | None,
    category: str,
    embed_factory: Any,
    *,
    channel_id: int | None = None,
    user_id: int | None = None,
) -> bool:
    """Shared gate for every passive handler.

    Loads the policy, applies the master+category gate **and** the ignore
    lists (completion cert punch #1: skip events whose ``channel_id`` or
    subject ``user_id`` is excluded for this guild), then posts the embed
    built by ``embed_factory`` (a zero-arg callable, evaluated only once the
    gates pass so a disabled/ignored event does no embed work). Fully
    fail-safe.
    """
    if guild is None:
        return False
    from services import server_logging_config as _cfg

    try:
        policy = await _cfg.load_policy(guild.id)
        if not policy.should_log(category):
            _bump("event_skipped_disabled")
            return False
        if policy.is_ignored(channel_id=channel_id, user_id=user_id):
            _bump("event_skipped_ignored")
            return False
        return await _post_event_embed(
            guild,
            category,
            per_category=policy.per_category,
            embed=embed_factory(),
        )
    except Exception as exc:  # noqa: BLE001 — a logging fault must never block
        _bump("subscriber_errors")
        logger.exception(
            "server_logging event handler raised %s — counted and swallowed.",
            type(exc).__name__,
            exc_info=exc,
        )
        return False


async def log_message_delete(message: discord.Message) -> bool:
    """Post a deleted-message embed when the messages category is enabled."""
    from services.server_logging_config import CATEGORY_MESSAGES

    return await _log_event_if_enabled(
        message.guild,
        CATEGORY_MESSAGES,
        lambda: format_message_delete_embed(message),
        channel_id=getattr(message.channel, "id", None),
        user_id=getattr(message.author, "id", None),
    )


async def log_message_edit(
    before: discord.Message,
    after: discord.Message,
) -> bool:
    """Post a message-edit embed when the messages category is enabled."""
    from services.server_logging_config import CATEGORY_MESSAGES

    return await _log_event_if_enabled(
        after.guild,
        CATEGORY_MESSAGES,
        lambda: format_message_edit_embed(before, after),
        channel_id=getattr(after.channel, "id", None),
        user_id=getattr(after.author, "id", None),
    )


async def log_member_join(member: discord.Member) -> bool:
    """Post a member-join embed when the members category is enabled."""
    from services.server_logging_config import CATEGORY_MEMBERS

    return await _log_event_if_enabled(
        member.guild,
        CATEGORY_MEMBERS,
        lambda: format_member_join_embed(member),
        user_id=getattr(member, "id", None),
    )


async def log_member_leave(member: discord.Member) -> bool:
    """Post a member-departure embed when the members category is enabled."""
    from services.server_logging_config import CATEGORY_MEMBERS

    return await _log_event_if_enabled(
        member.guild,
        CATEGORY_MEMBERS,
        lambda: format_member_leave_embed(member),
        user_id=getattr(member, "id", None),
    )


async def log_role_change(
    member: discord.Member,
    added: list[discord.Role],
    removed: list[discord.Role],
) -> bool:
    """Post a role-change embed when the roles category is enabled."""
    from services.server_logging_config import CATEGORY_ROLES

    if not added and not removed:
        return False
    return await _log_event_if_enabled(
        member.guild,
        CATEGORY_ROLES,
        lambda: format_role_change_embed(member, added, removed),
        user_id=getattr(member, "id", None),
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
    bus.on(EVT_MOD_ACTION, _on_moderation_action_public)
    bus.on(EVT_AUDIT_ACTION_RECORDED, _on_audit_action)
    _SUBSCRIBED = True
    logger.info(
        "server_logging: subscribed to %r (+ public mirror) + %r "
        "(default per-guild policy: OFF)",
        EVT_MOD_ACTION,
        EVT_AUDIT_ACTION_RECORDED,
    )


def _register_diagnostics() -> None:
    from services import diagnostics_service

    diagnostics_service.register("server_logging", counters_snapshot)


_register_diagnostics()


__all__ = [
    "EVT_AUDIT_ACTION_RECORDED",
    "EVT_MOD_ACTION",
    "auto_create_enabled",
    "counters_snapshot",
    "ensure_log_channel",
    "format_audit_embed",
    "format_log_embed",
    "format_member_join_embed",
    "format_member_leave_embed",
    "format_message_delete_embed",
    "format_message_edit_embed",
    "format_public_log_embed",
    "format_role_change_embed",
    "is_enabled",
    "log_audit_event",
    "log_event",
    "log_member_join",
    "log_member_leave",
    "log_message_delete",
    "log_message_edit",
    "log_role_change",
    "maybe_log_public",
    "resolve_event_channel",
    "resolve_log_channel",
    "setup",
]
