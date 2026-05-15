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
      1. Live update scheduler — stop sending edits for the guild's channels.
      2. Runtime sessions      — delete DB sessions + cascade session_state rows.
      3. Session state store   — any remaining orphan state rows for the guild.
      4. Governance capability cache — clear per-guild execution overrides.
      5. Governance visibility cache — bump version, clear role-override flag.
      6. Governance feedback cooldown — clear governance/__init__ rate-limit dict.
    """
    logger.info("guild_lifecycle.teardown: beginning cleanup for guild=%d", guild_id)

    # 1. Live update scheduler — remove _last_edit throttle entries for the guild.
    _teardown_scheduler(guild_id)

    # 2. Runtime sessions — delete from DB (cascades to runtime_session_state).
    await _teardown_sessions(guild_id)

    # 3. Session state store — purge any orphan state rows not caught by cascade.
    await _teardown_session_state(guild_id)

    # 4. Governance capability overrides — clear execution-layer in-process dict.
    _teardown_capability_overrides(guild_id)

    # 5. Governance visibility cache — version bump + role flag removal.
    _teardown_visibility_cache(guild_id)

    # 6. Governance feedback cooldown dict in governance/__init__.
    _teardown_feedback_cooldown(guild_id)

    logger.info("guild_lifecycle.teardown: complete for guild=%d", guild_id)


# ---------------------------------------------------------------------------
# Individual teardown steps
# ---------------------------------------------------------------------------


def _teardown_scheduler(guild_id: int) -> None:
    """Remove _last_edit rate-limit entries for all channels in the guild.

    We do not have a guild→channels mapping in memory, so we cannot enumerate
    channels directly.  Instead, we rely on the GC / on_guild_remove pattern:
    next time a panel refresh is attempted for a stale channel it will fail
    gracefully.  We reset the _last_edit dict entirely if the entry count is
    small; for large deployments the scheduled panel edits will simply produce
    no-ops (channel not found / bot not in guild).

    A future improvement: track guild_id in the scheduler's _last_edit dict
    keyed as (guild_id, channel_id) to allow precise cleanup.
    """
    try:
        from core.runtime.live_update_scheduler import _last_edit

        # Purge all entries; the dict will refill only for active channels.
        # This is safe because _last_edit is only a rate-limit hint.
        if len(_last_edit) < 5_000:
            _last_edit.clear()
            logger.debug("Scheduler _last_edit cleared for guild=%d", guild_id)
    except Exception as exc:
        logger.warning("guild_lifecycle: scheduler teardown failed: %s", exc)


async def _teardown_sessions(guild_id: int) -> None:
    """Delete all runtime sessions for the guild from the DB."""
    try:
        from utils import db

        result = await db.get().execute(
            "DELETE FROM runtime_sessions WHERE guild_id = $1", guild_id
        )
        count = _parse_pg_count(result)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d session(s) for guild=%d", count, guild_id
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


def _parse_pg_count(result: str) -> int:
    try:
        return int(result.split()[-1])
    except (IndexError, ValueError):
        return 0
