"""Binding mutation pipeline — Phase 2b.

The canonical write path for ``subsystem_bindings``.  Mirrors the
6-step contract from :class:`~governance.writes.GovernanceMutationPipeline`:

  1. Input validation       — subsystem declared, binding declared,
                              kind matches the declared ``BindingSpec``
  2. Authority validation   — capability-native (ADR-005 A1): the actor
                              must hold ``BindingSpec.capability_required``
  3. Target validation      — dispatch via
                              :func:`core.runtime.bindings.validate_binding_target`
                              (resource kinds vs MEMBER kind)
  4. Read old value         — for the audit row
  5. DB write + audit       — single transaction via
                              :mod:`utils.db.bindings`
  6. Cache invalidation     — guild_config namespace for this binding
  7. Event emission         — EVT_BINDING_CHANGED

If event emission raises **after** a successful DB commit, the error
is logged but not re-raised; the DB state is correct and the next
event consumer will reconcile on its next read (mirrors
:class:`GovernanceMutationPipeline`'s best-effort emission contract).

Hard limits for Phase 2b:

  * No setup wizard UI integration — that is Phase 7.
  * No resource provisioning — :class:`~core.resources.mutation.ResourceMutationPipeline`
    handles channel/role creation in Phase 7.5.
  * No permission-aware target validation — Phase 4.5 hook
    (:func:`core.resources.discovery.validate_resource_permissions`)
    is still NotImplementedError.
  * Authority is capability-native (ADR-005 A1): resolved via
    :func:`governance.capability.actor_holds_capability` against
    ``BindingSpec.capability_required`` (empty resolves to the admin floor).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import discord

from core.resources.status import ResourceStatus
from core.runtime.bindings import BindingValue, get_binding, validate_binding_target
from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SubsystemSchema,
    get_schema,
)
from services.audit_events import emit_audit_action
from utils.db import bindings as bindings_db
from utils.subsystem_registry import SUBSYSTEMS

logger = logging.getLogger("bot.services.binding_mutation")

# ---------------------------------------------------------------------------
# Canonical event name + result type
# ---------------------------------------------------------------------------

EVT_BINDING_CHANGED = "bindings.changed"


class BindingMutationError(Exception):
    """Base class for failures from :class:`BindingMutationPipeline`."""


class UnknownSubsystemError(BindingMutationError):
    """Raised when the mutation targets a subsystem not in SUBSYSTEMS."""


class UndeclaredBindingError(BindingMutationError):
    """Raised when the binding_name is not declared in the SubsystemSchema."""


class BindingKindMismatchError(BindingMutationError):
    """Raised when the declared kind disagrees with the caller's kind."""


class UnauthorizedBindingMutationError(BindingMutationError):
    """Raised when the calling member does not hold sufficient authority."""


