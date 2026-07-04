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


def _set_subject_author(embed: discord.Embed, user: Any) -> None:
    """Put the event *subject*'s avatar + name in the embed's author slot.

    Discord renders the author slot as a small round avatar beside a name at the
    top of the embed, so every log entry gets a face — the "who" of the event at
    a glance while scanning the channel (what mature log bots show).  Purely
    additive: the structured fields below (the mention + copyable id, channel,
    content…) are untouched, and there is **no network on our side** — the embed
    just references the avatar's CDN url, so nothing is fetched and there is no
    failure path to guard.  Defensive so a partial object (a bare id, an odd
    fake, or ``None``) yields no author line rather than raising into the
    fail-safe handler; ``display_name`` / ``display_avatar`` exist on both
    ``discord.User`` and ``discord.Member``.
    """
    if user is None:
        return
    name = getattr(user, "display_name", None) or getattr(user, "name", None)
    if not name:
        return
    avatar = getattr(user, "display_avatar", None)
    icon_url = getattr(avatar, "url", None)
    embed.set_author(name=str(name)[:256], icon_url=icon_url)


def _resolve_subject_user(guild: discord.Guild, user_id: int | None) -> Any:
    """Best-effort resolve a user id to a member/user object for the avatar.

    The passive-event embeds already hold the ``discord.Member``/``User`` object
    they log; the moderation + audit embeds carry only ids, so this is how they
    get the same face.  Tries the guild member cache first (via the canonical
    ``resources.resolve_member`` resolver — the invariant forbids a raw
    ``guild.get_member`` here), then the bot's global user cache (covers a
    just-banned/kicked member no longer in the guild).  **Cache lookups only —
    never a network call** in the hot logging path.  Returns ``None`` when
    neither resolves, so the embed simply gets no author line (the same graceful
    degradation as a departed member in the passive log).
    """
    if user_id is None:
        return None
    # Lazy import: this module never imports core.runtime at module load (it
    # would re-enter a partially-loaded core.runtime during startup) — mirrors
    # resolve_log_channel below.
    from core.runtime.guild_resources import resolve_member

    member = resolve_member(guild, user_id)
    if member is not None:
        return member
    bot = _BOT
    get_user = getattr(bot, "get_user", None) if bot is not None else None
    return get_user(user_id) if get_user is not None else None


