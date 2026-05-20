"""Rollout mutation pipeline — Phase 2d PR-3.

The canonical write path for ``feature_flag_global_overrides``,
``feature_flag_guild_overrides``, and ``environment_tiers``.  Mirrors
the 7-step contract from
:class:`~services.binding_mutation.BindingMutationPipeline`:

  1. Input validation       — flag declared in the registry; mutation
                              type matches the entry point; scope/state
                              tokens recognized.
  2. Authority validation   — actor_type within an explicit allowed
                              set.  Discord-facing command surface is
                              deferred to a follow-up PR.
  3. Read previous state    — for the audit row.
  4. DB write + audit       — single transaction via
                              :mod:`utils.db.feature_flag_state` /
                              :mod:`utils.db.environment_tiers`.
  5. Cache invalidation     — :func:`core.runtime.feature_flags.clear_cache`
                              scoped to the affected flag and/or guild.
  6. Event emission         — advisory, post-commit, never raises.
  7. Return result          — with mutation_id for cross-pipeline
                              correlation.

Authority model (intentionally minimal for PR-3):

  * ``actor_type='platform_owner'`` — the only actor accepted from
    operator scripts / future Discord admin command.  ``actor_id`` is
    required to be non-None for this type.
  * ``actor_type='system'`` — for CI seeds / migration helpers.
    ``actor_id`` may be None.
  * ``actor_type='backfill'`` — reserved for future logical-migration
    runs (PR-5/6).  Currently no callers.

Any other actor_type is rejected at step 2.  The Phase 4.5 typed
access-control resolver will replace this with the same capability
mechanism the binding pipeline uses.

Hard limits for PR-3:

  * No Discord admin command for flag mutation — operators mutate via
    a one-off Python script that imports this pipeline.  The command
    surface ships in a follow-up after authority is tightened.
  * Subscribers of the three new events are not wired in this PR.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from core.runtime import feature_flags
from services.audit_events import EVT_AUDIT_ACTION_RECORDED, emit_audit_action
from utils.db import environment_tiers as et_db
from utils.db import feature_flag_state as ff_db

logger = logging.getLogger("bot.services.rollout_mutation")

# ---------------------------------------------------------------------------
# Catalogued event names
# ---------------------------------------------------------------------------

EVT_FEATURE_FLAGS_CHANGED = "feature_flags.changed"
EVT_ROLLOUT_ADVANCED = "rollout.advanced"
EVT_ENVIRONMENT_TIER_CHANGED = "environment_tier.changed"

# ``EVT_AUDIT_ACTION_RECORDED`` is re-exported from
# :mod:`services.audit_events` (Phase 9c.2 shared publisher) so existing
# importers of ``from services.rollout_mutation import
# EVT_AUDIT_ACTION_RECORDED`` keep working.

# ---------------------------------------------------------------------------
# Recognized literal sets (mirror migration 023 / 024 / 025 CHECK constraints)
# ---------------------------------------------------------------------------

_VALID_STATES: frozenset[str] = frozenset(
    {"off", "owner", "canary", "beta", "production", "on"},
)
_VALID_TIERS: frozenset[str] = frozenset(
    {"production", "beta", "canary", "owner_guild_only", "development"},
)
_ALLOWED_ACTOR_TYPES: frozenset[str] = frozenset(
    {"platform_owner", "system", "backfill"},
)

Scope = Literal["global", "guild"]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RolloutMutationError(Exception):
    """Base class for failures from :class:`RolloutMutationPipeline`."""


class UnknownFeatureFlagError(RolloutMutationError):
    """Raised when the flag_name is not in the FeatureFlag registry."""


class InvalidStateError(RolloutMutationError):
    """Raised when the supplied state token is not recognized."""


class InvalidTierError(RolloutMutationError):
    """Raised when the supplied tier token is not recognized."""


class InvalidRolloutPercentError(RolloutMutationError):
    """Raised when rollout_percent is outside 0..100."""


class UnauthorizedRolloutMutationError(RolloutMutationError):
    """Raised when ``actor_type`` is not in the allowed set or actor_id
    is missing for an actor_type that requires it.
    """


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RolloutMutationResult:
    """Outcome of a successful (or partially successful) mutation."""

    mutation_id: str
    flag_name: str
    scope: Scope
    guild_id: int | None
    prev_state: str | None
    new_state: str | None
    prev_rollout_percent: int | None
    new_rollout_percent: int | None
    prev_tier: str | None
    new_tier: str | None
    mutation_type: Literal["set_state", "set_rollout_percent", "set_tier"]
    committed_at: datetime
    event_emitted: bool


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class RolloutMutationPipeline:
    """Centralised orchestration for feature-flag + environment-tier writes.

    Stateless — create one per mutation request.  Three public methods:

    * :meth:`set_flag_state` — flip a flag on/off or to a tier name,
      scoped global or per-guild.
    * :meth:`set_rollout_percent` — change a global flag's rollout %.
    * :meth:`set_environment_tier` — change a guild's tier.

    All three follow the same 7-step contract documented in the module
    docstring.
    """

    def __init__(self) -> None:
        # No instance state.
        pass

    # ------------------------------------------------------------------
    # set_flag_state
    # ------------------------------------------------------------------

    async def set_flag_state(
        self,
        *,
        flag_name: str,
        scope: Scope,
        state: str,
        actor_id: int | None,
        actor_type: str = "platform_owner",
        guild_id: int | None = None,
    ) -> RolloutMutationResult:
        """Set ``state`` on the global or per-guild override row."""
        self._validate_flag(flag_name)
        self._validate_state(state)
        self._validate_scope_and_guild(scope, guild_id)
        self._validate_authority(actor_id, actor_type)

        mutation_id = str(uuid.uuid4())
        if scope == "global":
            prev = await ff_db.get_global_override(flag_name)
            prev_state = prev["state"] if prev else None
            prev_rollout = prev["rollout_percent"] if prev else None
            try:
                await ff_db.upsert_global_with_audit(
                    flag_name=flag_name,
                    state=state,
                    rollout_percent=prev_rollout,
                    actor_id=actor_id,
                    actor_type=actor_type,
                    mutation_id=mutation_id,
                    prev_state=prev_state,
                    prev_rollout_percent=prev_rollout,
                    mutation_type="set_state",
                )
            except Exception:
                logger.exception(
                    "RolloutMutationPipeline.set_flag_state: DB transaction "
                    "failed for flag=%r scope=global; no cache invalidation, "
                    "no event emission.",
                    flag_name,
                )
                raise
            feature_flags.clear_cache(flag_name=flag_name)
            committed_at = _now_utc()
            event_emitted = await _emit_feature_flag_event(
                mutation_id=mutation_id,
                flag_name=flag_name,
                scope="global",
                guild_id=None,
                prev_state=prev_state,
                new_state=state,
                actor_id=actor_id,
                actor_type=actor_type,
                committed_at=committed_at,
            )
            return RolloutMutationResult(
                mutation_id=mutation_id,
                flag_name=flag_name,
                scope="global",
                guild_id=None,
                prev_state=prev_state,
                new_state=state,
                prev_rollout_percent=prev_rollout,
                new_rollout_percent=prev_rollout,
                prev_tier=None,
                new_tier=None,
                mutation_type="set_state",
                committed_at=committed_at,
                event_emitted=event_emitted,
            )

        # Guild-scoped branch.  guild_id non-null is guaranteed by
        # _validate_scope_and_guild above; the assert is just for mypy.
        assert guild_id is not None  # noqa: S101
        prev_guild = await ff_db.get_guild_override(flag_name, guild_id)
        prev_state = prev_guild["state"] if prev_guild else None
        try:
            await ff_db.upsert_guild_with_audit(
                flag_name=flag_name,
                guild_id=guild_id,
                state=state,
                actor_id=actor_id,
                actor_type=actor_type,
                mutation_id=mutation_id,
                prev_state=prev_state,
            )
        except Exception:
            logger.exception(
                "RolloutMutationPipeline.set_flag_state: DB transaction "
                "failed for flag=%r scope=guild guild=%d; no cache "
                "invalidation, no event emission.",
                flag_name,
                guild_id,
            )
            raise
        # Invalidate both the per-guild entry AND the global entry for
        # this flag (a global lookup could have cached a "no guild row"
        # decision that is now stale).
        feature_flags.clear_cache(flag_name=flag_name, guild_id=guild_id)
        feature_flags.clear_cache(flag_name=flag_name, guild_id=None)
        committed_at = _now_utc()
        event_emitted = await _emit_feature_flag_event(
            mutation_id=mutation_id,
            flag_name=flag_name,
            scope="guild",
            guild_id=guild_id,
            prev_state=prev_state,
            new_state=state,
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
        )
        return RolloutMutationResult(
            mutation_id=mutation_id,
            flag_name=flag_name,
            scope="guild",
            guild_id=guild_id,
            prev_state=prev_state,
            new_state=state,
            prev_rollout_percent=None,
            new_rollout_percent=None,
            prev_tier=None,
            new_tier=None,
            mutation_type="set_state",
            committed_at=committed_at,
            event_emitted=event_emitted,
        )

    # ------------------------------------------------------------------
    # set_rollout_percent
    # ------------------------------------------------------------------

    async def set_rollout_percent(
        self,
        *,
        flag_name: str,
        percent: int,
        actor_id: int | None,
        actor_type: str = "platform_owner",
    ) -> RolloutMutationResult:
        """Set the global rollout_percent for ``flag_name``."""
        self._validate_flag(flag_name)
        if not (0 <= percent <= 100):
            raise InvalidRolloutPercentError(
                f"rollout_percent must be in 0..100, got {percent!r}",
            )
        self._validate_authority(actor_id, actor_type)

        mutation_id = str(uuid.uuid4())
        prev = await ff_db.get_global_override(flag_name)
        prev_state = prev["state"] if prev else "off"
        prev_percent = prev["rollout_percent"] if prev else None
        try:
            await ff_db.upsert_global_with_audit(
                flag_name=flag_name,
                state=prev_state,
                rollout_percent=percent,
                actor_id=actor_id,
                actor_type=actor_type,
                mutation_id=mutation_id,
                prev_state=prev_state,
                prev_rollout_percent=prev_percent,
                mutation_type="set_rollout_percent",
            )
        except Exception:
            logger.exception(
                "RolloutMutationPipeline.set_rollout_percent: DB transaction "
                "failed for flag=%r; no cache invalidation, no event emission.",
                flag_name,
            )
            raise
        # Rollout changes invalidate every cached guild decision for
        # this flag.
        feature_flags.clear_cache(flag_name=flag_name)
        committed_at = _now_utc()
        event_emitted = await _emit_rollout_event(
            mutation_id=mutation_id,
            flag_name=flag_name,
            prev_percent=prev_percent,
            new_percent=percent,
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
        )
        return RolloutMutationResult(
            mutation_id=mutation_id,
            flag_name=flag_name,
            scope="global",
            guild_id=None,
            prev_state=prev_state,
            new_state=prev_state,
            prev_rollout_percent=prev_percent,
            new_rollout_percent=percent,
            prev_tier=None,
            new_tier=None,
            mutation_type="set_rollout_percent",
            committed_at=committed_at,
            event_emitted=event_emitted,
        )

    # ------------------------------------------------------------------
    # set_environment_tier
    # ------------------------------------------------------------------

    async def set_environment_tier(
        self,
        *,
        guild_id: int,
        tier: str,
        actor_id: int | None,
        actor_type: str = "platform_owner",
    ) -> RolloutMutationResult:
        """Set a guild's environment tier."""
        if tier not in _VALID_TIERS:
            raise InvalidTierError(
                f"tier must be one of {sorted(_VALID_TIERS)}, got {tier!r}",
            )
        self._validate_authority(actor_id, actor_type)

        mutation_id = str(uuid.uuid4())
        prev_tier = await et_db.get_tier(guild_id)
        try:
            await et_db.upsert_with_audit(
                guild_id=guild_id,
                tier=tier,
                actor_id=actor_id,
                actor_type=actor_type,
                mutation_id=mutation_id,
                prev_tier=prev_tier,
            )
        except Exception:
            logger.exception(
                "RolloutMutationPipeline.set_environment_tier: DB transaction "
                "failed for guild=%d; no cache invalidation, no event emission.",
                guild_id,
            )
            raise
        # A tier change can change every flag's effective value for
        # this guild; drop every cached entry scoped to it.
        feature_flags.clear_cache(guild_id=guild_id)
        committed_at = _now_utc()
        event_emitted = await _emit_environment_tier_event(
            mutation_id=mutation_id,
            guild_id=guild_id,
            prev_tier=prev_tier,
            new_tier=tier,
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
        )
        return RolloutMutationResult(
            mutation_id=mutation_id,
            flag_name="__environment_tier__",
            scope="guild",
            guild_id=guild_id,
            prev_state=None,
            new_state=None,
            prev_rollout_percent=None,
            new_rollout_percent=None,
            prev_tier=prev_tier,
            new_tier=tier,
            mutation_type="set_tier",
            committed_at=committed_at,
            event_emitted=event_emitted,
        )

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_flag(flag_name: str) -> None:
        if feature_flags.get(flag_name) is None:
            raise UnknownFeatureFlagError(
                f"flag {flag_name!r} is not declared; register it in "
                "core/runtime/feature_flags.py or the owning subsystem "
                "before mutating.",
            )

    @staticmethod
    def _validate_state(state: str) -> None:
        if state not in _VALID_STATES:
            raise InvalidStateError(
                f"state must be one of {sorted(_VALID_STATES)}, got {state!r}",
            )

    @staticmethod
    def _validate_scope_and_guild(scope: str, guild_id: int | None) -> None:
        if scope not in ("global", "guild"):
            raise RolloutMutationError(
                f"scope must be 'global' or 'guild', got {scope!r}",
            )
        if scope == "guild" and guild_id is None:
            raise RolloutMutationError(
                "scope='guild' requires guild_id to be set",
            )
        if scope == "global" and guild_id is not None:
            raise RolloutMutationError(
                "scope='global' must not specify guild_id",
            )

    @staticmethod
    def _validate_authority(actor_id: int | None, actor_type: str) -> None:
        if actor_type not in _ALLOWED_ACTOR_TYPES:
            raise UnauthorizedRolloutMutationError(
                f"actor_type must be one of {sorted(_ALLOWED_ACTOR_TYPES)}, "
                f"got {actor_type!r}",
            )
        if actor_type == "platform_owner" and actor_id is None:
            raise UnauthorizedRolloutMutationError(
                "actor_type='platform_owner' requires non-None actor_id",
            )


