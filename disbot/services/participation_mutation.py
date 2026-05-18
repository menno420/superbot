"""Participation mutation pipeline — Phase 2c PR-9.

The canonical write path for the four per-user participation tables:

  * ``user_participation``
  * ``user_subscriptions``
  * ``user_preferences``
  * ``user_visibility_overrides``

Mirrors the 7-step contract from
:class:`services.binding_mutation.BindingMutationPipeline` and
:class:`services.rollout_mutation.RolloutMutationPipeline`:

  1. Input validation   — value shapes, enum literals
  2. Authority          — actor_type in allowed set; self-write
                          requires actor_id == user_id
  3. Read previous      — for the audit row
  4. DB write + audit   — single transaction via
                          :mod:`utils.db.user_participation`
  5. Cache invalidation — :func:`core.runtime.user_config.invalidate_user_guild`
                          called inline AFTER the DB commit and
                          BEFORE event emission
  6. Event emission     — advisory, post-commit, never raises
  7. Return result      — typed :class:`ParticipationMutationResult`
                          carrying mutation_id for cross-pipeline
                          correlation

Authority model:

* ``actor_type='user'`` — self-update.  ``actor_id`` MUST equal
  ``user_id``; otherwise :class:`UnauthorizedParticipationMutationError`.
* ``actor_type='moderator'`` / ``'admin'`` — privileged override.
  ``actor_id`` required non-None and need not equal ``user_id``.
  No Discord-facing surface invokes these in PR-9; they exist so a
  future moderation tool can land without a migration.
* ``actor_type='system'`` — CI seeds / scripted ops.  ``actor_id``
  may be NULL.
* ``actor_type='backfill'`` — reserved for future logical migrations.
  Currently no callers.

Events (catalogued in ``core/events_catalogue.py``, advisory):

* ``participation.changed``      — set_participation
* ``subscription.changed``       — set_subscription
* ``user_preference.changed``    — set_preference (value intentionally
                                    omitted from payload)
* ``user_visibility.changed``    — set_visibility

Cache invalidation happens INLINE in step 5 (synchronous w.r.t. the
mutation result), not via event subscription.  This matches the
pattern in :class:`RolloutMutationPipeline` and keeps the user_config
cache consistent with DB state even if the event bus subscriber
crashes.

Subscriber failure semantics: any exception from
``core.events.bus.emit`` is logged with the ``mutation_id`` and
swallowed.  DB state is authoritative; the event is best-effort.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from utils.db import user_participation as up_db

logger = logging.getLogger("bot.services.participation_mutation")

# ---------------------------------------------------------------------------
# Catalogued event names (registered in core/events_catalogue.py).
# ---------------------------------------------------------------------------

EVT_PARTICIPATION_CHANGED = "participation.changed"
EVT_SUBSCRIPTION_CHANGED = "subscription.changed"
EVT_USER_PREFERENCE_CHANGED = "user_preference.changed"
EVT_USER_VISIBILITY_CHANGED = "user_visibility.changed"

# ---------------------------------------------------------------------------
# Recognized literal sets (mirror migration 027 + 028 CHECK constraints).
# Alignment tests pin these to the SQL CHECK literals.
# ---------------------------------------------------------------------------

_VALID_PARTICIPATION_STATES: frozenset[str] = frozenset({"opted_in", "opted_out"})
_VALID_VISIBILITY_STATES: frozenset[str] = frozenset({"public", "hidden"})
_ALLOWED_ACTOR_TYPES: frozenset[str] = frozenset(
    {"user", "moderator", "admin", "system", "backfill"},
)

MutationType = Literal[
    "set_participation",
    "set_subscription",
    "set_preference",
    "set_visibility",
]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ParticipationMutationError(Exception):
    """Base class for failures from :class:`ParticipationMutationPipeline`."""


class InvalidParticipationStateError(ParticipationMutationError):
    """Raised when the supplied participation state is not recognised."""


class InvalidVisibilityStateError(ParticipationMutationError):
    """Raised when the supplied visibility state is not recognised."""


class InvalidPreferenceValueError(ParticipationMutationError):
    """Raised when the preference value is not JSON-serialisable."""


class UnauthorizedParticipationMutationError(ParticipationMutationError):
    """Raised when the actor is not allowed to perform this mutation."""


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParticipationMutationResult:
    """Outcome of a successful (or partially successful) mutation."""

    mutation_id: str
    user_id: int
    guild_id: int
    mutation_type: MutationType
    subsystem: str | None
    topic: str | None
    key: str | None
    prev_state: str | None
    new_state: str | None
    prev_enabled: bool | None
    new_enabled: bool | None
    prev_value: Any
    new_value: Any
    prev_visibility: str | None
    new_visibility: str | None
    actor_id: int | None
    actor_type: str
    committed_at: datetime
    event_emitted: bool


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class ParticipationMutationPipeline:
    """Centralised orchestration for per-user participation writes.

    Stateless — create one per mutation request.  Four public methods,
    one per concern.  All follow the same 7-step contract documented
    in the module docstring.
    """

    def __init__(self) -> None:
        # No instance state.
        pass

    # ------------------------------------------------------------------
    # set_participation
    # ------------------------------------------------------------------

    async def set_participation(
        self,
        *,
        user_id: int,
        guild_id: int,
        subsystem: str,
        state: str,
        actor_id: int | None,
        actor_type: str = "user",
    ) -> ParticipationMutationResult:
        """Opt the user in/out of ``subsystem`` for this guild."""
        if state not in _VALID_PARTICIPATION_STATES:
            raise InvalidParticipationStateError(
                f"state must be one of {sorted(_VALID_PARTICIPATION_STATES)}, "
                f"got {state!r}",
            )
        self._validate_authority(user_id, actor_id, actor_type)

        mutation_id = str(uuid.uuid4())
        prev_row = await up_db.get_participation(user_id, guild_id, subsystem)
        prev_state = prev_row["state"] if prev_row else None
        try:
            await up_db.upsert_participation_with_audit(
                user_id=user_id,
                guild_id=guild_id,
                subsystem=subsystem,
                state=state,
                actor_id=actor_id,
                actor_type=actor_type,
                mutation_id=mutation_id,
                prev_state=prev_state,
            )
        except Exception:
            logger.exception(
                "ParticipationMutationPipeline.set_participation: DB transaction "
                "failed for user=%d guild=%d subsystem=%r; no cache invalidation, "
                "no event emission.",
                user_id,
                guild_id,
                subsystem,
            )
            raise
        _invalidate_cache(user_id, guild_id)
        committed_at = _now_utc()
        event_emitted = await _emit(
            EVT_PARTICIPATION_CHANGED,
            mutation_id=mutation_id,
            user_id=user_id,
            guild_id=guild_id,
            subsystem=subsystem,
            prev_state=prev_state,
            new_state=state,
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
        )
        return ParticipationMutationResult(
            mutation_id=mutation_id,
            user_id=user_id,
            guild_id=guild_id,
            mutation_type="set_participation",
            subsystem=subsystem,
            topic=None,
            key=None,
            prev_state=prev_state,
            new_state=state,
            prev_enabled=None,
            new_enabled=None,
            prev_value=None,
            new_value=None,
            prev_visibility=None,
            new_visibility=None,
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
            event_emitted=event_emitted,
        )

    # ------------------------------------------------------------------
    # set_subscription
    # ------------------------------------------------------------------

    async def set_subscription(
        self,
        *,
        user_id: int,
        guild_id: int,
        subsystem: str,
        topic: str,
        enabled: bool,
        actor_id: int | None,
        actor_type: str = "user",
    ) -> ParticipationMutationResult:
        """Set the user's topic-level subscription for ``(subsystem, topic)``."""
        if not isinstance(enabled, bool):
            raise ParticipationMutationError(
                f"enabled must be bool, got {type(enabled).__name__}",
            )
        self._validate_authority(user_id, actor_id, actor_type)

        mutation_id = str(uuid.uuid4())
        prev_row = await up_db.get_subscription(user_id, guild_id, subsystem, topic)
        prev_enabled = prev_row["enabled"] if prev_row else None
        try:
            await up_db.upsert_subscription_with_audit(
                user_id=user_id,
                guild_id=guild_id,
                subsystem=subsystem,
                topic=topic,
                enabled=enabled,
                actor_id=actor_id,
                actor_type=actor_type,
                mutation_id=mutation_id,
                prev_enabled=prev_enabled,
            )
        except Exception:
            logger.exception(
                "ParticipationMutationPipeline.set_subscription: DB transaction "
                "failed for user=%d guild=%d subsystem=%r topic=%r; no cache "
                "invalidation, no event emission.",
                user_id,
                guild_id,
                subsystem,
                topic,
            )
            raise
        _invalidate_cache(user_id, guild_id)
        committed_at = _now_utc()
        event_emitted = await _emit(
            EVT_SUBSCRIPTION_CHANGED,
            mutation_id=mutation_id,
            user_id=user_id,
            guild_id=guild_id,
            subsystem=subsystem,
            topic=topic,
            prev_enabled=prev_enabled,
            new_enabled=enabled,
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
        )
        return ParticipationMutationResult(
            mutation_id=mutation_id,
            user_id=user_id,
            guild_id=guild_id,
            mutation_type="set_subscription",
            subsystem=subsystem,
            topic=topic,
            key=None,
            prev_state=None,
            new_state=None,
            prev_enabled=prev_enabled,
            new_enabled=enabled,
            prev_value=None,
            new_value=None,
            prev_visibility=None,
            new_visibility=None,
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
            event_emitted=event_emitted,
        )

    # ------------------------------------------------------------------
    # set_preference
    # ------------------------------------------------------------------

    async def set_preference(
        self,
        *,
        user_id: int,
        guild_id: int,
        key: str,
        value: Any,
        actor_id: int | None,
        actor_type: str = "user",
    ) -> ParticipationMutationResult:
        """Set a JSONB preference for the user."""
        if value is None:
            raise InvalidPreferenceValueError(
                "preference value must not be None; use a clear primitive "
                "later if needed",
            )
        # JSON-serialisability check.  The DB layer will encode again,
        # but failing fast here is friendlier than asyncpg's error.
        import json as _json

        try:
            _json.dumps(value, default=str)
        except (TypeError, ValueError) as exc:
            raise InvalidPreferenceValueError(
                f"preference value is not JSON-serialisable: {exc}",
            ) from exc
        self._validate_authority(user_id, actor_id, actor_type)

        mutation_id = str(uuid.uuid4())
        prev_row = await up_db.get_preference(user_id, guild_id, key)
        prev_value = prev_row["value"] if prev_row else None
        try:
            await up_db.upsert_preference_with_audit(
                user_id=user_id,
                guild_id=guild_id,
                key=key,
                value=value,
                actor_id=actor_id,
                actor_type=actor_type,
                mutation_id=mutation_id,
                prev_value=prev_value,
            )
        except Exception:
            logger.exception(
                "ParticipationMutationPipeline.set_preference: DB transaction "
                "failed for user=%d guild=%d key=%r; no cache invalidation, "
                "no event emission.",
                user_id,
                guild_id,
                key,
            )
            raise
        _invalidate_cache(user_id, guild_id)
        committed_at = _now_utc()
        # Event payload deliberately omits the value (could contain PII).
        event_emitted = await _emit(
            EVT_USER_PREFERENCE_CHANGED,
            mutation_id=mutation_id,
            user_id=user_id,
            guild_id=guild_id,
            key=key,
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
        )
        return ParticipationMutationResult(
            mutation_id=mutation_id,
            user_id=user_id,
            guild_id=guild_id,
            mutation_type="set_preference",
            subsystem=None,
            topic=None,
            key=key,
            prev_state=None,
            new_state=None,
            prev_enabled=None,
            new_enabled=None,
            prev_value=prev_value,
            new_value=value,
            prev_visibility=None,
            new_visibility=None,
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
            event_emitted=event_emitted,
        )

    # ------------------------------------------------------------------
    # set_visibility
    # ------------------------------------------------------------------

    async def set_visibility(
        self,
        *,
        user_id: int,
        guild_id: int,
        subsystem: str,
        visibility: str,
        actor_id: int | None,
        actor_type: str = "user",
    ) -> ParticipationMutationResult:
        """Set the user's visibility override for ``subsystem``."""
        if visibility not in _VALID_VISIBILITY_STATES:
            raise InvalidVisibilityStateError(
                f"visibility must be one of {sorted(_VALID_VISIBILITY_STATES)}, "
                f"got {visibility!r}",
            )
        self._validate_authority(user_id, actor_id, actor_type)

        mutation_id = str(uuid.uuid4())
        prev_row = await up_db.get_visibility(user_id, guild_id, subsystem)
        prev_visibility = prev_row["visibility"] if prev_row else None
        try:
            await up_db.upsert_visibility_with_audit(
                user_id=user_id,
                guild_id=guild_id,
                subsystem=subsystem,
                visibility=visibility,
                actor_id=actor_id,
                actor_type=actor_type,
                mutation_id=mutation_id,
                prev_visibility=prev_visibility,
            )
        except Exception:
            logger.exception(
                "ParticipationMutationPipeline.set_visibility: DB transaction "
                "failed for user=%d guild=%d subsystem=%r; no cache "
                "invalidation, no event emission.",
                user_id,
                guild_id,
                subsystem,
            )
            raise
        _invalidate_cache(user_id, guild_id)
        committed_at = _now_utc()
        event_emitted = await _emit(
            EVT_USER_VISIBILITY_CHANGED,
            mutation_id=mutation_id,
            user_id=user_id,
            guild_id=guild_id,
            subsystem=subsystem,
            prev_visibility=prev_visibility,
            new_visibility=visibility,
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
        )
        return ParticipationMutationResult(
            mutation_id=mutation_id,
            user_id=user_id,
            guild_id=guild_id,
            mutation_type="set_visibility",
            subsystem=subsystem,
            topic=None,
            key=None,
            prev_state=None,
            new_state=None,
            prev_enabled=None,
            new_enabled=None,
            prev_value=None,
            new_value=None,
            prev_visibility=prev_visibility,
            new_visibility=visibility,
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
            event_emitted=event_emitted,
        )

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_authority(
        user_id: int,
        actor_id: int | None,
        actor_type: str,
    ) -> None:
        """Authority rules (PR-9 minimum surface).

        * 'user' → actor_id MUST equal user_id (self-update only).
        * 'moderator' / 'admin' → actor_id required non-None and may
          differ from user_id (privileged override).
        * 'system' / 'backfill' → actor_id may be None.
        """
        if actor_type not in _ALLOWED_ACTOR_TYPES:
            raise UnauthorizedParticipationMutationError(
                f"actor_type must be one of {sorted(_ALLOWED_ACTOR_TYPES)}, "
                f"got {actor_type!r}",
            )
        if actor_type == "user":
            if actor_id is None or actor_id != user_id:
                raise UnauthorizedParticipationMutationError(
                    f"actor_type='user' requires actor_id == user_id "
                    f"({actor_id!r} != {user_id!r})",
                )
        elif actor_type in ("moderator", "admin"):
            if actor_id is None:
                raise UnauthorizedParticipationMutationError(
                    f"actor_type={actor_type!r} requires non-None actor_id",
                )
        # 'system' / 'backfill' may have None actor_id