def format_log_embed(
    *,
    action: str,
    guild_id: int,
    target_id: int,
    actor_id: int | None,
    reason: str,
    extras: dict[str, Any] | None = None,
    subject: Any = None,
) -> discord.Embed:
    """Render a moderation/cleanup payload as a Discord embed.

    Unknown actions render with the generic dark-grey style so
    subscribers never blank-render a new moderation action type the
    service hasn't seen.  ``extras`` is capped at
    :data:`_MAX_EXTRA_FIELDS` slots and each value is truncated to
    :data:`_EXTRA_VALUE_CAP` chars; if more keys are supplied, a
    single ``"... truncated"`` field reports the count so the embed
    stays under Discord's 25-field / 6000-char limits.  ``subject`` (the
    resolved target member/user, when the sender could look it up) puts a
    face in the author slot, matching the passive-event embeds.
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
    _set_subject_author(embed, subject)
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
    subject: Any = None,
) -> discord.Embed:
    """Render the **public** moderation-log embed (server-management PR10).

    Deliberately narrower than :func:`format_log_embed`: it shows the action,
    the affected member, and the reason — but **never the acting moderator**
    (the maintainer's choice for the public surface) nor the internal guild id.
    The staff mod-log keeps the full record.  ``subject`` (the affected member)
    rides the author slot for the same face-per-entry look; it is the *target*,
    never the moderator, so the public surface still never reveals who acted.
    """
    root = _root_action(action)
    embed = discord.Embed(
        title=f"{_ACTION_ICON.get(root, '•')} {action}",
        color=_ACTION_COLOR.get(root, discord.Color.dark_grey()),
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    _set_subject_author(embed, subject)
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
        subject=_resolve_subject_user(guild, target_id),
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
    subject: Any = None,
) -> discord.Embed:
    """Render an ``audit.action_recorded`` payload as a Discord embed.

    Phase 9c.1 — generic audit-trail rendering. The payload contract
    matches what :func:`services.rollout_mutation._emit_audit_event`
    sends; future publishers (other mutation pipelines) MUST use the
    same field names.  ``subject`` (the resolved **actor**, when a user
    made the change) rides the author slot for the same face-per-entry
    look; a system/pipeline actor simply has no face.
    """
    embed = discord.Embed(
        title=f"📋 {mutation_type}",
        description=(
            f"`{subsystem}` · scope `{scope}`"
            + (f" · guild `{guild_id}`" if guild_id is not None else "")
        ),
        color=discord.Color.dark_teal(),
    )
    _set_subject_author(embed, subject)
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
        subject=_resolve_subject_user(guild, actor_id),
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
    embed = format_public_log_embed(
        action=action,
        target_id=target_id,
        reason=reason,
        subject=_resolve_subject_user(guild, target_id),
    )
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
    _set_subject_author(embed, author)
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
    _set_subject_author(embed, author)
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
    _set_subject_author(embed, member)
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
    _set_subject_author(embed, member)
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
    *,
    actor: Any = None,
) -> discord.Embed:
    """Render a member's role grants/revocations as a log embed.

    ``actor`` (server event logging v2) is the user who performed the change,
    resolved from the Discord audit log — when supplied it adds an **Actor**
    field so the log finally names *who* granted/revoked the role (the
    phase-2 gap called out in ``docs/server-logging.md``). Defaults to
    ``None`` (the v1 passive path never had an actor), so existing callers
    render byte-identically.
    """
    embed = discord.Embed(
        title="🎭 Roles updated",
        color=discord.Color.blurple(),
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    _set_subject_author(embed, member)
    embed.add_field(
        name="Member",
        value=f"<@{member.id}> (`{member.id}`)",
        inline=False,
    )
    if added:
        embed.add_field(
            name="➕ Added",
            value=_truncate(", ".join(_role_ref(r) for r in added)),
            inline=False,
        )
    if removed:
        embed.add_field(
            name="➖ Removed",
            value=_truncate(", ".join(_role_ref(r) for r in removed)),
            inline=False,
        )
    actor_id = getattr(actor, "id", None)
    if actor_id is not None:
        embed.add_field(name="Actor", value=f"<@{actor_id}>", inline=False)
    return embed


def _role_ref(role: Any) -> str:
    """Render a role reference that is safe for partial audit-log objects.

    A cached ``discord.Role`` renders as a ``@role`` mention; an uncached
    audit-log ``discord.Object`` has no ``.mention`` / ``.name`` and falls
    back to its id. Keeps :func:`format_role_change_embed` usable from both
    the passive path (real Roles) and the v2 audit-log path (possibly bare
    ``Object`` ids).
    """
    mention = getattr(role, "mention", None)
    if mention:
        return str(mention)
    rid = getattr(role, "id", None)
    name = getattr(role, "name", None)
    if name and rid:
        return f"{name} (`{rid}`)"
    return f"`{rid}`" if rid else str(role)


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

    Server event logging v2 categories (``moderation`` / ``channels`` /
    ``server`` / ``voice``) have **no dedicated per-category route** — they
    always resolve to the combined ``events`` channel, even in
    ``per_category`` mode. An unmapped category therefore falls back to
    ``events`` rather than returning ``None`` (which would have silently
    dropped every v2 event whenever a guild picked ``per_category`` routing).
    """
    kind = _CATEGORY_TO_ROUTE.get(category, "events") if per_category else "events"
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
# Server event logging v2 — Discord audit-log integration
# ---------------------------------------------------------------------------
#
# One gateway event — ``on_audit_log_entry_create`` — surfaces *every*
# administrative action Discord records, performed by *anyone* (a moderator
# using the native right-click menu, another bot such as Dyno, or SuperBot
# itself), with the responsible actor named. This is the layer that closes the
# "Dyno catches things we don't" gap: the pre-v2 service only heard SuperBot's
# **own** moderation actions (the ``moderation.action_taken`` bus event), so a
# ban / kick / channel-edit / role-rename done outside SuperBot was invisible.
#
# Requires the bot to hold the **View Audit Log** permission in the guild —
# without it Discord never dispatches the gateway event at all (surfaced in
# ``!logging status`` so an operator can see why the audit categories are
# silent). Every path is fail-safe like the rest of this module.

# category token → embed accent colour (imported categories kept as string
# literals here to avoid a module-level services import; a drift-guard test
# asserts every value is a real ``server_logging_config.CATEGORIES`` member).
_AUDIT_CATEGORY_COLOR: dict[str, discord.Color] = {
    "moderation": discord.Color.red(),
    "channels": discord.Color.blue(),
    "server": discord.Color.blurple(),
    "roles": discord.Color.blurple(),
    "messages": discord.Color.dark_grey(),
}

# audit-log action name → (category, icon, human verb). Keyed by
# ``AuditLogEntry.action.name`` (a stable discord.py enum-member string) so the
# map is robust across discord.py point releases and needs no enum imports.
# Actions absent from this map are simply not logged (e.g. single
# ``message_delete`` — the passive raw/cached path owns those, with content;
# ``member_role_update`` is handled specially below via the richer role embed).
_AUDIT_ACTION_META: dict[str, tuple[str, str, str]] = {
    # -- moderation ----------------------------------------------------------
    "kick": ("moderation", "👢", "Member kicked"),
    "ban": ("moderation", "🔨", "Member banned"),
    "unban": ("moderation", "🕊️", "Member unbanned"),
    "member_prune": ("moderation", "🧹", "Members pruned"),
    "member_update": ("moderation", "⏳", "Member updated"),  # verb refined at render
    "member_disconnect": ("moderation", "🔇", "Member disconnected from voice"),
    "member_move": ("moderation", "↔️", "Member moved between voice channels"),
    "automod_block_message": ("moderation", "🛡️", "AutoMod blocked a message"),
    "automod_flag_message": ("moderation", "🚩", "AutoMod flagged a message"),
    "automod_timeout_member": ("moderation", "⏳", "AutoMod timed out a member"),
    # -- roles (member grants/revocations, with actor) — special-cased ------
    "member_role_update": ("roles", "🎭", "Roles updated"),
    # -- channels ------------------------------------------------------------
    "channel_create": ("channels", "📁", "Channel created"),
    "channel_update": ("channels", "📝", "Channel updated"),
    "channel_delete": ("channels", "🗑️", "Channel deleted"),
    "overwrite_create": ("channels", "🔐", "Channel permission added"),
    "overwrite_update": ("channels", "🔐", "Channel permission updated"),
    "overwrite_delete": ("channels", "🔓", "Channel permission removed"),
    "thread_create": ("channels", "🧵", "Thread created"),
    "thread_update": ("channels", "🧵", "Thread updated"),
    "thread_delete": ("channels", "🧵", "Thread deleted"),
    "stage_instance_create": ("channels", "🎙️", "Stage started"),
    "stage_instance_update": ("channels", "🎙️", "Stage updated"),
    "stage_instance_delete": ("channels", "🎙️", "Stage ended"),
    # -- server (settings / structure) --------------------------------------
    "guild_update": ("server", "🛠️", "Server settings updated"),
    "role_create": ("server", "✨", "Role created"),
    "role_update": ("server", "🖊️", "Role updated"),
    "role_delete": ("server", "❌", "Role deleted"),
    "emoji_create": ("server", "😀", "Emoji created"),
    "emoji_update": ("server", "😀", "Emoji renamed"),
    "emoji_delete": ("server", "😶", "Emoji deleted"),
    "sticker_create": ("server", "🏷️", "Sticker created"),
    "sticker_update": ("server", "🏷️", "Sticker updated"),
    "sticker_delete": ("server", "🏷️", "Sticker deleted"),
    "webhook_create": ("server", "🪝", "Webhook created"),
    "webhook_update": ("server", "🪝", "Webhook updated"),
    "webhook_delete": ("server", "🪝", "Webhook deleted"),
    "integration_create": ("server", "🔌", "Integration added"),
    "integration_update": ("server", "🔌", "Integration updated"),
    "integration_delete": ("server", "🔌", "Integration removed"),
    "bot_add": ("server", "🤖", "Bot added"),
    "invite_create": ("server", "✉️", "Invite created"),
    "invite_update": ("server", "✉️", "Invite updated"),
    "invite_delete": ("server", "✉️", "Invite deleted"),
    "automod_rule_create": ("server", "🛡️", "AutoMod rule created"),
    "automod_rule_update": ("server", "🛡️", "AutoMod rule updated"),
    "automod_rule_delete": ("server", "🛡️", "AutoMod rule deleted"),
    "scheduled_event_create": ("server", "📅", "Event scheduled"),
    "scheduled_event_update": ("server", "📅", "Scheduled event updated"),
    "scheduled_event_delete": ("server", "📅", "Scheduled event deleted"),
    # -- messages (only actions the passive path can't see) -----------------
    "message_bulk_delete": ("messages", "🧨", "Messages bulk-deleted"),
    "message_pin": ("messages", "📌", "Message pinned"),
    "message_unpin": ("messages", "📍", "Message unpinned"),
}

# member_update audit entries cover several distinct actions; refine the verb
# from the attribute that changed so the embed title is meaningful.
_MEMBER_UPDATE_VERBS: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (
        ("timed_out_until", "communication_disabled_until"),
        "⏳",
        "Member timeout changed",
    ),
    (("nick",), "✏️", "Nickname changed"),
    (("mute",), "🔇", "Member server-mute changed"),
    (("deaf",), "🔇", "Member server-deafen changed"),
)