# ---------------------------------------------------------------------------
# Event emitters (post-commit, advisory)
# ---------------------------------------------------------------------------


async def _emit_feature_flag_event(
    *,
    mutation_id: str,
    flag_name: str,
    scope: Scope,
    guild_id: int | None,
    prev_state: str | None,
    new_state: str,
    actor_id: int | None,
    actor_type: str,
    committed_at: datetime,
) -> bool:
    """Emit feature_flags.changed + audit.action_recorded.

    Returns False on feature_flags.changed emission failure. Audit
    emission failure is logged independently and does not affect the
    feature-flags return — pipeline-specific consumers receive their
    event regardless of audit-channel reachability.
    """
    from core.events import bus

    try:
        await bus.emit(
            EVT_FEATURE_FLAGS_CHANGED,
            mutation_id=mutation_id,
            flag_name=flag_name,
            scope=scope,
            guild_id=guild_id,
            prev_state=prev_state,
            new_state=new_state,
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=committed_at.isoformat(),
        )
    except Exception:
        logger.exception(
            "RolloutMutationPipeline: feature_flags.changed emission failed "
            "for mutation_id=%s; DB state is correct, event lost.",
            mutation_id,
        )
        return False

    # Phase 9c.1 — companion audit event for the generic audit
    # consumer (server_logging). Emission failure here is independent
    # of the feature-flags event success.
    await emit_audit_action(
        mutation_id=mutation_id,
        subsystem="logging",
        mutation_type="set_flag_state",
        target=f"flag:{flag_name}",
        scope=scope,
        guild_id=guild_id,
        prev_value=prev_state,
        new_value=new_state,
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=committed_at,
    )
    return True