# ---------------------------------------------------------------------------
# Step 5 helper: cache invalidation (synchronous w.r.t. the result).
# ---------------------------------------------------------------------------


def _invalidate_cache(user_id: int, guild_id: int) -> None:
    """Drop the cached bundle for ``(user, guild)`` so the next read reloads.

    Local import keeps this module light at import time and matches
    the existing cycle-safety discipline.
    """
    try:
        from core.runtime import user_config

        user_config.invalidate_user_guild(user_id, guild_id)
    except Exception:
        # Cache invalidation MUST NOT raise into the mutation flow.
        # Worst case: a stale read for up to TTL_SECS until the
        # entry expires naturally.  Log and continue.
        logger.exception(
            "ParticipationMutationPipeline: cache invalidation raised for "
            "user=%d guild=%d; DB state is correct, cache will expire via TTL",
            user_id,
            guild_id,
        )


# ---------------------------------------------------------------------------
# Step 6 helper: advisory event emission.  Failures swallowed.
# ---------------------------------------------------------------------------


async def _emit(event_name: str, *, committed_at: datetime, **payload: Any) -> bool:
    """Emit a catalogued event with the standard payload shape.

    Returns ``True`` on success, ``False`` if emission raised.  The
    DB state is correct in both cases.
    """
    from core.events import bus

    try:
        await bus.emit(
            event_name,
            occurred_at=committed_at.isoformat(),
            **payload,
        )
    except Exception:
        logger.exception(
            "ParticipationMutationPipeline._emit: emission failed for "
            "event=%r mutation_id=%s; DB state is correct, event lost.",
            event_name,
            payload.get("mutation_id"),
        )
        return False
    return True


def _now_utc() -> datetime:
    """Return a tz-aware "now" — INV-N forbids bare datetime.utcnow."""
    return datetime.now(timezone.utc)


__all__ = [
    "EVT_PARTICIPATION_CHANGED",
    "EVT_SUBSCRIPTION_CHANGED",
    "EVT_USER_PREFERENCE_CHANGED",
    "EVT_USER_VISIBILITY_CHANGED",
    "InvalidParticipationStateError",
    "InvalidPreferenceValueError",
    "InvalidVisibilityStateError",
    "ParticipationMutationError",
    "ParticipationMutationPipeline",
    "ParticipationMutationResult",
    "UnauthorizedParticipationMutationError",
]