def _audit_ref(obj: Any) -> str:
    """Render an audit-log actor/target as ``mention (id)`` / ``name (id)`` / id.

    Handles the full range of ``entry.target`` types (Member, User, Role,
    channel, Invite, Emoji, or a bare ``discord.Object`` id) without raising on
    a partial object — the same defensive contract as :func:`_role_ref`.
    """
    if obj is None:
        return "*(none)*"
    mention = getattr(obj, "mention", None)
    oid = getattr(obj, "id", None)
    name = getattr(obj, "name", None) or getattr(obj, "code", None)
    if mention and oid is not None:
        return f"{mention} (`{oid}`)"
    if name and oid is not None:
        return f"{name} (`{oid}`)"
    if oid is not None:
        return f"`{oid}`"
    return _truncate(str(obj), 200)


def _fmt_change_value(value: Any) -> str:
    """Compactly render one before/after audit-diff value, capped for embeds."""
    if value is None:
        return "*(none)*"
    if isinstance(value, (list, tuple, set)):
        parts = [getattr(x, "name", None) or str(getattr(x, "id", x)) for x in value]
        return _truncate(", ".join(str(p) for p in parts) or "*(empty)*", 300)
    return _truncate(str(value), 300)


def _iter_diff(diff: Any) -> dict[str, Any]:
    """Best-effort ``{attr: value}`` from an ``AuditLogDiff`` (never raises)."""
    out: dict[str, Any] = {}
    try:
        for attr, val in diff:
            out[attr] = val
    except Exception:  # noqa: BLE001 — a malformed diff must not crash logging
        return {}
    return out


