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
      10. Platform migration checkpoints — drop per-guild checkpoint rows
                                   (Phase 2 PR-5); global rows preserved.
      11. Per-user participation tables — delete user_participation /
                                   user_subscriptions / user_preferences /
                                   user_visibility_overrides rows scoped to
                                   this guild (Phase 2c PR-8).  Same user's
                                   rows in OTHER guilds are preserved.
      12. User-config cache      — drop cached per-(user, guild) bundles
                                   (Phase 2c PR-8).
      13. Governance capability cache — clear per-guild execution overrides.
      14. Governance visibility cache — bump version, clear role-override flag.
      15. Guild-config cache    — drop cached guild config entries (F-1).
      16. Scope locks           — invoke registered per-cog teardown hooks (F-2).
      17. Governance feedback cooldown — documented, no per-guild cleanup needed.
      18. Setup session         — delete the setup_session row (Phase 9e PR 8).
                                   The launcher cog re-creates it on the next
                                   on_guild_join.
      19. Automation rules      — delete every automation_rules row for the
                                   guild (Phase 9g PR 18). ``automation_runs``
                                   rows are removed via ON DELETE CASCADE.
      20. AI Platform           — drop every per-guild row across the six M2
                                   tables; invalidate resolver cache + drop
                                   conversation buffers.
      21. BTD6 strategies (M4)  — delete guild-local rows; detach published
                                   rows so attribution survives.
      22. Command-access policy — drop both the cached snapshot and the
                                   ``guild_command_access_policy`` row
                                   (CASCADE sweeps the channel allowlist).
      23. Role menus            — delete every ``role_menus`` row for the
                                   guild (reaction-roles overhaul);
                                   ``role_menu_options`` rows cascade via FK.
                                   The legacy ``reaction_roles`` table is
                                   handled by its own step (30) — it is
                                   guild-scoped and does NOT self-clean.
      28. Role thresholds       — delete every ``role_thresholds`` row for the
                                   guild (time + XP automation tiers).
      29. Role-automation exemptions — delete every
                                   ``role_automation_exemptions`` row.
      30. Reaction roles        — delete every ``reaction_roles`` row for the
                                   guild; not message-delete-cleaned.
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

    # 10. Platform migration checkpoints — per-guild rows only (Phase 2 PR-5).
    await _teardown_platform_migration_checkpoints(guild_id)

    # 11. Per-user participation tables — drop user_*/visibility rows scoped
    #     to this guild only (Phase 2c PR-8).
    await _teardown_user_participation(guild_id)

    # 12. User-config cache — drop cached (user, guild) bundles for this guild.
    _teardown_user_config_cache(guild_id)

    # 13. Governance capability overrides — clear execution-layer in-process dict.
    _teardown_capability_overrides(guild_id)

    # 14. Governance visibility cache — version bump + role flag removal.
    _teardown_visibility_cache(guild_id)

    # 15. Guild-config cache — drop cached config entries for the guild (F-1 / S1.1).
    _teardown_guild_config(guild_id)

    # 16. Scope locks — invoke registered per-cog teardown hooks (F-2 / S1.2).
    _teardown_scope_locks(guild_id)

    # 17. Governance feedback cooldown dict in governance/__init__.
    _teardown_feedback_cooldown(guild_id)

    # 18. Setup session row (Phase 9e PR 8). The launcher cog re-creates
    #     it via ``services.setup_session.start_session`` on the next
    #     ``on_guild_join``.
    await _teardown_setup_session(guild_id)

    # 19. Automation rules (Phase 9g PR 18). ``automation_runs`` rows
    #     get cleaned up by the ON DELETE CASCADE on rule_id.
    await _teardown_automation_rules(guild_id)

    # 20. AI Platform — drop every per-guild row across the six M2
    #     tables (instruction profile / guild policy / channel /
    #     category / role / decision audit). Global instruction
    #     profiles (guild_id IS NULL) are preserved. Process-local
    #     conversation buffers also get dropped.
    await _teardown_ai_platform(guild_id)

    # 21. BTD6 strategies (M4) — guild-local rows are deleted;
    #     published rows survive (current_guild_id flips to NULL,
    #     origin_guild_id + origin_metadata preserved for
    #     attribution).
    await _teardown_btd6_strategies(guild_id)

    # 22. Command-access policy (command-access onboarding PR-3) —
    #     drop both the cached typed-accessor entry and the
    #     ``guild_command_access_policy`` row (CASCADE sweeps the
    #     child ``guild_command_access_channels`` rows).  Paired in
    #     ``core.runtime.command_access.forget_guild`` so the cache
    #     and the DB never diverge across a re-invite.
    await _teardown_command_access(guild_id)

    # 23. Role menus (reaction-roles overhaul) — delete role_menus rows;
    #     role_menu_options cascade via the FK.
    await _teardown_role_menus(guild_id)

    # 24. Reaction-role message modes (overhaul PR 3) — per-message
    #     normal/unique/verify rows for the legacy emoji surface.
    await _teardown_reaction_modes(guild_id)

    # 25. Temporary role grants (overhaul PR 4) — pending temp-role rows for
    #     the departed guild (the role itself goes with the guild).
    await _teardown_role_grants(guild_id)

    # 26. Role-pickup analytics (overhaul PR 5) — aggregate (guild, role)
    #     pickup counters for the departed guild.
    await _teardown_role_pickup_stats(guild_id)

    # 27. Starboard / Hall-of-Fame (idea B1) — settings + entries for the
    #     departed guild.
    await _teardown_starboard(guild_id)

    # 28. Role thresholds (time + XP automation tiers) — guild-scoped rows
    #     with no other cleanup anchor.
    await _teardown_role_thresholds(guild_id)

    # 29. Role-automation exemptions — per-(guild, role) exemption rows.
    await _teardown_role_exemptions(guild_id)

    # 30. Reaction roles — guild-scoped emoji→role bindings. These do NOT
    #     self-clean on message delete, so an explicit purge is required.
    await _teardown_reaction_roles(guild_id)

    # 31. Proof-channel timed locks — persisted unlock deadlines (bug #8).
    await _teardown_proof_channel_locks(guild_id)

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


