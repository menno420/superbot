"""Subsystem bindings — typed runtime layer (Phase 2b).

The platform's read surface for ``subsystem_bindings``.  Wraps
:mod:`utils.db.bindings` with a typed :class:`BindingValue` so callers
never touch raw target IDs outside the binding/resource validation
layer, and adds the small dispatch abstraction that routes binding
targets to the right validator (resource kinds → ``core.resources``;
member kind → ``core.runtime.guild_resources.resolve_member``).

Public surface:

* :class:`BindingValue` — frozen typed read result.
* :func:`get_binding` — typed accessor; returns ``UNRESOLVED`` on miss.
* :func:`validate_binding_target` — dispatch by kind to the appropriate
  validator.  Resolves the long-standing question raised in
  ``docs/archive/phase_2b_bindings_plan.md`` about member bindings.

Phase 2b does NOT add a ``set_binding`` write here — writes go through
:class:`~services.binding_mutation.BindingMutationPipeline` which
calls into :mod:`utils.db.bindings` directly.  Keeping the write path
out of the read module preserves the layering rule that callers can
import the read API without pulling in the mutation pipeline.

Diagnostics: this module self-registers a snapshot provider named
``bindings`` so ``!platform bindings`` can display per-guild histograms.
The provider returns module-level state only (registered taxonomies,
counts of known events); per-guild histograms are fetched by the admin
command directly from :mod:`utils.db.bindings`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import discord

from core.resources import discovery
from core.resources.status import ResourceStatus
from core.resources.types import ResourceKind
from core.runtime import guild_resources
from core.runtime.subsystem_schema import BindingKind
from utils.db import bindings as bindings_db

logger = logging.getLogger("bot.bindings")


# ---------------------------------------------------------------------------
# Typed read result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BindingValue:
    """Typed snapshot of a subsystem binding's runtime state.

    A binding always has a slot identity (subsystem + binding_name +
    kind); the ``target_id`` is the runtime value the operator filled
    in (or ``None`` for an unbound slot).

    Status semantics match :class:`core.resources.status.ResourceStatus`
    — Phase 2a's structural-only validation applies to bindings too.
    Phase 4.5 will add a permission-aware sibling field.

    Fields:

    guild_id, subsystem, binding_name:
        Composite identity.
    kind:
        The expected target type.  Must match the corresponding
        :class:`~core.runtime.subsystem_schema.BindingSpec.kind`.
    target_id:
        The discord snowflake the slot points at, or ``None`` when
        unbound.
    status:
        Last-known validation status.  ``UNRESOLVED`` for slots that
        have never been validated (including those returned by
        :func:`get_binding` when no DB row exists).
    last_validated_at / last_updated_at:
        Audit timestamps.  ``None`` when no row exists.
    version:
        Row-level revision counter; bumped on every mutation.  Zero
        when no row exists.
    """

    guild_id: int
    subsystem: str
    binding_name: str
    kind: BindingKind
    target_id: int | None = None
    status: ResourceStatus = ResourceStatus.UNRESOLVED
    last_validated_at: datetime | None = None
    last_updated_at: datetime | None = None
    version: int = 0

    @property
    def is_bound(self) -> bool:
        """True iff a target is bound and structurally valid."""
        return self.target_id is not None and self.status is ResourceStatus.BOUND


# ---------------------------------------------------------------------------
# Binding-target validator dispatch
# ---------------------------------------------------------------------------

# Resource-kind aliases for the dispatch.  Phase 2b's design decision
# (see docs/archive/phase_2b_bindings_plan.md): resource kinds use
# ``core.resources.discovery``; member kind uses ``guild_resources``.
_RESOURCE_KIND_MAP: dict[BindingKind, ResourceKind] = {
    BindingKind.CHANNEL: ResourceKind.CHANNEL,
    BindingKind.ROLE: ResourceKind.ROLE,
    BindingKind.CATEGORY: ResourceKind.CATEGORY,
    BindingKind.THREAD: ResourceKind.THREAD,
}


async def validate_binding_target(
    guild: discord.Guild,
    kind: BindingKind,
    target_id: int,
) -> ResourceStatus:
    """Validate that ``target_id`` exists in ``guild`` for ``kind``.

    Dispatches by kind:

    * ``CHANNEL`` / ``ROLE`` / ``CATEGORY`` / ``THREAD`` →
      :func:`core.resources.discovery.validate_resource`
      (``persist=False`` — Phase 2b does not write to the resource
      cache; the binding row tracks its own status).
    * ``MEMBER`` →
      :func:`core.runtime.guild_resources.resolve_member`
      (sync; returns ``None`` for missing members).

    Returns :class:`ResourceStatus.BOUND` when the target is found,
    :class:`ResourceStatus.MISSING` otherwise.  Resource-kind validation
    may also return :class:`ResourceStatus.INVALID` for wrong-type IDs
    (channel ID pointing at a category, etc.).
    """
    if kind is BindingKind.MEMBER:
        member = guild_resources.resolve_member(guild, target_id)
        return ResourceStatus.BOUND if member is not None else ResourceStatus.MISSING

    resource_kind = _RESOURCE_KIND_MAP.get(kind)
    if resource_kind is None:
        # Defensive — should not happen because BindingKind is exhaustive
        # over the dispatch table, but a future enum addition without a
        # validator update would land here.
        logger.warning(
            "validate_binding_target: no validator for kind=%r; "
            "returning UNRESOLVED.  Add the kind to _RESOURCE_KIND_MAP "
            "or extend the MEMBER branch.",
            kind,
        )
        return ResourceStatus.UNRESOLVED

    return await discovery.validate_resource(
        guild,
        resource_kind,
        target_id,
        persist=False,
    )


# ---------------------------------------------------------------------------
# Typed accessor
# ---------------------------------------------------------------------------


async def get_binding(
    guild_id: int,
    subsystem: str,
    binding_name: str,
    *,
    expected_kind: BindingKind | None = None,
) -> BindingValue:
    """Return the typed :class:`BindingValue` for a slot.

    ``expected_kind`` lets the caller assert what kind the slot should
    be; if the DB row's kind disagrees, this function logs a warning
    and uses the DB-stored kind in the returned value.  The caller can
    treat that as an invariant violation (a schema migration is needed).

    If no row exists, returns ``BindingValue`` with ``target_id=None``,
    ``status=UNRESOLVED``, and ``version=0``.  Callers that need to
    distinguish "slot never bound" from "slot cleared" should consult
    :data:`BindingValue.last_updated_at` (``None`` for never-bound).
    """
    row = await bindings_db.get_one(guild_id, subsystem, binding_name)
    if row is None:
        return BindingValue(
            guild_id=guild_id,
            subsystem=subsystem,
            binding_name=binding_name,
            kind=expected_kind or BindingKind.CHANNEL,
            status=ResourceStatus.UNRESOLVED,
        )

    try:
        kind = BindingKind(row["kind"])
    except ValueError:
        logger.error(
            "get_binding: row carries unknown kind=%r for "
            "(guild=%d, subsystem=%r, binding=%r); using fallback.",
            row["kind"],
            guild_id,
            subsystem,
            binding_name,
        )
        kind = expected_kind or BindingKind.CHANNEL

    if expected_kind is not None and kind != expected_kind:
        logger.warning(
            "get_binding: stored kind=%r differs from expected_kind=%r "
            "for (guild=%d, subsystem=%r, binding=%r) — schema drift.",
            kind,
            expected_kind,
            guild_id,
            subsystem,
            binding_name,
        )

    try:
        status = ResourceStatus(row["status"])
    except ValueError:
        logger.error(
            "get_binding: row carries unknown status=%r; using UNRESOLVED.",
            row["status"],
        )
        status = ResourceStatus.UNRESOLVED

    return BindingValue(
        guild_id=row["guild_id"],
        subsystem=row["subsystem"],
        binding_name=row["binding_name"],
        kind=kind,
        target_id=row["target_id"],
        status=status,
        last_validated_at=row["last_validated_at"],
        last_updated_at=row["last_updated_at"],
        version=row["version"],
    )


# ---------------------------------------------------------------------------
# Diagnostics provider — registers at import time
# ---------------------------------------------------------------------------


def _bindings_snapshot() -> dict[str, Any]:
    """Snapshot provider for ``!platform bindings``.

    Returns *process-local* state only — per-guild histograms come from
    :mod:`utils.db.bindings` via the admin command, since the
    diagnostics provider contract is synchronous and DB-free.
    """
    return {
        "kinds": [k.value for k in BindingKind],
        "validator_dispatch": {
            **{k.value: "resource" for k in _RESOURCE_KIND_MAP},
            BindingKind.MEMBER.value: "member",
        },
    }


def _register_diagnostics_providers() -> None:
    from services import diagnostics_service

    diagnostics_service.register("bindings", _bindings_snapshot)


_register_diagnostics_providers()


__all__ = [
    "BindingValue",
    "get_binding",
    "validate_binding_target",
]
