"""Phase 1c — Resource capability declarations.

A subsystem declares the platform resources it needs at runtime via
``ResourceRequirement`` entries on its :class:`SubsystemSchema`.

Why this lives in its own module:

* Resources are the *platform substrate* subsystems run on — channels,
  roles, categories, threads. They are not the same kind of thing as
  bindings or settings, even though a binding may eventually point at a
  resource.
* Phase 2c's ``core/resources/`` runtime will absorb resource discovery
  + validation; declaring requirements here lets Phase 4c diagnostics
  cross-reference "which subsystems want this resource" without coupling
  to a specific provisioning path.
* Phase 7.5's resource provisioning runtime consumes ``ProvisioningHint``
  to decide what to create when an operator asks for a setup pack.

Public surface:

* :class:`ResourceKind` — enumerates the resource taxonomy.
* :class:`ProvisioningHint` — operator-facing creation guidance.
* :class:`ResourceRequirement` — a subsystem's declaration of what it
  needs.

The :class:`SubsystemSchema` in ``subsystem_schema.py`` imports these
types as an optional ``resource_requirements`` list field.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ResourceKind(Enum):
    """The platform's first-class resource types.

    Channels and roles are *peers* — both are typed ``GuildResource``
    subclasses in Phase 2c, with their own discovery, validation, and
    provisioning paths.
    """

    CHANNEL = "channel"
    ROLE = "role"
    CATEGORY = "category"
    THREAD = "thread"


class ProvisioningPriority(Enum):
    """How important it is that the resource exists.

    Drives Phase 4c diagnostics severity and Phase 7.5 setup pack
    behavior.  A ``REQUIRED`` resource missing is a fatal finding; a
    ``RECOMMENDED`` resource missing is a warn; ``OPTIONAL`` is info-only.
    """

    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


@dataclass(frozen=True)
class ProvisioningHint:
    """Operator-facing guidance for creating the resource on demand.

    All fields except ``priority`` are advisory — the operator's setup
    flow may override any suggestion.  ``priority`` is the diagnostic
    severity gate.
    """

    priority: ProvisioningPriority
    suggested_name: str = ""
    suggested_category: str = ""  # parent category name (channel only)
    suggested_permissions: tuple[str, ...] = ()  # canonical perm names; empty = inherit


@dataclass(frozen=True)
class ResourceRequirement:
    """A subsystem's declaration that it needs a specific resource at runtime.

    Resources are referenced from the same subsystem's bindings via the
    ``binding_name`` cross-link.  Same channel may satisfy multiple
    subsystems' ``log_destination`` intents; the resource diagnostics
    layer (Phase 4c) surfaces shared usage.

    Fields:

    kind:
        Which resource type the subsystem expects.
    intent:
        What the subsystem uses this resource for, e.g.
        ``"log_destination"``, ``"announcement_target"``,
        ``"role_threshold_anchor"``.  Free-form within a subsystem; used
        by diagnostics to group findings.
    provisioning:
        :class:`ProvisioningHint` driving auto-provisioning suggestions.
    binding_name:
        Name of the :class:`~core.runtime.subsystem_schema.BindingSpec`
        that points at the runtime value of this resource.  Empty if the
        subsystem declares the requirement but does not bind it (rare —
        most subsystems do bind).
    description:
        Short human-readable description for the wizard UI.
    """

    kind: ResourceKind
    intent: str
    provisioning: ProvisioningHint
    binding_name: str = ""
    description: str = ""


@dataclass(frozen=True)
class _ResourceRequirementSnapshot:
    """Snapshot shape returned by the diagnostics provider."""

    subsystem: str
    kind: str
    intent: str
    priority: str
    binding_name: str
    suggested_name: str


def snapshot_resource_requirements(
    schemas_by_subsystem: dict[str, list[ResourceRequirement]],
) -> list[dict]:
    """Flatten resource requirements into the snapshot shape.

    Used by the ``!platform resource-requirements`` admin command via
    the diagnostics provider registered in
    :mod:`core.runtime.subsystem_schema`.
    """
    out: list[dict] = []
    for subsystem, reqs in sorted(schemas_by_subsystem.items()):
        for r in reqs:
            out.append(
                {
                    "subsystem": subsystem,
                    "kind": r.kind.value,
                    "intent": r.intent,
                    "priority": r.provisioning.priority.value,
                    "binding_name": r.binding_name,
                    "suggested_name": r.provisioning.suggested_name,
                },
            )
    return out


__all__ = [
    "ProvisioningHint",
    "ProvisioningPriority",
    "ResourceKind",
    "ResourceRequirement",
    "snapshot_resource_requirements",
]


# Suppress unused-warning for the dataclass kept for type stability.
_ = field
_ = _ResourceRequirementSnapshot