async def _teardown_platform_migration_checkpoints(guild_id: int) -> None:
    """Delete per-guild ``platform_migration_checkpoints`` rows.

    Phase 2 PR-5.  Global rows (``guild_id IS NULL``) are preserved so
    cross-guild migration metadata survives an individual guild leave.
    A re-invited guild starts with no checkpoint history; running the
    binding-backfill dry-run again will write a fresh row.
    """
    try:
        from utils.db.platform_migration_checkpoints import (
            delete_for_guild as _checkpoint_delete,
        )

        count = await _checkpoint_delete(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d migration checkpoint row(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: platform migration checkpoint teardown failed: %s",
            exc,
        )


async def _teardown_user_participation(guild_id: int) -> None:
    """Delete per-user participation rows scoped to the departed guild.

    Phase 2c PR-8.  Drops rows in user_participation, user_subscriptions,
    user_preferences, and user_visibility_overrides whose ``guild_id``
    matches.  The same user's rows in OTHER guilds are preserved.
    """
    try:
        from utils.db.user_participation import (
            delete_for_guild as _participation_delete,
        )

        count = await _participation_delete(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d user participation row(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: user participation teardown failed: %s",
            exc,
        )


def _teardown_user_config_cache(guild_id: int) -> None:
    """Drop cached per-(user, guild) participation bundles for ``guild_id``.

    Phase 2c PR-8.  Symmetric to ``_teardown_feature_flag_cache`` —
    keeps cache and DB consistent on guild leave.
    """
    try:
        from core.runtime.user_config import forget_guild as _user_cache_forget

        dropped = _user_cache_forget(guild_id)
        if dropped:
            logger.debug(
                "guild_lifecycle: dropped %d user_config cache entry(s) for guild=%d",
                dropped,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: user_config cache teardown failed: %s",
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


async def _teardown_setup_session(guild_id: int) -> None:
    """Delete the ``setup_session`` row for the departed guild.

    Phase 9e PR 8. The launcher cog re-creates the row via
    :func:`services.setup_session.start_session` on the next
    ``on_guild_join``, so per-guild state is bounded.
    """
    try:
        from utils.db import setup_session as db

        await db.clear(guild_id)
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: setup_session teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )


async def _teardown_automation_rules(guild_id: int) -> None:
    """Delete every automation_rules row for the departed guild.

    Phase 9g PR 18. ``automation_runs`` history rows cascade away
    via the FK; nothing else references the rules.
    """
    try:
        from utils.db import automation as db

        count = await db.delete_rules_for_guild(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d automation rule(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: automation_rules teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )


async def _teardown_command_access(guild_id: int) -> None:
    """Drop the guild's command-access policy + cached snapshot.

    Wraps :func:`core.runtime.command_access.forget_guild`, which
    invalidates the typed-accessor cache entry and then runs
    ``DELETE FROM guild_command_access_policy WHERE guild_id = $1``.
    The CASCADE on ``guild_command_access_channels`` sweeps the child
    rows; no separate step needed for the allowlist.
    """
    try:
        from core.runtime.command_access import forget_guild as _ca_forget

        await _ca_forget(guild_id)
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: command_access teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )


async def _teardown_btd6_strategies(guild_id: int) -> None:
    """Drop guild-local BTD6 strategies; detach published rows.

    M4 retention rule: ``visibility='guild'`` rows are removed.
    ``visibility='published'`` rows are RETAINED with
    ``current_guild_id`` set to NULL — ``origin_guild_id`` and
    ``origin_metadata`` stay so attribution survives the guild
    leaving. Submitter anonymisation is a separate privacy path
    routed through ``btd6_strategy_mutation.anonymise_submitter``.
    """
    try:
        from utils.db import btd6_strategies as db

        deleted = await db.delete_guild_local_for_guild(guild_id)
        detached = await db.detach_published_from_guild(guild_id)
        if deleted or detached:
            logger.debug(
                "guild_lifecycle: btd6 strategies — deleted %d guild-local, "
                "detached %d published for guild=%d",
                deleted,
                detached,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: btd6 strategy teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )


async def _teardown_ai_platform(guild_id: int) -> None:
    """Drop every AI Platform row scoped to ``guild_id``.

    M2 of the BTD6 + AI-central-policy initiative. Sweeps the six
    typed tables (``ai_guild_policy``, ``ai_channel_policy``,
    ``ai_category_policy``, ``ai_role_policy``,
    ``ai_decision_audit``, and per-guild ``ai_instruction_profile``
    rows). Global instruction profiles (``guild_id IS NULL``) are
    preserved. Also invalidates the resolver cache and drops the
    process-local conversation buffers AND the permission-service
    cooldown / fresh-allowance trackers for the guild.
    """
    try:
        from services import (
            ai_conversation_service,
            ai_natural_language_policy,
            ai_permission_service,
        )
        from utils.db import ai as ai_db

        deleted = await ai_db.delete_for_guild(guild_id)
        ai_natural_language_policy.invalidate(guild_id)
        ai_conversation_service.forget_guild(guild_id)
        ai_permission_service.forget_guild(guild_id)
        if deleted:
            logger.debug(
                "guild_lifecycle: deleted %d AI Platform row(s) for guild=%d",
                deleted,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: AI Platform teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )


async def _teardown_role_menus(guild_id: int) -> None:
    """Delete every role_menus row for the departed guild (reaction-roles overhaul).

    ``role_menu_options`` rows cascade away via the FK. The legacy
    ``reaction_roles`` table is guild-scoped and is purged by its own teardown
    step (:func:`_teardown_reaction_roles`); it does NOT self-clean on message
    delete.
    """
    try:
        from utils.db.role_menus import delete_for_guild as _role_menus_delete

        count = await _role_menus_delete(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d role menu(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: role menu teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )


async def _teardown_starboard(guild_id: int) -> None:
    """Delete starboard settings + entries for the departed guild (idea B1)."""
    try:
        from utils.db.starboard import delete_for_guild as _starboard_delete

        count = await _starboard_delete(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d starboard entr(ies) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: starboard teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )


async def _teardown_reaction_modes(guild_id: int) -> None:
    """Delete per-message reaction modes for the departed guild (overhaul PR 3).

    The legacy ``reaction_roles`` bindings self-clean when the host messages are
    deleted; their per-message mode rows have no such anchor, so they need an
    explicit teardown step.
    """
    try:
        from utils.db import delete_reaction_modes_for_guild

        count = await delete_reaction_modes_for_guild(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d reaction-mode row(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: reaction-mode teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )


async def _teardown_role_grants(guild_id: int) -> None:
    """Delete every temporary role-grant row for the departed guild (PR 4)."""
    try:
        from utils.db.role_grants import delete_for_guild as _grants_delete

        count = await _grants_delete(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d role-grant row(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: role-grant teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )


async def _teardown_role_pickup_stats(guild_id: int) -> None:
    """Delete role-pickup analytics rows for the departed guild (PR 5)."""
    try:
        from utils.db.role_menus import delete_pickup_stats_for_guild

        count = await delete_pickup_stats_for_guild(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d pickup-stat row(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: pickup-stat teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )


async def _teardown_role_thresholds(guild_id: int) -> None:
    """Delete every ``role_thresholds`` row for the departed guild (teardown gap fix)."""
    try:
        from utils.db.roles import delete_role_thresholds_for_guild

        count = await delete_role_thresholds_for_guild(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d role-threshold row(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: role-threshold teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )


async def _teardown_role_exemptions(guild_id: int) -> None:
    """Delete every ``role_automation_exemptions`` row for the departed guild."""
    try:
        from utils.db.roles import delete_role_exemptions_for_guild

        count = await delete_role_exemptions_for_guild(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d role-exemption row(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: role-exemption teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )


async def _teardown_reaction_roles(guild_id: int) -> None:
    """Delete every ``reaction_roles`` row for the departed guild.

    ``reaction_roles`` is guild-scoped and has no message-delete cleanup path, so
    without this step its rows persist forever after guild-leave.
    """
    try:
        from utils.db.roles import delete_reaction_roles_for_guild

        count = await delete_reaction_roles_for_guild(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d reaction-role row(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: reaction-role teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )


async def _teardown_proof_channel_locks(guild_id: int) -> None:
    """Delete every persisted proof-channel timed lock for the departed guild."""
    try:
        from utils.db.proof_channel_locks import delete_for_guild as _proof_delete

        count = await _proof_delete(guild_id)
        if count:
            logger.debug(
                "guild_lifecycle: deleted %d proof-channel lock(s) for guild=%d",
                count,
                guild_id,
            )
    except Exception as exc:
        logger.warning(
            "guild_lifecycle: proof-channel lock teardown failed for guild=%d: %s",
            guild_id,
            exc,
        )
