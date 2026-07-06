"""Automation mutation pipeline — Phase 9g / Track 6 PR 16.

The canonical write path for ``automation_rules``. Mirrors the
7-step contract from
:class:`services.binding_mutation.BindingMutationPipeline`:

  1. Input validation       — config keys match the registry's
                              ``required_config_keys``; schedule
                              syntax sanity-checked.
  2. Authority validation   — actor must be the guild owner (or
                              ``actor_type='system'`` for setup
                              templates).
  3. Read previous state    — for the audit row's prev_value.
  4. DB write + audit       — single asyncpg transaction via
                              :mod:`utils.db.automation`.
  5. Cache invalidation     — no-op in v1; the scheduler polls
                              every 30 s so there is no in-process
                              cache to invalidate. Documented
                              here for shape parity.
  6. Event emission         — ``automation.rule_changed`` +
                              ``audit.action_recorded`` via the
                              Track 1 shared publisher.
  7. Return result          — with mutation_id for cross-pipeline
                              correlation.

The pipeline exposes three entry points:

* :meth:`create_rule`   — insert + emit + audit.
* :meth:`set_enabled`   — flip the enabled bit on an existing rule.
* :meth:`delete_rule`   — delete the rule (cascades to runs).

Authority model: this is owner-only by default. ``actor_type``
literals match the existing rollout pipeline:

* ``platform_owner`` — actor_id must be the guild's owner.
* ``system``         — for CI seeds and the setup wizard's
                       template-application path. ``actor_id`` may
                       be None.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from services.audit_events import emit_audit_action
from services.automation_registry import (
    KNOWN_ACTION_KINDS,
    KNOWN_TRIGGER_KINDS,
    UNSUPPORTED_INSTALLABLE_TRIGGER_KINDS,
    validate_action_config,
    validate_trigger_config,
)
from utils.db import automation as db

logger = logging.getLogger("bot.services.automation_mutation")

EVT_AUTOMATION_RULE_CHANGED = "automation.rule_changed"

_ALLOWED_ACTOR_TYPES: frozenset[str] = frozenset({"platform_owner", "system"})


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AutomationMutationError(Exception):
    """Base class for failures from :class:`AutomationMutationPipeline`."""


class InvalidAutomationConfigError(AutomationMutationError):
    """Trigger / action config validation failed."""


class UnauthorizedAutomationMutationError(AutomationMutationError):
    """Actor below the required tier."""


class UnknownAutomationRuleError(AutomationMutationError):
    """``rule_id`` does not exist for the guild."""


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AutomationMutationResult:
    mutation_id: str
    rule_id: int
    guild_id: int
    mutation_type: str  # "create" / "set_enabled" / "delete"
    name: str
    trigger_kind: str | None
    action_kind: str | None
    prev_enabled: bool | None
    new_enabled: bool | None
    committed_at: datetime
    event_emitted: bool


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class AutomationMutationPipeline:
    """Owner-gated, audit-emitting writer for ``automation_rules``.

    Stateless; instantiate once or per-call.
    """

    async def create_rule(
        self,
        *,
        guild_id: int,
        guild_owner_id: int,
        name: str,
        trigger_kind: str,
        action_kind: str,
        trigger_config: dict[str, Any] | None = None,
        action_config: dict[str, Any] | None = None,
        schedule: str | None = None,
        timezone_str: str = "UTC",
        actor_id: int | None,
        actor_type: str = "platform_owner",
    ) -> AutomationMutationResult:
        # 1. Input validation.
        self._validate_kinds(trigger_kind, action_kind)
        if trigger_kind in UNSUPPORTED_INSTALLABLE_TRIGGER_KINDS:
            raise InvalidAutomationConfigError(
                f"trigger_kind {trigger_kind!r} is known but not installable yet; "
                f"{trigger_kind} requires the cron-parser implementation before "
                "new rules can be created.",
            )
        errors = list(
            validate_trigger_config(trigger_kind, trigger_config or {}),
        ) + list(validate_action_config(action_kind, action_config or {}))
        if errors:
            raise InvalidAutomationConfigError("; ".join(errors))

        # 2. Authority validation.
        self._validate_actor(
            actor_type=actor_type,
            actor_id=actor_id,
            guild_owner_id=guild_owner_id,
        )

        # 3. Read previous (none — create path).
        mutation_id = str(uuid.uuid4())

        # 4. DB write.
        try:
            rule_id = await db.insert_rule(
                guild_id=guild_id,
                name=name,
                trigger_kind=trigger_kind,
                action_kind=action_kind,
                trigger_config=trigger_config or {},
                action_config=action_config or {},
                schedule=schedule,
                timezone=timezone_str,
                created_by=actor_id,
            )
        except Exception:
            logger.exception(
                "AutomationMutationPipeline.create_rule: insert failed for "
                "guild=%d name=%r",
                guild_id,
                name,
            )
            raise

        committed_at = _now_utc()

        # 5. (No cache to invalidate; scheduler polls.)

        # 6. Events.
        event_emitted = await self._emit_event(
            mutation_id=mutation_id,
            rule_id=rule_id,
            guild_id=guild_id,
            mutation_type="create",
            name=name,
            committed_at=committed_at,
        )
        await emit_audit_action(
            mutation_id=mutation_id,
            subsystem="automation",
            mutation_type="create_rule",
            target=f"rule:{name}",
            scope="guild",
            guild_id=guild_id,
            prev_value=None,
            new_value=f"{trigger_kind}->{action_kind}",
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=committed_at,
        )

        # 7. Return.
        return AutomationMutationResult(
            mutation_id=mutation_id,
            rule_id=rule_id,
            guild_id=guild_id,
            mutation_type="create",
            name=name,
            trigger_kind=trigger_kind,
            action_kind=action_kind,
            prev_enabled=None,
            new_enabled=False,
            committed_at=committed_at,
            event_emitted=event_emitted,
        )

    async def set_enabled(
        self,
        *,
        guild_id: int,
        guild_owner_id: int,
        rule_id: int,
        enabled: bool,
        actor_id: int | None,
        actor_type: str = "platform_owner",
    ) -> AutomationMutationResult:
        # 2. Authority.
        self._validate_actor(
            actor_type=actor_type,
            actor_id=actor_id,
            guild_owner_id=guild_owner_id,
        )
        # 3. Read previous.
        existing = await db.get_rule(rule_id)
        if existing is None or existing.get("guild_id") != guild_id:
            raise UnknownAutomationRuleError(
                f"rule_id={rule_id} not found for guild_id={guild_id}",
            )
        prev_enabled = bool(existing.get("enabled"))
        if prev_enabled == enabled:
            # No-op; still emit an audit row so the trail is honest.
            mutation_id = str(uuid.uuid4())
            committed_at = _now_utc()
            await emit_audit_action(
                mutation_id=mutation_id,
                subsystem="automation",
                mutation_type="set_enabled",
                target=f"rule:{existing['name']}",
                scope="guild",
                guild_id=guild_id,
                prev_value=str(prev_enabled),
                new_value=str(enabled),
                actor_id=actor_id,
                actor_type=actor_type,
                occurred_at=committed_at,
            )
            return AutomationMutationResult(
                mutation_id=mutation_id,
                rule_id=rule_id,
                guild_id=guild_id,
                mutation_type="set_enabled",
                name=existing["name"],
                trigger_kind=existing["trigger_kind"],
                action_kind=existing["action_kind"],
                prev_enabled=prev_enabled,
                new_enabled=enabled,
                committed_at=committed_at,
                event_emitted=False,
            )

        mutation_id = str(uuid.uuid4())

        # 4. DB write.
        try:
            await db.set_enabled(rule_id, enabled)
        except Exception:
            logger.exception(
                "AutomationMutationPipeline.set_enabled: db.set_enabled "
                "failed for rule_id=%d",
                rule_id,
            )
            raise

        committed_at = _now_utc()

        # 6. Events.
        event_emitted = await self._emit_event(
            mutation_id=mutation_id,
            rule_id=rule_id,
            guild_id=guild_id,
            mutation_type="set_enabled",
            name=existing["name"],
            committed_at=committed_at,
        )
        await emit_audit_action(
            mutation_id=mutation_id,
            subsystem="automation",
            mutation_type="set_enabled",
            target=f"rule:{existing['name']}",
            scope="guild",
            guild_id=guild_id,
            prev_value=str(prev_enabled),
            new_value=str(enabled),
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=committed_at,
        )

        return AutomationMutationResult(
            mutation_id=mutation_id,
            rule_id=rule_id,
            guild_id=guild_id,
            mutation_type="set_enabled",
            name=existing["name"],
            trigger_kind=existing["trigger_kind"],
            action_kind=existing["action_kind"],
            prev_enabled=prev_enabled,
            new_enabled=enabled,
            committed_at=committed_at,
            event_emitted=event_emitted,
        )

    async def delete_rule(
        self,
        *,
        guild_id: int,
        guild_owner_id: int,
        rule_id: int,
        actor_id: int | None,
        actor_type: str = "platform_owner",
    ) -> AutomationMutationResult:
        # 2. Authority.
        self._validate_actor(
            actor_type=actor_type,
            actor_id=actor_id,
            guild_owner_id=guild_owner_id,
        )
        # 3. Read previous.
        existing = await db.get_rule(rule_id)
        if existing is None or existing.get("guild_id") != guild_id:
            raise UnknownAutomationRuleError(
                f"rule_id={rule_id} not found for guild_id={guild_id}",
            )

        mutation_id = str(uuid.uuid4())

        # 4. DB write.
        try:
            await db.delete_rule(rule_id)
        except Exception:
            logger.exception(
                "AutomationMutationPipeline.delete_rule: db.delete_rule "
                "failed for rule_id=%d",
                rule_id,
            )
            raise

        committed_at = _now_utc()

        # 6. Events.
        event_emitted = await self._emit_event(
            mutation_id=mutation_id,
            rule_id=rule_id,
            guild_id=guild_id,
            mutation_type="delete",
            name=existing["name"],
            committed_at=committed_at,
        )
        await emit_audit_action(
            mutation_id=mutation_id,
            subsystem="automation",
            mutation_type="delete_rule",
            target=f"rule:{existing['name']}",
            scope="guild",
            guild_id=guild_id,
            prev_value=f"{existing['trigger_kind']}->{existing['action_kind']}",
            new_value=None,
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=committed_at,
        )

        return AutomationMutationResult(
            mutation_id=mutation_id,
            rule_id=rule_id,
            guild_id=guild_id,
            mutation_type="delete",
            name=existing["name"],
            trigger_kind=existing["trigger_kind"],
            action_kind=existing["action_kind"],
            prev_enabled=bool(existing.get("enabled")),
            new_enabled=None,
            committed_at=committed_at,
            event_emitted=event_emitted,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_kinds(trigger_kind: str, action_kind: str) -> None:
        if trigger_kind not in KNOWN_TRIGGER_KINDS:
            raise InvalidAutomationConfigError(
                f"trigger_kind={trigger_kind!r} not in {sorted(KNOWN_TRIGGER_KINDS)}",
            )
        if action_kind not in KNOWN_ACTION_KINDS:
            raise InvalidAutomationConfigError(
                f"action_kind={action_kind!r} not in {sorted(KNOWN_ACTION_KINDS)}",
            )

    @staticmethod
    def _validate_actor(
        *,
        actor_type: str,
        actor_id: int | None,
        guild_owner_id: int,
    ) -> None:
        if actor_type not in _ALLOWED_ACTOR_TYPES:
            raise UnauthorizedAutomationMutationError(
                f"actor_type={actor_type!r} not in {sorted(_ALLOWED_ACTOR_TYPES)}",
            )
        if actor_type == "platform_owner":
            if actor_id is None:
                raise UnauthorizedAutomationMutationError(
                    "actor_type='platform_owner' requires non-None actor_id",
                )
            if actor_id != guild_owner_id:
                raise UnauthorizedAutomationMutationError(
                    f"actor_id={actor_id} is not the guild owner "
                    f"(owner_id={guild_owner_id}); automation_rules "
                    "mutations are owner-only.",
                )

    async def _emit_event(
        self,
        *,
        mutation_id: str,
        rule_id: int,
        guild_id: int,
        mutation_type: str,
        name: str,
        committed_at: datetime,
    ) -> bool:
        from core.events import bus

        try:
            await bus.emit(
                EVT_AUTOMATION_RULE_CHANGED,
                mutation_id=mutation_id,
                rule_id=rule_id,
                guild_id=guild_id,
                mutation_type=mutation_type,
                name=name,
                occurred_at=committed_at.isoformat(),
            )
        except Exception:
            logger.exception(
                "AutomationMutationPipeline._emit_event: bus.emit failed "
                "for mutation_id=%s; DB state correct, event lost.",
                mutation_id,
            )
            return False
        return True


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


__all__ = [
    "EVT_AUTOMATION_RULE_CHANGED",
    "AutomationMutationError",
    "AutomationMutationPipeline",
    "AutomationMutationResult",
    "InvalidAutomationConfigError",
    "UnauthorizedAutomationMutationError",
    "UnknownAutomationRuleError",
]
