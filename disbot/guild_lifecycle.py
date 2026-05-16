"""Unified guild lifecycle management.

Centralises all cleanup that must happen when the bot leaves a guild, so that
no module accumulates permanent per-guild state indefinitely.

Every module that owns guild-scoped in-process state must be represented here.
The teardown sequence is ordered to clear higher-level state before lower-level
dependencies (runtime before governance cache before DB-level cleanup).

Public surface:
    teardown(guild_id) → None  — call from bot1.on_guild_remove
"""

from __future__ import annotations

import logging

logger = logging.getLogger("bot.guild_lifecycle")


async def teardown(guild_id: int) -> None:
    """Purge ALL in-process and DB state owned by a guild.

    Called from on_guild_remove.  Safe to call even if the guild was never
    fully initialised (all operations are no-ops on missing keys).

    Teardown order (high-level → low-level):
      1. Live update scheduler  — drop _last_edit throttle entries for the guild.
      2. Runtime sessions       — delete DB sessions + cascade session_state rows.
      3. Session state store    — remaining orphan state rows for the guild.
      4. Panel anchors          — delete all panel_anchors rows for the guild.
      5. Governance capability cache — clear per-guild execution overrides.
      6. Governance visibility cache — bump version, clear role-override flag.
      7. Governance feedback cooldown — documented, no per-guild cleanup needed.
    """
    logger.info("guild_lifecycle.teardown: beginning cleanup for guild=%d", guild_id)

    # 1. Live update scheduler — remove _last_edit throttle entries for the guild.
    _teardown_scheduler(guild_id)

    # 2. Runtime sessions — delete from DB (cascades to runtime_session_state).
    await _teardown_sessions(guild_id)

    # 3. Session state store — purge any orphan state rows not caught by cascade.
    await _teardown_session_state(guild_id)

    # 4. Panel anchors — delete all panel_anchors rows for the guild (GAP-001).
    await _teardown_panel_anchors(guild_id)

    # 5. Governance capability overrides — clear execution-layer in-process dict.
    _teardown_capability_overrides(guild_id)

    # 6. Governance visibility cache — version bump + role flag removal.
    _teardown_visibility_cache(guild_id)

    # 7. Governance feedback cooldown dict in governance/__init__.
    _teardown_feedback_cooldown(guild_id)

    logger.info("guild_lifecycle.teardown: complete for guild=%d", guild_id)


# ---------------------------------------------------------------------------
# Individual teardown steps
# ---------------------------------------------------------------------------


def _teardown_scheduler(guild_id: int) -> None:
    """Drop _last_edit rate-limit entries for the departed guild.

    Always runs — no size-gated bypass (DEBT-006).  The scheduler keys
    _last_edit by (guild_id, channel_id) so cleanup is deterministic and
    isolated to the departed guild's channels.
    """
    try:
        from core.runtime.live_update_scheduler import forget_guild as _sched_forget

        removed = _sched_forget(guild_id)
        if removed:
            logger.debug(
                "Scheduler _last_edit purged %d entries for guild=%d",
                removed,
                guild_id,
            )
    except Exception as exc:
        logger.warning("guild_lifecycle: scheduler teardown failed: %s", exc)


async def _teardown_sessions(guild_id: int) -> None:
    """Delete all runtime sessions for the guild from the DB.

    PR N1: uses ``db.delete_sessions_for_guild`` so the returned IDs can
    feed ``navigation_stack.forget``.  The previous raw DELETE returned
    only a Postgres command tag; the per-session lock dict would have
    accumulated stale entries for departed guilds.
    """
    try:
        from core.runtime import navigation_stack
        from utils import db

        removed_ids = await db.delete_sessions_for_guild(guild_id)
        for sid in removed_ids:
            navigation_stack.forget(sid)
        if removed_ids:
            logger.debug(
                "guild_lifecycle: deleted %d session(s) for guild=%d",
                len(removed_ids),
                guild_id,
            )
    except Exception as exc:
        logger.warning("guild_lifecycle: session teardown failed: %s", exc)


async def _teardown_session_state(guild_id: int) -> None:
    """Purge orphan session state rows for the guild."""
    try:
        from utils import db

        await db.delete_guild_session_state(guild_id)
    except Exception as exc:
        logger.warning("guild_lifecycle: session state teardown failed: %s", exc)


async def _teardown_panel_anchors(guild_id: int) -> None:
    """Delete all panel_anchors rows for the departed guild (GAP-001).

    Without this step, panel anchors for departed guilds accumulate
    indefinitely in the DB.  Index idx_panel_anchors_guild (migration 013)
    supports the DELETE.
    """
    try:
        from utils import db

        count = await db.delete_guild_panel_anchors(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d panel anchor(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning("guild_lifecycle: panel anchor teardown failed: %s", exc)


def _teardown_capability_overrides(guild_id: int) -> None:
    """Clear execution-layer capability override cache for the guild."""
    try:
        from governance.execution import forget_guild_capabilities

        forget_guild_capabilities(guild_id)
    except Exception as exc:
        logger.warning("guild_lifecycle: capability override teardown failed: %s", exc)


def _teardown_visibility_cache(guild_id: int) -> None:
    """Clear governance visibility cache for the guild."""
    try:
        from governance.cache import forget_guild

        forget_guild(guild_id)
    except Exception as exc:
        logger.warning("guild_lifecycle: visibility cache teardown failed: %s", exc)


def _teardown_feedback_cooldown(guild_id: int) -> None:
    """Clear governance command-feedback rate-limit entries for the guild.

    governance/__init__._FEEDBACK_COOLDOWN is keyed by (channel_id, subsystem).
    We cannot enumerate guild→channel IDs here so we skip targeted cleanup;
    entries expire naturally after _FEEDBACK_COOLDOWN_SECS (10 s).
    The dict's own size guard (>500 entries → purge expired) handles unbounded
    growth without per-guild teardown.
    """