def _refine_member_update(entry: Any, icon: str, verb: str) -> tuple[str, str]:
    """Pick a specific icon/verb for a ``member_update`` entry by changed attr."""
    changed = set(_iter_diff(getattr(entry.changes, "before", None))) | set(
        _iter_diff(getattr(entry.changes, "after", None)),
    )
    for attrs, ricon, rverb in _MEMBER_UPDATE_VERBS:
        if changed.intersection(attrs):
            return ricon, rverb
    return icon, verb


def format_audit_log_embed(
    entry: Any,
    *,
    icon: str,
    verb: str,
    category: str,
) -> discord.Embed:
    """Render a generic ``AuditLogEntry`` as a structured log embed.

    Shows the actor (in the author slot **and** an Actor field), the affected
    target, the audit reason, and a compact before→after diff of the changed
    attributes (capped at :data:`_MAX_EXTRA_FIELDS`). Special-cased entries
    (``member_role_update``) never reach here — they use the richer role embed.
    """
    if getattr(entry, "action", None) is not None and (
        getattr(entry.action, "name", None) == "member_update"
    ):
        icon, verb = _refine_member_update(entry, icon, verb)

    actor = getattr(entry, "user", None)
    embed = discord.Embed(
        title=f"{icon} {verb}",
        color=_AUDIT_CATEGORY_COLOR.get(category, discord.Color.dark_grey()),
        timestamp=getattr(entry, "created_at", None)
        or datetime.datetime.now(tz=datetime.timezone.utc),
    )
    _set_subject_author(embed, actor)
    actor_id = getattr(actor, "id", None)
    embed.add_field(
        name="Actor",
        value=(
            f"<@{actor_id}> (`{actor_id}`)" if actor_id is not None else "*(unknown)*"
        ),
        inline=True,
    )
    embed.add_field(
        name="Target",
        value=_audit_ref(getattr(entry, "target", None)),
        inline=True,
    )

    reason = getattr(entry, "reason", None)
    if reason:
        embed.add_field(name="Reason", value=_truncate(str(reason), 1000), inline=False)

    # Compact before→after diff of the changed attributes.
    changes = getattr(entry, "changes", None)
    before = _iter_diff(getattr(changes, "before", None)) if changes is not None else {}
    after = _iter_diff(getattr(changes, "after", None)) if changes is not None else {}
    keys = list(dict.fromkeys([*before, *after]))
    shown = 0
    for key in keys:
        if shown >= _MAX_EXTRA_FIELDS:
            embed.add_field(
                name="… more",
                value=f"{len(keys) - shown} more field(s) changed.",
                inline=False,
            )
            break
        b_val = _fmt_change_value(before.get(key))
        a_val = _fmt_change_value(after.get(key))
        if b_val == a_val:
            continue
        embed.add_field(
            name=str(key)[:256],
            value=_truncate(f"{b_val} → {a_val}", _EVENT_VALUE_CAP),
            inline=False,
        )
        shown += 1

    # A few actions carry their payload in ``extra`` rather than ``changes``.
    extra = getattr(entry, "extra", None)
    extra_count = getattr(extra, "count", None) if extra is not None else None
    if extra_count is not None:
        embed.add_field(name="Count", value=str(extra_count), inline=True)
    return embed


