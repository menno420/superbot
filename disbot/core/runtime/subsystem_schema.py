"""Phase 1a — Subsystem-owned configuration schema protocol.

A subsystem declares its guild-level configuration shape via a
:class:`SubsystemSchema` instance registered in ``cog_load``.  The
platform reads the schema; the subsystem owns it.

Public surface:

* :class:`BindingKind` — typed resource-kind enumeration for bindings.
* :class:`BindingSpec` — a named "slot" the operator fills.
* :class:`SettingSpec` — a typed, validated, keyed scalar setting.
* :class:`CompletenessReport` — diagnostic shape returned by a schema's
  ``completeness_rule``.
* :class:`SubsystemSchema` — the full per-subsystem declaration.
* ``register(schema)`` / ``get_schema(name)`` / ``all_schemas()`` /
  ``registered_subsystems()`` — the registry surface, mirroring the
  ``diagnostics_service`` / ``persistent_views`` self-registration
  pattern.

Why this lives in ``core/runtime/`` rather than ``utils/``:

* Schemas are platform-runtime primitives: they reference capability
  strings declared in :mod:`utils.subsystem_registry`, they participate
  in Phase 6's identity contract, and Phase 4a's setup health service
  introspects them.
* ``utils/`` is reserved for pure helpers without runtime semantics.

Cross-track integration:

* The optional ``resource_requirements`` field on a schema is typed as
  ``list[ResourceRequirement]`` (Phase 1c).  Declaring resources here
  keeps the schema the single declaration point a subsystem owns, even
  though resources are conceptually a Track-C concern.
* Per-user participation shape lives in
  :mod:`core.runtime.participation_schema` (Phase 1b) — a sibling
  registry.  Guild config and participation are never mixed into the
  same schema.

The registry is intentionally re-registration-friendly (hot-reload-safe);
re-registering a subsystem overwrites with a DEBUG log line so accidental
duplicates are visible.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.runtime.resource_specs import (
    ResourceRequirement,
    snapshot_resource_requirements,
)

logger = logging.getLogger("bot.subsystem_schema")


class BindingKind(Enum):
    """Resource kinds a :class:`BindingSpec` may point at.

    Matches :class:`~core.runtime.resource_specs.ResourceKind` plus
    ``MEMBER`` (which is not provisioned but is a valid binding target).
    """

    CHANNEL = "channel"
    ROLE = "role"
    CATEGORY = "category"
    THREAD = "thread"
    MEMBER = "member"


@dataclass(frozen=True)
class BindingSpec:
    """A named slot in a subsystem's guild configuration.

    Bindings are runtime-typed pointers at platform resources — channels,
    roles, categories.  Phase 2b stores their values in the
    ``subsystem_bindings`` table; Phase 7's wizard renders them via the
    :class:`~core.runtime.components.binding_panel.BindingPanel`.

    Fields:

    name:
        Unique-within-subsystem identifier (e.g. ``"announce_channel"``).
    kind:
        Which resource type the binding accepts.
    required:
        If ``True``, an unbound slot is a fatal completeness finding.

    Hint:
        Short human-readable description rendered by the wizard.
    capability_required:
        Three-part capability string (``{subsystem}.{resource}.{action}``)
        the operator must hold to bind the slot.  Validated against
        :data:`utils.subsystem_registry.SUBSYSTEMS` at registry
        validation time.
    """

    name: str
    kind: BindingKind
    required: bool
    hint: str
    capability_required: str


@dataclass(frozen=True)
class SettingSpec:
    """A typed, validated, keyed scalar setting in a subsystem's config.

    Settings differ from bindings: a setting carries a value (int, str,
    bool) and is not a pointer at a guild resource.  Bindings own the
    "this channel does X" shape; settings own the "X happens every N
    seconds" shape.

    Fields:

    name:
        Unique-within-subsystem identifier.
    value_type:
        The Python type the value is coerced to.  ``int``, ``str``,
        ``bool``, or ``float``.
    default:
        Default value when unset.
    settings_key:
        Canonical key string from :mod:`utils.settings_keys`.  Empty if
        the setting is not yet migrated off ``db.get_setting``.
    capability_required:
        Three-part capability string the operator must hold to mutate.
        Empty if no auth is required (uncommon).

    Hint:
        Short human-readable description rendered by the wizard.
    validator:
        Optional callable raising ``ValueError`` on invalid input.
    """

    name: str
    value_type: type
    default: Any
    settings_key: str = ""
    capability_required: str = ""
    hint: str = ""
    validator: Callable[[Any], None] | None = None


@dataclass(frozen=True)
class CompletenessReport:
    """Diagnostic shape produced by a schema's ``completeness_rule``.

    Phase 4a's setup health service surfaces these reports to operators.
    The shape mirrors the existing finding-tier model in
    :mod:`utils.subsystem_registry` so the wizard renders both via the
    same :class:`DiagnosticsPanel` (Phase 5b).
    """

    subsystem: str
    complete: bool
    missing_bindings: tuple[str, ...] = ()
    missing_settings: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()


@dataclass(frozen=True)
class SubsystemSchema:
    """A subsystem's complete guild-level configuration declaration.

    Registered in ``cog_load`` via :func:`register`.  Once registered the
    schema is read-only — re-registration replaces atomically (and logs).

    Fields:

    subsystem:
        Must match a key in :data:`utils.subsystem_registry.SUBSYSTEMS`.
        Validated at registry validation time.
    bindings:
        Named slots the operator fills via the wizard.
    settings:
        Typed scalar settings the operator configures.
    resource_requirements:
        Phase 1c declarations of platform resources this subsystem
        consumes at runtime.  Optional but recommended for any subsystem
        with bindings.
    version:
        Schema version.  Phase 1 schemas start at ``1``; bumped on
        breaking shape changes so Phase 4a diagnostics can warn on
        version drift between code and stored config.
    completeness_rule:
        Optional callable ``(guild_id) -> CompletenessReport`` that
        runs Phase 4a setup-health checks.  Phase 4a registers a default
        rule that just inspects ``bindings`` and ``settings``; this hook
        is for subsystems that need extra logic (e.g. "needs at least 3
        moderators").
    """

    subsystem: str
    bindings: tuple[BindingSpec, ...] = ()
    settings: tuple[SettingSpec, ...] = ()
    resource_requirements: tuple[ResourceRequirement, ...] = ()
    version: int = 1
    completeness_rule: Callable[[int], CompletenessReport] | None = None


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, SubsystemSchema] = {}


def register(schema: SubsystemSchema) -> None:
    """Register ``schema`` under its subsystem name.

    Re-registration is allowed (hot-reload-friendly) and emits a
    DEBUG-level log entry so accidental duplicates are visible.

    The registry primitive does NOT validate ``schema.subsystem`` against
    :data:`utils.subsystem_registry.SUBSYSTEMS` here — validation runs at
    startup via the registry validator extension to avoid an import-order
    dependency on the subsystem manifest.
    """
    if schema.subsystem in _REGISTRY:
        logger.debug(
            "subsystem_schema: re-registering schema for %r",
            schema.subsystem,
        )
    _REGISTRY[schema.subsystem] = schema


def get_schema(subsystem: str) -> SubsystemSchema | None:
    """Return the registered schema for ``subsystem``, or ``None``."""
    return _REGISTRY.get(subsystem)


def all_schemas() -> dict[str, SubsystemSchema]:
    """Return a copy of the schema registry, keyed by subsystem name."""
    return dict(_REGISTRY)


def registered_subsystems() -> list[str]:
    """Return registered subsystems, alphabetically sorted."""
    return sorted(_REGISTRY)


def _reset_for_tests() -> None:
    """Wipe the registry.  Tests call this in their setup/teardown fixture."""
    _REGISTRY.clear()


# ---------------------------------------------------------------------------
# Diagnostics provider — registers at import time
# ---------------------------------------------------------------------------


def _schemas_snapshot() -> dict[str, Any]:
    """Snapshot provider for ``!platform schemas``.

    Returns a dict shaped for ``_fmt_snapshot_value`` rendering: counts +
    a flat list of subsystem/binding/setting/resource declarations.
    """
    schemas = all_schemas()
    binding_total = sum(len(s.bindings) for s in schemas.values())
    setting_total = sum(len(s.settings) for s in schemas.values())
    resource_total = sum(len(s.resource_requirements) for s in schemas.values())

    by_subsystem: dict[str, dict[str, int]] = {}
    for name, schema in schemas.items():
        by_subsystem[name] = {
            "bindings": len(schema.bindings),
            "settings": len(schema.settings),
            "resources": len(schema.resource_requirements),
            "version": schema.version,
        }

    return {
        "registered": len(schemas),
        "bindings_total": binding_total,
        "settings_total": setting_total,
        "resources_total": resource_total,
        "by_subsystem": by_subsystem,
    }


def _resource_requirements_snapshot() -> list[dict]:
    """Snapshot provider for ``!platform resource-requirements``."""
    schemas = all_schemas()
    return snapshot_resource_requirements(
        {name: list(s.resource_requirements) for name, s in schemas.items()},
    )


# Defer the actual registration to a helper so tests can opt out.
def _register_diagnostics_providers() -> None:
    from services import diagnostics_service

    diagnostics_service.register("schemas", _schemas_snapshot)
    diagnostics_service.register(
        "resource_requirements",
        _resource_requirements_snapshot,
    )


_register_diagnostics_providers()


__all__ = [
    "BindingKind",
    "BindingSpec",
    "CompletenessReport",
    "SettingSpec",
    "SubsystemSchema",
    "all_schemas",
    "get_schema",
    "register",
    "registered_subsystems",
]
