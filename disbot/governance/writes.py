"""Governance write operations — all mutations flow through GovernanceMutationPipeline.

Layer: models → ... → health → writes.
Imports from governance.models, governance.events, governance.cache.

Architecture
────────────
All governance state changes must pass through GovernanceMutationPipeline, which
enforces a deterministic sequence:

  1. Input validation
  2. Authority validation (SEC-001 — infrastructure boundary, not cog-level)
  3. Read old value from DB (for full audit trail)
  4. DB write + audit in a single transaction
  5. In-memory cache invalidation
  6. Event emission (EVT_VISIBILITY_CHANGED + EVT_CACHE_INVALIDATED)

Ad-hoc governance writes that bypass the pipeline are prohibited.  The pipeline
is the single orchestration point — partial or out-of-order side effects are not
permitted.

Phase 3.3 — Structured event payloads
Each event payload includes mutation_id and occurred_at for replay-readiness.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from config import is_platform_owner
from governance.cache import invalidate_guild_cache
from governance.events import (
    EVT_CACHE_INVALIDATED,
    EVT_CLEANUP_CHANGED,
    EVT_VISIBILITY_CHANGED,
    _emit_governance_event,
)
from governance.models import GovernanceContext
from governance.scopes import (
    VALID_CLEANUP_SCOPE_TYPES,
    VALID_VISIBILITY_SCOPE_TYPES,
)
from services.audit_events import emit_audit_action
from utils import db, settings_keys
from utils.governance_exceptions import (
    GovernanceError,
    UnauthorizedGovernanceWriteError,
)
from utils.subsystem_registry import REGISTRY_VERSION, SUBSYSTEMS
from utils.visibility_rules import get_member_visibility_tier, is_tier_sufficient

logger = logging.getLogger("bot")

# Scope types accepted by the pipeline.  The canonical, read-side definitions
# live in ``governance.scopes`` (so diagnostics/explainers can consume them
# without importing this mutation module — RC-8A dependency-direction fix);
# these module-private aliases keep the existing write-validation call sites and
# the RC-5 test stable.
#
# RC-5: visibility and cleanup do NOT share a scope set.
#   * subsystem_visibility gained "thread" in migration 009 and the resolver
#     walks thread → channel → category → guild, so visibility overrides may be
#     thread-scoped.
#   * cleanup_policies deliberately kept its non-thread CHECK constraint in that
#     same migration and the cleanup resolver (governance/cleanup.py) skips
#     thread scope, so a thread cleanup write would pass service validation only
#     to be rejected late by Postgres.  Reject it here, before the DB.
_VALID_VISIBILITY_SCOPE_TYPES = VALID_VISIBILITY_SCOPE_TYPES
_VALID_CLEANUP_SCOPE_TYPES = VALID_CLEANUP_SCOPE_TYPES

# Minimum tier required to mutate governance state.
_WRITE_AUTHORITY_TIER = "moderator"


def _validate_authority(ctx: GovernanceContext) -> None:
    """Assert the calling member has sufficient authority for governance writes.

    This is an infrastructure boundary check — it runs even if the cog layer
    has already validated permissions.  The governance pipeline must never rely
    solely on caller discipline.

    Raises UnauthorizedGovernanceWriteError on insufficient authority.
    """
    if ctx.member is None:
        raise UnauthorizedGovernanceWriteError(
            "Governance writes require a guild member context (member is None).",
        )
    # Platform-owner override: the configured bot owner
    # (config.BOT_OWNER_USER_ID / PermissionTier.PLATFORM_OWNER) may mutate
    # governance state (e.g. per-channel subsystem visibility) in any guild they
    # are a member of, so they can configure where the bot operates even without
    # Discord perms there.  ctx.member is a member of the target guild, so this
    # preserves the "authority bound to the write target" invariant.
    if is_platform_owner(ctx.member.id):
        return
    guild_owner_id = ctx.member.guild.owner_id if ctx.member.guild else 0
    tier = get_member_visibility_tier(ctx.member, guild_owner_id)
    if not is_tier_sufficient(tier, _WRITE_AUTHORITY_TIER):
        raise UnauthorizedGovernanceWriteError(
            f"Member {ctx.member.id!r} (tier={tier!r}) requires at least "
            f"{_WRITE_AUTHORITY_TIER!r} to mutate governance state.",
        )


class GovernanceMutationPipeline:
    """Centralized orchestration for all governance state mutations.

    Instances are stateless — create one per mutation request.

    All public write functions (set_subsystem_visibility,
    set_cleanup_policy_for_scope) delegate to this class so the complete
    side-effect sequence is executed exactly once, in order, with proper
    error handling.

    Transaction model
    ─────────────────
    DB writes (visibility/cleanup upsert + audit log insert) occur inside a
    single asyncpg transaction.  In-memory cache invalidation and event
    emission happen after a successful commit.  If the commit fails, no
    in-process state is mutated and no events are emitted.

    If event emission raises after a successful commit, the DB state is correct
    and the error is logged but not re-raised (best-effort propagation).
    """

    async def set_visibility(
        self,
        ctx: GovernanceContext,
        scope_type: str,
        scope_id: int,
        subsystem: str,
        enabled: bool | None,
    ) -> None:
        """Set a subsystem visibility override.  enabled=None clears the override.

        scope_type must be one of: channel, category, guild, thread.
        Role-scoped overrides are not yet resolvable (ISSUE-007) and are
        explicitly rejected to prevent silent misconfiguration.
        """
        # 1. Validate inputs
        if scope_type not in _VALID_VISIBILITY_SCOPE_TYPES:
            raise GovernanceError(
                f"Invalid scope_type {scope_type!r}. "
                f"Must be one of: {sorted(_VALID_VISIBILITY_SCOPE_TYPES)}. "
                "Role-scoped overrides are not yet supported.",
            )
        if subsystem not in SUBSYSTEMS:
            raise GovernanceError(
                f"Unknown subsystem {subsystem!r}.  "
                "Only registered subsystems may have visibility overrides.",
            )

        # 2. Validate authority (infrastructure boundary — always enforced)
        _validate_authority(ctx)

        # 3. Read old value for full audit trail
        old_enabled = await db.get_visibility_override(
            ctx.guild_id,
            scope_type,
            scope_id,
            subsystem,
        )

        mutation_id = str(uuid.uuid4())
        committed_at = datetime.now(tz=timezone.utc)
        occurred_at = committed_at.isoformat()

        # 4. DB write + audit in a single transaction.
        # ``asyncpg.Pool`` does not implement ``.transaction()`` — only an
        # acquired ``Connection`` does — so the transaction MUST be opened
        # on a connection.  We inline the SQL (matching
        # ``services.economy_service.transfer``) so the visibility upsert
        # and the audit-log insert really share one transaction; calling
        # ``db.set_subsystem_visibility`` / ``db.write_governance_audit``
        # here would acquire fresh pool connections and break atomicity.
        pool = db.get()
        async with pool.acquire() as conn, conn.transaction():
            await conn.execute(
                """INSERT INTO subsystem_visibility
                       (guild_id, scope_type, scope_id, subsystem, enabled)
                   VALUES ($1, $2, $3, $4, $5)
                   ON CONFLICT (guild_id, scope_type, scope_id, subsystem)
                   DO UPDATE SET enabled = EXCLUDED.enabled""",
                ctx.guild_id,
                scope_type,
                scope_id,
                subsystem,
                enabled,
            )
            await conn.execute(
                """INSERT INTO governance_audit_log
                       (guild_id, actor_id, action, scope_type, scope_id,
                        subsystem, old_value, new_value)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                ctx.guild_id,
                ctx.member.id if ctx.member else 0,
                "set_visibility",
                scope_type,
                scope_id,
                subsystem,
                {"enabled": old_enabled},  # JSONB codec handles encoding
                {"enabled": enabled},
            )

        # 5. In-memory cache invalidation (after successful commit)
        invalidate_guild_cache(ctx.guild_id)

        # Phase 9c.2: companion ``audit.action_recorded`` event via the
        # shared publisher. Best-effort; failure is logged inside the
        # helper and does not affect the primary governance events
        # below.
        await emit_audit_action(
            mutation_id=mutation_id,
            subsystem=subsystem,
            mutation_type="set_visibility",
            target=f"{scope_type}:{scope_id}.{subsystem}",
            scope=scope_type,
            guild_id=ctx.guild_id,
            prev_value=str(old_enabled) if old_enabled is not None else None,
            new_value=str(enabled) if enabled is not None else None,
            actor_id=ctx.member.id if ctx.member else None,
            actor_type="user",
            occurred_at=committed_at,
        )

        # 6. Event emission (best-effort; DB state is already correct)
        event_payload = {
            "guild_id": ctx.guild_id,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "subsystem": subsystem,
            "enabled": enabled,
            "mutation_id": mutation_id,
            "occurred_at": occurred_at,
            "actor_id": ctx.member.id if ctx.member else 0,
        }
        try:
            await _emit_governance_event(EVT_VISIBILITY_CHANGED, event_payload)
            await _emit_governance_event(
                EVT_CACHE_INVALIDATED,
                {
                    "guild_id": ctx.guild_id,
                    "mutation_id": mutation_id,
                    "occurred_at": occurred_at,
                },
            )
        except Exception as exc:
            logger.error(
                "Governance event emission failed after successful DB commit "
                "(mutation_id=%s): %s",
                mutation_id,
                exc,
                exc_info=True,
            )

    async def set_cleanup_policy(
        self,
        ctx: GovernanceContext,
        scope_type: str,
        scope_id: int,
        delete_invalid_commands: bool = True,
        delete_failed_commands: bool = True,
        delete_after_seconds: int = 5,
    ) -> None:
        """Set a cleanup policy override for a scope.

        scope_type must be one of: channel, category, guild.  Unlike visibility,
        cleanup policies do not support thread scope — a thread (or otherwise
        invalid) scope_type raises GovernanceError *before* any DB write (RC-5;
        cleanup_policies kept its non-thread CHECK constraint in migration 009).
        """
        if scope_type not in _VALID_CLEANUP_SCOPE_TYPES:
            raise GovernanceError(
                f"Invalid scope_type {scope_type!r} for cleanup policy. "
                f"Must be one of: {sorted(_VALID_CLEANUP_SCOPE_TYPES)}. "
                "cleanup_policies does not support thread scope (migration 009).",
            )

        _validate_authority(ctx)

        mutation_id = str(uuid.uuid4())
        committed_at = datetime.now(tz=timezone.utc)
        occurred_at = committed_at.isoformat()

        # DB write + audit in a single transaction.  Same constraint as
        # set_visibility: transactions live on connections, not pools.  We
        # inline the SQL so both writes share one transaction.
        pool = db.get()
        async with pool.acquire() as conn, conn.transaction():
            await conn.execute(
                """INSERT INTO cleanup_policies
                       (guild_id, scope_type, scope_id,
                        delete_invalid_commands, delete_failed_commands,
                        delete_after_seconds)
                   VALUES ($1, $2, $3, $4, $5, $6)
                   ON CONFLICT (guild_id, scope_type, scope_id)
                   DO UPDATE SET
                       delete_invalid_commands = EXCLUDED.delete_invalid_commands,
                       delete_failed_commands  = EXCLUDED.delete_failed_commands,
                       delete_after_seconds    = EXCLUDED.delete_after_seconds""",
                ctx.guild_id,
                scope_type,
                scope_id,
                delete_invalid_commands,
                delete_failed_commands,
                delete_after_seconds,
            )
            await conn.execute(
                """INSERT INTO governance_audit_log
                       (guild_id, actor_id, action, scope_type, scope_id,
                        subsystem, old_value, new_value)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                ctx.guild_id,
                ctx.member.id if ctx.member else 0,
                "set_cleanup",
                scope_type,
                scope_id,
                None,
                None,  # JSONB codec handles None
                {
                    "delete_invalid_commands": delete_invalid_commands,
                    "delete_failed_commands": delete_failed_commands,
                    "delete_after_seconds": delete_after_seconds,
                },
            )

        invalidate_guild_cache(ctx.guild_id)

        # Phase 9c.2: companion ``audit.action_recorded`` event via the
        # shared publisher. Best-effort; failure is logged inside the
        # helper.
        await emit_audit_action(
            mutation_id=mutation_id,
            subsystem="governance",
            mutation_type="set_cleanup_policy",
            target=f"{scope_type}:{scope_id}",
            scope=scope_type,
            guild_id=ctx.guild_id,
            prev_value=None,
            new_value=(
                f"after_{delete_after_seconds}s:"
                f"invalid={delete_invalid_commands},"
                f"failed={delete_failed_commands}"
            ),
            actor_id=ctx.member.id if ctx.member else None,
            actor_type="user",
            occurred_at=committed_at,
        )

        try:
            await _emit_governance_event(
                EVT_CLEANUP_CHANGED,
                {
                    "guild_id": ctx.guild_id,
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "mutation_id": mutation_id,
                    "occurred_at": occurred_at,
                    "actor_id": ctx.member.id if ctx.member else 0,
                },
            )
            await _emit_governance_event(
                EVT_CACHE_INVALIDATED,
                {
                    "guild_id": ctx.guild_id,
                    "mutation_id": mutation_id,
                    "occurred_at": occurred_at,
                },
            )
        except Exception as exc:
            logger.error(
                "Governance event emission failed after successful DB commit "
                "(mutation_id=%s): %s",
                mutation_id,
                exc,
                exc_info=True,
            )

    async def remove_cleanup_policy(
        self,
        ctx: GovernanceContext,
        scope_type: str,
        scope_id: int,
    ) -> bool:
        """Delete a cleanup policy override for a scope (audited).

        The mirror of :meth:`set_cleanup_policy` for clearing a row.  Keyed by
        the *literal* ``scope_id`` so a stale or legacy-keyed row (e.g. a guild
        row written at ``scope_id=0`` the resolver never reads) can be removed.
        Returns ``True`` when a row was deleted, ``False`` when none matched
        (still a valid, audited no-op — the operator learns it was already gone).
        Same scope-type and authority rules as the set path; DELETE + audit run
        in one transaction.
        """
        if scope_type not in _VALID_CLEANUP_SCOPE_TYPES:
            raise GovernanceError(
                f"Invalid scope_type {scope_type!r} for cleanup policy. "
                f"Must be one of: {sorted(_VALID_CLEANUP_SCOPE_TYPES)}. "
                "cleanup_policies does not support thread scope (migration 009).",
            )

        _validate_authority(ctx)

        mutation_id = str(uuid.uuid4())
        committed_at = datetime.now(tz=timezone.utc)
        occurred_at = committed_at.isoformat()

        pool = db.get()
        async with pool.acquire() as conn, conn.transaction():
            status = await conn.execute(
                "DELETE FROM cleanup_policies"
                " WHERE guild_id=$1 AND scope_type=$2 AND scope_id=$3",
                ctx.guild_id,
                scope_type,
                scope_id,
            )
            removed = status.rsplit(" ", 1)[-1] != "0"
            await conn.execute(
                """INSERT INTO governance_audit_log
                       (guild_id, actor_id, action, scope_type, scope_id,
                        subsystem, old_value, new_value)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                ctx.guild_id,
                ctx.member.id if ctx.member else 0,
                "remove_cleanup",
                scope_type,
                scope_id,
                None,
                {"removed": removed},
                None,  # JSONB codec handles None
            )

        invalidate_guild_cache(ctx.guild_id)

        await emit_audit_action(
            mutation_id=mutation_id,
            subsystem="governance",
            mutation_type="remove_cleanup_policy",
            target=f"{scope_type}:{scope_id}",
            scope=scope_type,
            guild_id=ctx.guild_id,
            prev_value="present" if removed else "absent",
            new_value=None,
            actor_id=ctx.member.id if ctx.member else None,
            actor_type="user",
            occurred_at=committed_at,
        )

        try:
            await _emit_governance_event(
                EVT_CLEANUP_CHANGED,
                {
                    "guild_id": ctx.guild_id,
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "mutation_id": mutation_id,
                    "occurred_at": occurred_at,
                    "actor_id": ctx.member.id if ctx.member else 0,
                },
            )
            await _emit_governance_event(
                EVT_CACHE_INVALIDATED,
                {
                    "guild_id": ctx.guild_id,
                    "mutation_id": mutation_id,
                    "occurred_at": occurred_at,
                },
            )
        except Exception as exc:
            logger.error(
                "Governance event emission failed after successful DB commit "
                "(mutation_id=%s): %s",
                mutation_id,
                exc,
                exc_info=True,
            )

        return removed