@dataclass(frozen=True)
class BindingMutationResult:
    """Outcome of a successful (or partially successful) mutation."""

    mutation_id: str
    guild_id: int
    subsystem: str
    binding_name: str
    old_target_id: int | None
    new_target_id: int | None
    old_status: ResourceStatus
    new_status: ResourceStatus
    committed_at: datetime
    event_emitted: bool


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class BindingMutationPipeline:
    """Centralized orchestration for ``subsystem_bindings`` writes.

    Instances are stateless — create one per mutation request.  Two
    public methods:

    * :meth:`set_binding` — bind a target to a slot (or rebind).
    * :meth:`clear_binding` — clear an existing binding back to
      ``UNRESOLVED``.

    Both methods follow the same 7-step contract documented in the
    module docstring.  Callers MUST NOT touch
    :mod:`utils.db.bindings`'s mutation primitives directly; the
    pipeline is the only legitimate writer.
    """

    def __init__(self) -> None:
        # No instance state.
        pass

    # ------------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------------

    async def set_binding(
        self,
        guild: discord.Guild,
        subsystem: str,
        binding_name: str,
        kind: BindingKind,
        target_id: int,
        actor: discord.Member,
    ) -> BindingMutationResult:
        """Bind ``target_id`` to ``(subsystem, binding_name)``.

        Raises:
            UnknownSubsystemError: ``subsystem`` not in SUBSYSTEMS.
            UndeclaredBindingError: schema does not declare ``binding_name``.
            BindingKindMismatchError: declared kind disagrees with ``kind``.
            UnauthorizedBindingMutationError: actor below the authority floor.
        """
        spec = self._resolve_spec(subsystem, binding_name, kind)
        await self._validate_authority(spec, actor)

        new_status = await validate_binding_target(guild, kind, target_id)
        old = await get_binding(guild.id, subsystem, binding_name)
        return await self._commit(
            guild=guild,
            subsystem=subsystem,
            binding_name=spec.name,
            kind=kind,
            new_target_id=target_id,
            new_status=new_status,
            old=old,
            actor=actor,
            action_label="set",
        )

    async def clear_binding(
        self,
        guild: discord.Guild,
        subsystem: str,
        binding_name: str,
        kind: BindingKind,
        actor: discord.Member,
    ) -> BindingMutationResult:
        """Clear the binding at ``(subsystem, binding_name)``.

        The slot row remains so the schema-declared binding stays
        discoverable; ``target_id`` is set to NULL and ``status`` to
        ``unresolved``.
        """
        spec = self._resolve_spec(subsystem, binding_name, kind)
        await self._validate_authority(spec, actor)

        old = await get_binding(guild.id, subsystem, binding_name)
        if old.target_id is None and old.last_updated_at is None:
            # Nothing to clear; treat as a no-op success rather than
            # raise — clearing an already-unbound slot is idempotent.
            return BindingMutationResult(
                mutation_id=str(uuid.uuid4()),
                guild_id=guild.id,
                subsystem=subsystem,
                binding_name=binding_name,
                old_target_id=None,
                new_target_id=None,
                old_status=ResourceStatus.UNRESOLVED,
                new_status=ResourceStatus.UNRESOLVED,
                committed_at=_now_utc(),
                event_emitted=False,
            )

        mutation_id = str(uuid.uuid4())
        try:
            await bindings_db.clear_with_audit(
                guild_id=guild.id,
                subsystem=subsystem,
                binding_name=binding_name,
                actor_id=actor.id,
                actor_type="user",
                mutation_id=mutation_id,
                old_target_id=old.target_id,
                old_status=old.status.value,
            )
        except Exception:
            logger.exception(
                "BindingMutationPipeline.clear_binding: DB transaction "
                "failed for (guild=%d, subsystem=%r, binding=%r); "
                "no cache invalidation, no event emission.",
                guild.id,
                subsystem,
                binding_name,
            )
            raise

        committed_at = _now_utc()
        # Phase 9c.2: companion ``audit.action_recorded`` event via the
        # shared publisher. Best-effort; failure is logged inside the
        # helper, not propagated.
        await emit_audit_action(
            mutation_id=mutation_id,
            subsystem=subsystem,
            mutation_type="clear_binding",
            target=f"binding:{subsystem}.{binding_name}",
            scope="guild",
            guild_id=guild.id,
            prev_value=str(old.target_id) if old.target_id is not None else None,
            new_value=None,
            actor_id=actor.id,
            actor_type="user",
            occurred_at=committed_at,
        )
        event_emitted = await self._emit_event(
            mutation_id=mutation_id,
            guild_id=guild.id,
            subsystem=subsystem,
            binding_name=binding_name,
            old_target_id=old.target_id,
            new_target_id=None,
            old_status=old.status.value,
            new_status=ResourceStatus.UNRESOLVED.value,
            committed_at=committed_at,
        )
        self._invalidate_cache(guild.id, subsystem, binding_name)
        return BindingMutationResult(
            mutation_id=mutation_id,
            guild_id=guild.id,
            subsystem=subsystem,
            binding_name=binding_name,
            old_target_id=old.target_id,
            new_target_id=None,
            old_status=old.status,
            new_status=ResourceStatus.UNRESOLVED,
            committed_at=committed_at,
            event_emitted=event_emitted,
        )

    # ------------------------------------------------------------------
    # Step helpers
    # ------------------------------------------------------------------

    def _resolve_spec(
        self,
        subsystem: str,
        binding_name: str,
        kind: BindingKind,
    ) -> BindingSpec:
        """Steps 1: subsystem declared, binding declared, kind matches."""
        if subsystem not in SUBSYSTEMS:
            msg = (
                f"unknown subsystem {subsystem!r}; "
                f"not in utils.subsystem_registry.SUBSYSTEMS"
            )
            raise UnknownSubsystemError(msg)

        schema: SubsystemSchema | None = get_schema(subsystem)
        if schema is None:
            msg = (
                f"subsystem {subsystem!r} has no registered SubsystemSchema; "
                f"register one in the cog's cog_load() before binding"
            )
            raise UndeclaredBindingError(msg)

        for spec in schema.bindings:
            if spec.name == binding_name:
                if spec.kind != kind:
                    msg = (
                        f"binding {subsystem!r}/{binding_name!r} declared "
                        f"kind={spec.kind!r} but caller supplied kind={kind!r}"
                    )
                    raise BindingKindMismatchError(msg)
                return spec

        msg = (
            f"binding {binding_name!r} not declared in SubsystemSchema "
            f"for {subsystem!r}; declared bindings: "
            f"{[s.name for s in schema.bindings]}"
        )
        raise UndeclaredBindingError(msg)

    async def _validate_authority(
        self,
        spec: BindingSpec,
        actor: discord.Member,
    ) -> None:
        """Step 2: capability-native authority (ADR-005 A1).

        The actor must hold ``spec.capability_required``; an empty capability
        resolves to the administrator floor.  Resolution (and any per-guild
        revoke overlay) lives in
        :func:`governance.capability.actor_holds_capability`.
        """
        from governance.capability import actor_holds_capability

        decision = await actor_holds_capability(
            actor,
            getattr(actor, "guild", None),
            spec.capability_required,
            actor_type="user",
        )
        if not decision.allowed:
            raise UnauthorizedBindingMutationError(decision.reason)

    async def _commit(
        self,
        *,
        guild: discord.Guild,
        subsystem: str,
        binding_name: str,
        kind: BindingKind,
        new_target_id: int,
        new_status: ResourceStatus,
        old: BindingValue,
        actor: discord.Member,
        action_label: str,
    ) -> BindingMutationResult:
        """Steps 4-7: read-old, write+audit, invalidate, emit."""
        del action_label  # currently single shape; reserved for future actions
        mutation_id = str(uuid.uuid4())
        try:
            await bindings_db.upsert_with_audit(
                guild_id=guild.id,
                subsystem=subsystem,
                binding_name=binding_name,
                kind=kind.value,
                target_id=new_target_id,
                status=new_status.value,
                actor_id=actor.id,
                actor_type="user",
                mutation_id=mutation_id,
                old_target_id=old.target_id,
                old_status=old.status.value,
            )
        except Exception:
            logger.exception(
                "BindingMutationPipeline._commit: DB transaction "
                "failed for (guild=%d, subsystem=%r, binding=%r); "
                "no cache invalidation, no event emission.",
                guild.id,
                subsystem,
                binding_name,
            )
            raise

        committed_at = _now_utc()
        # Phase 9c.2: companion ``audit.action_recorded`` event via the
        # shared publisher. Best-effort; failure is logged inside the
        # helper, not propagated.
        await emit_audit_action(
            mutation_id=mutation_id,
            subsystem=subsystem,
            mutation_type="upsert_binding",
            target=f"binding:{subsystem}.{binding_name}",
            scope="guild",
            guild_id=guild.id,
            prev_value=str(old.target_id) if old.target_id is not None else None,
            new_value=str(new_target_id),
            actor_id=actor.id,
            actor_type="user",
            occurred_at=committed_at,
        )
        event_emitted = await self._emit_event(
            mutation_id=mutation_id,
            guild_id=guild.id,
            subsystem=subsystem,
            binding_name=binding_name,
            old_target_id=old.target_id,
            new_target_id=new_target_id,
            old_status=old.status.value,
            new_status=new_status.value,
            committed_at=committed_at,
        )
        self._invalidate_cache(guild.id, subsystem, binding_name)
        return BindingMutationResult(
            mutation_id=mutation_id,
            guild_id=guild.id,
            subsystem=subsystem,
            binding_name=binding_name,
            old_target_id=old.target_id,
            new_target_id=new_target_id,
            old_status=old.status,
            new_status=new_status,
            committed_at=committed_at,
            event_emitted=event_emitted,
        )

    def _invalidate_cache(
        self,
        guild_id: int,
        subsystem: str,
        binding_name: str,
    ) -> None:
        """Step 6: invalidate the guild_config namespace for this binding.

        Phase 2b does not write to ``guild_config`` for bindings yet —
        that wiring lands in Phase 4c when binding values are read via
        typed accessors instead of direct DB reads.  This method exists
        as the documented hook so the wiring change is a one-line
        addition.
        """
        logger.debug(
            "BindingMutationPipeline: cache invalidation hook for "
            "guild=%d subsystem=%r binding=%r (no-op until Phase 4c)",
            guild_id,
            subsystem,
            binding_name,
        )

    async def _emit_event(
        self,
        *,
        mutation_id: str,
        guild_id: int,
        subsystem: str,
        binding_name: str,
        old_target_id: int | None,
        new_target_id: int | None,
        old_status: str,
        new_status: str,
        committed_at: datetime,
    ) -> bool:
        """Step 7: best-effort event emission.

        Returns ``True`` if the event was emitted successfully; ``False``
        if emission raised.  Emission failures after a successful DB
        commit are logged and swallowed — the DB state is correct, and
        Phase 4c's event-driven reconciliation will catch up on the
        next emit (mirrors :class:`GovernanceMutationPipeline`'s
        best-effort contract).
        """
        from core.events import bus

        try:
            await bus.emit(
                EVT_BINDING_CHANGED,
                mutation_id=mutation_id,
                guild_id=guild_id,
                subsystem=subsystem,
                binding_name=binding_name,
                old_target_id=old_target_id,
                new_target_id=new_target_id,
                old_status=old_status,
                new_status=new_status,
                occurred_at=committed_at.isoformat(),
            )
        except Exception:
            logger.exception(
                "BindingMutationPipeline._emit_event: emission failed for "
                "mutation_id=%s; DB state is correct, event lost.",
                mutation_id,
            )
            return False
        return True


def _now_utc() -> datetime:
    """Return a tz-aware "now" — INV-N forbids bare datetime.utcnow."""
    return datetime.now(timezone.utc)


__all__ = [
    "EVT_BINDING_CHANGED",
    "BindingKindMismatchError",
    "BindingMutationError",
    "BindingMutationPipeline",
    "BindingMutationResult",
    "UnauthorizedBindingMutationError",
    "UndeclaredBindingError",
    "UnknownSubsystemError",
]
