"""ResourceMutationPipeline — 6-step contract shell.

Phase 2a ships the **shape** of the resource mutation pipeline; Phase
7.5 fills in the actual provisioning behavior (channel creation, role
creation, category creation, delete, regenerate).  The shell lives
here so:

* Phase 2b's :class:`BindingMutationPipeline` can wire to the same
  contract for resolve-then-bind flows.
* Phase 4c diagnostics can reference the pipeline class by name
  without depending on Phase 7.5 being shipped.
* The AST invariant that blocks raw ``guild.create_text_channel`` /
  ``guild.create_role`` calls outside this module can land here in
  Phase 2a (warn-only) and promote to fatal in Phase 7.5.

The pipeline mirrors :class:`~governance.writes.GovernanceMutationPipeline`'s
6-step contract:

    1. Input validation
    2. Authority validation
    3. Read old state (current resource if mutating an existing one)
    4. DB write (provisioning audit row) + Discord create/delete in a
       single transactional commit boundary
    5. Cache invalidation (resource_validation_cache)
    6. Event emission (EVT_RESOURCE_PROVISIONED / EVT_RESOURCE_DELETED)

Steps 4-6 currently raise :exc:`NotImplementedError` — Phase 7.5 fills
them in.  The class structure + step signatures are stable; consumers
may import the class today knowing the contract will not change shape.
"""

from __future__ import annotations

import logging
from typing import Any

from core.resources.types import ResourceKind

logger = logging.getLogger("bot.resources.mutation")


class ResourceProvisioningError(Exception):
    """Base class for failures from :class:`ResourceMutationPipeline`."""


class UnauthorizedResourceProvisioningError(ResourceProvisioningError):
    """Raised when authority validation rejects the mutation."""


class ResourceMutationPipeline:
    """Centralized orchestration for guild-resource mutations.

    Instances are stateless — create one per mutation request.  Public
    methods (:meth:`provision_channel`, :meth:`provision_role`,
    :meth:`delete_resource`) currently raise :exc:`NotImplementedError`
    until Phase 7.5 fills them in.

    The class is intentionally importable + instantiable today so the
    Phase 4c diagnostics layer and the Phase 7.5 setup-pack runtime can
    reference it via type hints + isinstance checks.
    """

    def __init__(self) -> None:
        # No instance state; subclasses for test doubles override
        # individual steps.
        pass

    # ------------------------------------------------------------------
    # Steps 1-3 — pure validation, no side effects.  Implemented here
    # because the signatures are stable and useful from Phase 2a tests.
    # ------------------------------------------------------------------

    def _validate_inputs(self, kind: ResourceKind, payload: dict[str, Any]) -> None:
        """Reject malformed payloads before any side effect.

        Concrete payload schemas land in Phase 7.5 alongside the
        creation logic; this base implementation enforces that the
        caller supplied a non-empty dict and a recognized kind.
        """
        if not isinstance(payload, dict) or not payload:
            msg = f"empty or non-dict provisioning payload for kind={kind!r}"
            raise ResourceProvisioningError(msg)
        if not isinstance(kind, ResourceKind):
            msg = f"unexpected resource kind: {kind!r}"
            raise ResourceProvisioningError(msg)

    def _validate_authority(self, actor: object) -> None:
        """Reject unauthorized callers.

        Phase 7.5 binds this to :data:`~governance.permission_tiers.PermissionTier.ADMINISTRATOR`
        via :mod:`services.access_control_service` (Phase 4.5).  Until
        then this base implementation requires the caller to pass a
        non-None actor — callers must thread an explicit actor through
        rather than rely on implicit session state.
        """
        if actor is None:
            msg = "resource provisioning requires an authenticated actor"
            raise UnauthorizedResourceProvisioningError(msg)

    # ------------------------------------------------------------------
    # Steps 4-6 — Phase 7.5 fills these in.
    # ------------------------------------------------------------------

    async def provision_channel(
        self,
        guild: object,
        payload: dict[str, Any],
        actor: object,
    ) -> None:
        """Create a Discord channel from ``payload``.  Phase 7.5 implements."""
        del guild, payload, actor
        msg = (
            "ResourceMutationPipeline.provision_channel is not yet "
            "implemented — Phase 7.5 of the platform roadmap fills "
            "in resource creation."
        )
        raise NotImplementedError(msg)

    async def provision_role(
        self,
        guild: object,
        payload: dict[str, Any],
        actor: object,
    ) -> None:
        """Create a Discord role from ``payload``.  Phase 7.5 implements."""
        del guild, payload, actor
        msg = (
            "ResourceMutationPipeline.provision_role is not yet "
            "implemented — Phase 7.5 of the platform roadmap fills "
            "in resource creation."
        )
        raise NotImplementedError(msg)

    async def delete_resource(
        self,
        guild: object,
        kind: ResourceKind,
        resource_id: int,
        actor: object,
    ) -> None:
        """Delete a resource via Discord API.  Phase 7.5 implements."""
        del guild, kind, resource_id, actor
        msg = (
            "ResourceMutationPipeline.delete_resource is not yet "
            "implemented — Phase 7.5 of the platform roadmap fills "
            "in resource deletion + audit + rollback."
        )
        raise NotImplementedError(msg)


__all__ = [
    "ResourceMutationPipeline",
    "ResourceProvisioningError",
    "UnauthorizedResourceProvisioningError",
]