# ---------------------------------------------------------------------------
# Module-level convenience functions (thin wrappers around the pipeline)
# Kept for backward compatibility with existing call sites.
# ---------------------------------------------------------------------------

_pipeline = GovernanceMutationPipeline()


async def set_subsystem_visibility(
    ctx: GovernanceContext,
    scope_type: str,
    scope_id: int,
    subsystem: str,
    enabled: bool | None,
) -> None:
    """Set a subsystem visibility override.  Delegates to GovernanceMutationPipeline."""
    await _pipeline.set_visibility(ctx, scope_type, scope_id, subsystem, enabled)


async def set_cleanup_policy_for_scope(
    ctx: GovernanceContext,
    scope_type: str,
    scope_id: int,
    delete_invalid_commands: bool = True,
    delete_failed_commands: bool = True,
    delete_after_seconds: int = 5,
) -> None:
    """Set a cleanup policy override for a scope.  Delegates to GovernanceMutationPipeline."""
    await _pipeline.set_cleanup_policy(
        ctx,
        scope_type,
        scope_id,
        delete_invalid_commands=delete_invalid_commands,
        delete_failed_commands=delete_failed_commands,
        delete_after_seconds=delete_after_seconds,
    )


async def remove_cleanup_policy_for_scope(
    ctx: GovernanceContext,
    scope_type: str,
    scope_id: int,
) -> bool:
    """Delete a cleanup policy override for a scope.  Delegates to GovernanceMutationPipeline."""
    return await _pipeline.remove_cleanup_policy(ctx, scope_type, scope_id)