def _build_role_update_embed(entry: Any) -> discord.Embed:
    """Render a ``member_role_update`` audit entry via the role embed (+ actor).

    discord.py exposes the removed roles as ``changes.before.roles`` and the
    added roles as ``changes.after.roles``; either may be a partial
    ``discord.Object`` list, which :func:`_role_ref` renders safely.
    """
    member = getattr(entry, "target", None)
    changes = getattr(entry, "changes", None)
    added = list(getattr(getattr(changes, "after", None), "roles", None) or [])
    removed = list(getattr(getattr(changes, "before", None), "roles", None) or [])
    return format_role_change_embed(
        member,
        added,
        removed,
        actor=getattr(entry, "user", None),
    )


async def log_audit_entry(entry: Any) -> bool:
    """Post a log embed for a Discord audit-log entry (server event logging v2).

    Categorises the entry via :data:`_AUDIT_ACTION_META`, gates on the master
    switch + the matching category flag + the ignore lists (checked against
    **both** the actor and the target so an operator can mute a noisy bot by
    adding its id to ``ignored_users``), then posts to the routed channel.
    Uncategorised actions and disabled categories are skipped; every failure
    path is counted and swallowed — a logging fault never re-enters the gateway.
    """
    guild = getattr(entry, "guild", None)
    action = getattr(entry, "action", None)
    action_name = getattr(action, "name", None)
    if guild is None or action_name is None:
        return False
    meta = _AUDIT_ACTION_META.get(action_name)
    if meta is None:
        return False  # uncategorised audit action — deliberately not logged
    category, icon, verb = meta

    from services import server_logging_config as _cfg

    try:
        policy = await _cfg.load_policy(guild.id)
        if not policy.should_log(category):
            _bump("event_skipped_disabled")
            return False
        actor_id = getattr(getattr(entry, "user", None), "id", None)
        target_id = getattr(getattr(entry, "target", None), "id", None)
        if policy.is_ignored(user_id=actor_id) or policy.is_ignored(user_id=target_id):
            _bump("event_skipped_ignored")
            return False
        if action_name == "member_role_update":
            embed = _build_role_update_embed(entry)
        else:
            embed = format_audit_log_embed(
                entry,
                icon=icon,
                verb=verb,
                category=category,
            )
        return await _post_event_embed(
            guild,
            category,
            per_category=policy.per_category,
            embed=embed,
        )
    except Exception as exc:  # noqa: BLE001 — a logging fault must never block
        _bump("subscriber_errors")
        logger.exception(
            "server_logging audit-log handler raised %s — counted and swallowed.",
            type(exc).__name__,
            exc_info=exc,
        )
        return False


# ---------------------------------------------------------------------------
# Server event logging v2 — voice state + uncached message deletions
# ---------------------------------------------------------------------------