async def _emit_rollout_event(
    *,
    mutation_id: str,
    flag_name: str,
    prev_percent: int | None,
    new_percent: int,
    actor_id: int | None,
    actor_type: str,
    committed_at: datetime,
) -> bool:
    from core.events import bus

    try:
        await bus.emit(
            EVT_ROLLOUT_ADVANCED,
            mutation_id=mutation_id,
            flag_name=flag_name,
            prev_percent=prev_percent,
            new_percent=new_percent,
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=committed_at.isoformat(),
        )
    except Exception:
        logger.exception(
            "RolloutMutationPipeline: rollout.advanced emission failed "
            "for mutation_id=%s; DB state is correct, event lost.",
            mutation_id,
        )
        return False

    # Phase 9c.1 — companion audit emit. Rollout percent is global.
    await emit_audit_action(
        mutation_id=mutation_id,
        subsystem="logging",
        mutation_type="set_rollout_percent",
        target=f"flag:{flag_name}",
        scope="global",
        guild_id=None,
        prev_value=str(prev_percent) if prev_percent is not None else None,
        new_value=str(new_percent),
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=committed_at,
    )
    return True


async def _emit_environment_tier_event(
    *,
    mutation_id: str,
    guild_id: int,
    prev_tier: str | None,
    new_tier: str,
    actor_id: int | None,
    actor_type: str,
    committed_at: datetime,
) -> bool:
    from core.events import bus

    try:
        await bus.emit(
            EVT_ENVIRONMENT_TIER_CHANGED,
            mutation_id=mutation_id,
            guild_id=guild_id,
            prev_tier=prev_tier,
            new_tier=new_tier,
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=committed_at.isoformat(),
        )
    except Exception:
        logger.exception(
            "RolloutMutationPipeline: environment_tier.changed emission "
            "failed for mutation_id=%s; DB state is correct, event lost.",
            mutation_id,
        )
        return False

    # Phase 9c.1 — companion audit emit. Environment tier is guild-scoped.
    await emit_audit_action(
        mutation_id=mutation_id,
        subsystem="logging",
        mutation_type="set_environment_tier",
        target=f"guild:{guild_id}",
        scope="guild",
        guild_id=guild_id,
        prev_value=prev_tier,
        new_value=new_tier,
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=committed_at,
    )
    return True


def _now_utc() -> datetime:
    """Return a tz-aware "now" — INV-N forbids bare datetime.utcnow."""
    return datetime.now(timezone.utc)


__all__ = [
    "EVT_AUDIT_ACTION_RECORDED",
    "EVT_ENVIRONMENT_TIER_CHANGED",
    "EVT_FEATURE_FLAGS_CHANGED",
    "EVT_ROLLOUT_ADVANCED",
    "InvalidRolloutPercentError",
    "InvalidStateError",
    "InvalidTierError",
    "RolloutMutationError",
    "RolloutMutationPipeline",
    "RolloutMutationResult",
    "UnauthorizedRolloutMutationError",
    "UnknownFeatureFlagError",
]