async def check_governance_version(guild_id: int) -> None:
    """Check and upgrade governance version for a guild if needed."""
    stored = await db.get_setting(
        guild_id,
        settings_keys.GOVERNANCE_VERSION,
        default="0",
    )
    if int(stored) < REGISTRY_VERSION:
        await _run_governance_upgrade(guild_id, from_version=int(stored))


async def _run_governance_upgrade(guild_id: int, from_version: int) -> None:
    logger.info(
        "governance upgrade guild=%d from v%d to v%d",
        guild_id,
        from_version,
        REGISTRY_VERSION,
    )
    # Clean up orphaned overrides for subsystems no longer in the registry.
    known = set(SUBSYSTEMS.keys())
    all_rows = await db.get_all_visibility_for_guild(guild_id)
    orphans = [r for r in all_rows if r["subsystem"] not in known]
    if orphans:
        logger.warning(
            "governance upgrade: removing %d orphan override(s) for guild=%d",
            len(orphans),
            guild_id,
        )
        for o in orphans:
            await db.get().execute(
                """DELETE FROM subsystem_visibility
                   WHERE guild_id=$1 AND scope_type=$2 AND scope_id=$3 AND subsystem=$4""",
                guild_id,
                o["scope_type"],
                o["scope_id"],
                o["subsystem"],
            )

    await db.set_setting(
        guild_id,
        settings_keys.GOVERNANCE_VERSION,
        str(REGISTRY_VERSION),
    )
