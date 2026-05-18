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
      5. Subsystem bindings     — delete active subsystem_bindings rows (Phase 2);
                                   binding_audit_log rows are PRESERVED by design.
      6. Resource validation cache — drop resource_validation_cache rows (Phase 2).
      7. Feature flag per-guild overrides — drop feature_flag_guild_overrides
                                   rows (Phase 2d PR-2); global rows preserved.
      8. Environment tier        — delete environment_tiers row (Phase 2d PR-2).
      9. Feature flag evaluator cache — drop cached decisions for the guild.
      10. Governance capability cache — clear per-guild execution overrides.
      11. Governance visibility cache — bump version, clear role-override flag.
      12. Guild-config cache    — drop cached guild config entries (F-1).
      13. Scope locks           — invoke registered per-cog teardown hooks (F-2).
      14. Governance feedback cooldown — documented, no per-guild cleanup needed.
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

    # 5. Subsystem bindings active rows — audit log preserved (Phase 2 retention).
    await _teardown_subsystem_bindings(guild_id)

    # 6. Resource validation cache — drop cached resource status rows (Phase 2a).
    await _teardown_resource_cache(guild_id)

    # 7. Feature flag per-guild overrides — global rows preserved (Phase 2d).
    await _teardown_feature_flag_guild_overrides(guild_id)

    # 8. Environment tier row — guild defaults back to production on re-join.
    await _teardown_environment_tier(guild_id)

    # 9. Feature flag evaluator cache — drop stale cached decisions.
    _teardown_feature_flag_cache(guild_id)

    # 10. Governance capability overrides — clear execution-layer in-process dict.
    _teardown_capability_overrides(guild_id)

    # 11. Governance visibility cache — version bump + role flag removal.
    _teardown_visibility_cache(guild_id)

    # 12. Guild-config cache — drop cached config entries for the guild (F-1 / S1.1).
    _teardown_guild_config(guild_id)

    # 13. Scope locks — invoke registered per-cog teardown hooks (F-2 / S1.2).
    _teardown_scope_locks(guild_id)

    # 14. Governance feedback cooldown dict in governance/__init__.
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


async def _teardown_subsystem_bindings(guild_id: int) -> None:
    """Delete active subsystem_bindings rows for the departed guild.

    Phase 2 retention policy: ``binding_audit_log`` is **preserved** on
    guild leave so the historical trail survives re-invitation.  This
    teardown step calls ``delete_active_bindings_for_guild`` — the
    deliberately-split primitive that touches only the active table.
    A separate ``purge_binding_audit_for_guild`` primitive exists for
    explicit forensic cleanup but is NOT invoked here.
    """
    try:
        from utils.db.bindings import delete_active_bindings_for_guild

        count = await delete_active_bindings_for_guild(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d active binding(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning("guild_lifecycle: bindings teardown failed: %s", exc)


async def _teardown_resource_cache(guild_id: int) -> None:
    """Drop resource_validation_cache rows for the departed guild.

    Phase 2a hardening shipped the ``delete_for_guild`` primitive; this
    step wires it into the lifecycle.  Resource cache rows are pure
    derived state (recomputable from Discord), so deletion is safe and
    avoids unbounded growth across re-invitations.
    """
    try:
        from utils.db.resource_cache import delete_for_guild as _resource_delete

        count = await _resource_delete(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d resource cache row(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning("guild_lifecycle: resource cache teardown failed: %s", exc)


async def _teardown_feature_flag_guild_overrides(guild_id: int) -> None:
    """Delete every feature_flag_guild_overrides row for the departed guild.

    Phase 2d, PR-2.  Global override rows survive (they're not scoped to
    a single guild); only the per-guild rows are purged.  Operators can
    re-seed canary/owner overrides after re-invitation.
    """
    try:
        from utils.db.feature_flag_state import delete_for_guild as _ff_delete

        count = await _ff_delete(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d feature_flag guild override(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: feature_flag guild override teardown failed: %s",
            exc,
        )


async def _teardown_environment_tier(guild_id: int) -> None:
    """Drop the environment_tiers row so the guild re-defaults to PRODUCTION.

    Phase 2d, PR-2.  When the bot is re-invited, the guild starts at the
    most restrictive tier until an operator re-assigns it.
    """
    try:
        from utils.db.environment_tiers import delete_for_guild as _et_delete

        count = await _et_delete(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted environment_tier row for guild=%d",
                guild_id,
            )
    except Exception as exc:
        logger.warning("guild_lifecycle: environment_tier teardown failed: %s", exc)


def _teardown_feature_flag_cache(guild_id: int) -> None:
    """Drop every evaluator cache entry scoped to ``guild_id``.

    Phase 2d, PR-2.  Until PR-3 wires event-driven invalidation, the
    explicit clear on guild-leave guarantees a re-invited guild does
    not observe stale per-guild decisions.
    """
    try:
        from core.runtime.feature_flags import clear_cache

        removed = clear_cache(guild_id=guild_id)
        if removed:
            logger.debug(
                "guild_lifecycle: cleared %d feature_flag cache entry(s) for guild=%d",
                removed,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: feature_flag cache teardown failed: %s",
            exc,
        )


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


def _teardown_guild_config(guild_id: int) -> None:
    """Clear F-1 guild-config cache entries for the departed guild.

    Symmetric to ``_teardown_visibility_cache`` above — same lifetime,
    same teardown discipline.  The primitive lives in
    ``core/runtime/guild_config.py`` (Phase S1.1).
    """
    try:
        from core.runtime.guild_config import forget_guild as _gc_forget

        _gc_forget(guild_id)
    except Exception as exc:
        logger.warning("guild_lifecycle: guild_config teardown failed: %s", exc)


def _teardown_scope_locks(guild_id: int) -> None:
    """Invoke registered F-2 scope_locks per-guild teardown hooks.

    Unlike caches keyed by ``guild_id``, ``scope_locks`` keys are
    caller-defined strings (``counting:channel:{cid}``,
    ``tournament:{tid}``, …) — the primitive cannot know which scopes
    belong to a given guild.  Each cog that uses ``scope_locks``
    registers a hook via ``scope_locks.register_guild_teardown_hook``
    at ``cog_load`` time; this teardown step fans out to all of them.

    In Phase S1.2 (this PR) no cogs register hooks yet — counting
    registers its hook in S2.1.  The teardown step is in place so
    ``session_gc.sweep_idle`` is the only fallback for *missed*
    forget calls, not the only cleanup path for guild_remove.
    """
    try:
        from core.runtime.scope_locks import teardown_guild

        removed = teardown_guild(guild_id)
        if removed:
            logger.debug(
                "guild_lifecycle: dropped %d scope_lock(s) for guild=%d",
                removed,
                guild_id,
            )
    except Exception as exc:
        logger.warning("guild_lifecycle: scope_locks teardown failed: %s", exc)


def _teardown_feedback_cooldown(guild_id: int) -> None:
    """Clear governance command-feedback rate-limit entries for the guild.

    governance/__init__._FEEDBACK_COOLDOWN is keyed by (channel_id, subsystem).
    We cannot enumerate guild→channel IDs here so we skip targeted cleanup;
    entries expire naturally after _FEEDBACK_COOLDOWN_SECS (10 s).
    The dict's own size guard (>500 entries → purge expired) handles unbounded
    growth without per-guild teardown.
    """