def format_voice_state_embed(
    member: discord.Member,
    kind: str,
    before_channel: Any,
    after_channel: Any,
) -> discord.Embed:
    """Render a voice join / leave / move as a log embed.

    ``kind`` is ``"join"`` / ``"leave"`` / ``"move"``; the relevant channel
    mention(s) are shown. The moving member rides the author slot for the
    same face-per-entry look as the other event embeds.
    """
    icon, verb, color = {
        "join": ("🔊", "Joined voice", discord.Color.green()),
        "leave": ("🔈", "Left voice", discord.Color.dark_orange()),
        "move": ("↔️", "Moved voice channel", discord.Color.blurple()),
    }.get(kind, ("🎧", "Voice update", discord.Color.blurple()))
    embed = discord.Embed(
        title=f"{icon} {verb}",
        color=color,
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    _set_subject_author(embed, member)
    embed.add_field(
        name="Member",
        value=f"<@{member.id}> (`{member.id}`)",
        inline=True,
    )
    if kind == "move":
        embed.add_field(
            name="From → To",
            value=(
                f"{getattr(before_channel, 'mention', '*(unknown)*')} → "
                f"{getattr(after_channel, 'mention', '*(unknown)*')}"
            ),
            inline=False,
        )
    else:
        channel = after_channel if kind == "join" else before_channel
        embed.add_field(
            name="Channel",
            value=getattr(channel, "mention", "*(unknown)*"),
            inline=True,
        )
    return embed


async def log_voice_state(
    member: discord.Member,
    before: Any,
    after: Any,
) -> bool:
    """Post a voice join/leave/move embed when the voice category is enabled.

    Only the three channel transitions are logged — a same-channel state change
    (mute / deafen / stream toggle) is intentionally skipped to keep the voice
    log signal-dense. Fail-safe + gated + ignore-list aware via the shared gate.
    """
    from services.server_logging_config import CATEGORY_VOICE

    before_channel = getattr(before, "channel", None)
    after_channel = getattr(after, "channel", None)
    before_id = getattr(before_channel, "id", None)
    after_id = getattr(after_channel, "id", None)
    if before_channel is None and after_channel is not None:
        kind = "join"
    elif before_channel is not None and after_channel is None:
        kind = "leave"
    elif before_id != after_id:
        kind = "move"
    else:
        return False  # same channel — mute/deafen/stream toggle, not logged

    return await _log_event_if_enabled(
        getattr(member, "guild", None),
        CATEGORY_VOICE,
        lambda: format_voice_state_embed(member, kind, before_channel, after_channel),
        channel_id=after_id if kind != "leave" else before_id,
        user_id=getattr(member, "id", None),
    )


def format_uncached_message_delete_embed(
    channel_id: int | None,
    message_id: int,
) -> discord.Embed:
    """Render the fallback embed for a deleted message that was not cached.

    The passive ``on_message_delete`` path only fires for messages in the
    client cache, so an older/post-restart delete produced no log at all
    (a v1 gap). The raw path catches it, but Discord gives no content for an
    uncached message — so this embed records the *event* (channel + id) with
    the content marked unavailable, rather than dropping it silently. A raw
    ``<#id>`` still resolves to a channel link in the client with no cached
    channel object required.
    """
    embed = discord.Embed(
        title="🗑️ Message deleted",
        color=discord.Color.red(),
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    embed.add_field(
        name="Channel",
        value=f"<#{channel_id}>" if channel_id is not None else "*(unknown)*",
        inline=True,
    )
    embed.add_field(name="Message ID", value=f"`{message_id}`", inline=True)
    embed.add_field(
        name="Content",
        value="*(unavailable — message was not in the bot's cache)*",
        inline=False,
    )
    return embed


async def log_uncached_message_delete(
    guild: discord.Guild | None,
    channel_id: int | None,
    message_id: int,
) -> bool:
    """Log an uncached message deletion under the messages category.

    Complements — never duplicates — the passive ``on_message_delete`` path:
    the raw listener only calls this when ``payload.cached_message is None``
    (so the cached path did not, and will not, fire for this id).
    """
    from services.server_logging_config import CATEGORY_MESSAGES

    return await _log_event_if_enabled(
        guild,
        CATEGORY_MESSAGES,
        lambda: format_uncached_message_delete_embed(channel_id, message_id),
        channel_id=channel_id,
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
    "format_audit_log_embed",
    "format_log_embed",
    "format_member_join_embed",
    "format_member_leave_embed",
    "format_message_delete_embed",
    "format_message_edit_embed",
    "format_public_log_embed",
    "format_role_change_embed",
    "format_uncached_message_delete_embed",
    "format_voice_state_embed",
    "is_enabled",
    "log_audit_entry",
    "log_audit_event",
    "log_event",
    "log_member_join",
    "log_member_leave",
    "log_message_delete",
    "log_message_edit",
    "log_role_change",
    "log_uncached_message_delete",
    "log_voice_state",
    "maybe_log_public",
    "resolve_event_channel",
    "resolve_log_channel",
    "setup",
]
