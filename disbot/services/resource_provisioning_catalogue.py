"""Resource provisioning catalogue — S2.5 of the Global Settings & Customization Manager.

A frozen, read-only catalogue of every :class:`ResourceRequirement`
declared across all subsystem schemas, cross-linked with the
:class:`BindingSpec` that owns the runtime value of the resource.

Mirrors the shape of :mod:`core.runtime.settings_registry` and
:mod:`services.customization_catalogue`: the builder walks
:func:`core.runtime.subsystem_schema.all_schemas` once, returns a
frozen :class:`ProvisioningCatalogue`, and caches it for diagnostics.

Why this is its own catalogue:

* `ResourceRequirement` lives in :mod:`core.runtime.resource_specs`
  (Phase 1c). It carries the *creation* metadata an operator needs to
  decide what to create — kind, intent, suggested name/category/
  permissions, priority — separately from the binding row that stores
  the runtime value.
* `BindingSpec` (Phase 1a) owns the *binding* metadata — the
  capability required to mutate, whether the slot is required, and a
  human-readable hint.
* Cross-linking them at catalogue build time means future
  ``ResourceProvisioningPipeline`` (S4.5) and setup-pack UX (S10) can
  consume a single source: "for each provisionable resource, here's
  the suggested creation parameters AND the canonical binding to write
  through."

Cross-cutting findings:

* ``orphan_requirements`` — a :class:`ResourceRequirement` with no
  ``binding_name`` cross-link. Such requirements describe a resource
  but no slot exists for it. Flagged so subsystems can declare an
  explicit binding.
* ``binding_targets_unknown`` — the ``binding_name`` does not match
  any :class:`BindingSpec` declared in the same schema. Likely a typo
  or a removed binding.
* ``duplicate_options`` — the same ``(subsystem, binding_name)`` pair
  is declared more than once. Either two requirements point at the
  same binding (legal but worth surfacing) or a real duplicate.
* ``kind_mismatch`` — the :class:`ResourceKind` of the requirement
  doesn't equal the :class:`BindingKind` of the cross-linked binding.

Public surface:

* :class:`ProvisioningOption` — frozen dataclass per option.
* :class:`ProvisioningFindings` — frozen findings buckets.
* :class:`ProvisioningCatalogue` — frozen aggregate snapshot.
* :func:`build_provisioning_catalogue` — walks schemas, caches,
  returns snapshot.
* :func:`get_cached_provisioning_catalogue` — last-built snapshot or
  ``None``.

Diagnostics provider name: ``"resource_provisioning_catalogue"``.

Cycle discipline (mirrors :mod:`services.platform_consistency`): all
cross-package imports are function-local. Top-level imports are
stdlib only.
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("bot.services.resource_provisioning_catalogue")


_CATALOGUE_VERSION = 1


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProvisioningOption:
    """A single provisionable resource — the cross-link of a
    :class:`ResourceRequirement` with its :class:`BindingSpec`.

    ``binding_kind`` is ``None`` when no matching :class:`BindingSpec`
    was found in the schema (a ``binding_targets_unknown`` finding).
    The other ``binding_*`` fields are empty/default in that case.
    """

    subsystem: str
    binding_name: str
    kind: str  # ResourceKind value (channel/role/category/thread)
    binding_kind: str | None
    priority: str  # ProvisioningPriority value
    suggested_name: str
    suggested_category: str
    suggested_permissions: tuple[str, ...]
    intent: str
    description: str
    capability_required: str
    binding_required: bool
    binding_hint: str


@dataclass(frozen=True)
class ProvisioningFindings:
    """Cross-cutting checks computed at build time."""

    orphan_requirements: tuple[str, ...] = ()
    binding_targets_unknown: tuple[str, ...] = ()
    duplicate_options: tuple[str, ...] = ()
    kind_mismatch: tuple[str, ...] = ()

    @property
    def total(self) -> int:
        return (
            len(self.orphan_requirements)
            + len(self.binding_targets_unknown)
            + len(self.duplicate_options)
            + len(self.kind_mismatch)
        )


@dataclass(frozen=True)
class ProvisioningCatalogue:
    """An immutable snapshot of every cross-linked provisioning option."""

    version: int
    built_at: datetime.datetime
    options: tuple[ProvisioningOption, ...]
    findings: ProvisioningFindings

    def by_subsystem(self, subsystem: str) -> tuple[ProvisioningOption, ...]:
        return tuple(o for o in self.options if o.subsystem == subsystem)

    def find(
        self,
        subsystem: str,
        binding_name: str,
    ) -> ProvisioningOption | None:
        for option in self.options:
            if option.subsystem == subsystem and option.binding_name == binding_name:
                return option
        return None


# ---------------------------------------------------------------------------
# Module state — cached last-built catalogue
# ---------------------------------------------------------------------------


_CACHED: ProvisioningCatalogue | None = None


def _reset_for_tests() -> None:
    global _CACHED
    _CACHED = None


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def _build_option(
    subsystem: str,
    req: Any,  # core.runtime.resource_specs.ResourceRequirement
    binding: Any | None,  # core.runtime.subsystem_schema.BindingSpec | None
) -> ProvisioningOption:
    """Construct a :class:`ProvisioningOption` from a requirement and an
    optional cross-linked binding.
    """
    return ProvisioningOption(
        subsystem=subsystem,
        binding_name=req.binding_name,
        kind=req.kind.value,
        binding_kind=binding.kind.value if binding is not None else None,
        priority=req.provisioning.priority.value,
        suggested_name=req.provisioning.suggested_name,
        suggested_category=req.provisioning.suggested_category,
        suggested_permissions=tuple(req.provisioning.suggested_permissions),
        intent=req.intent,
        description=req.description,
        capability_required=(
            binding.capability_required if binding is not None else ""
        ),
        binding_required=binding.required if binding is not None else False,
        binding_hint=binding.hint if binding is not None else "",
    )


def build_provisioning_catalogue() -> ProvisioningCatalogue:
    """Walk every registered :class:`SubsystemSchema` and return a frozen
    snapshot of every ``ResourceRequirement`` × ``BindingSpec`` pair.

    Caches the result for diagnostics access; call again to refresh
    after a hot-reload. Sync — no I/O.
    """
    from core.runtime.subsystem_schema import all_schemas

    schemas = all_schemas()
    options: list[ProvisioningOption] = []
    orphan: list[str] = []
    unknown: list[str] = []
    duplicate: list[str] = []
    kind_mismatch: list[str] = []
    seen: set[tuple[str, str]] = set()

    for subsystem_name in sorted(schemas):
        schema = schemas[subsystem_name]
        bindings_by_name = {b.name: b for b in schema.bindings}

        for req in schema.resource_requirements:
            if not req.binding_name:
                orphan.append(f"{subsystem_name}/{req.intent}")
                continue

            binding = bindings_by_name.get(req.binding_name)
            key = (subsystem_name, req.binding_name)
            if key in seen:
                duplicate.append(f"{subsystem_name}.{req.binding_name}")
                continue
            seen.add(key)

            if binding is None:
                unknown.append(f"{subsystem_name}.{req.binding_name}")
                options.append(_build_option(subsystem_name, req, None))
                continue

            if binding.kind.value != req.kind.value:
                kind_mismatch.append(
                    f"{subsystem_name}.{req.binding_name} "
                    f"(req={req.kind.value} binding={binding.kind.value})",
                )

            options.append(_build_option(subsystem_name, req, binding))

    findings = ProvisioningFindings(
        orphan_requirements=tuple(sorted(orphan)),
        binding_targets_unknown=tuple(sorted(unknown)),
        duplicate_options=tuple(sorted(duplicate)),
        kind_mismatch=tuple(sorted(kind_mismatch)),
    )

    cat = ProvisioningCatalogue(
        version=_CATALOGUE_VERSION,
        built_at=datetime.datetime.now(tz=datetime.timezone.utc),
        options=tuple(options),
        findings=findings,
    )
    global _CACHED
    _CACHED = cat
    logger.info(
        "resource_provisioning_catalogue: built v%d — %d options across "
        "%d subsystem(s), %d findings",
        cat.version,
        len(cat.options),
        len({o.subsystem for o in cat.options}),
        findings.total,
    )
    return cat


def get_cached_provisioning_catalogue() -> ProvisioningCatalogue | None:
    """Return the last-built catalogue, or ``None`` if not yet built."""
    return _CACHED


# ---------------------------------------------------------------------------
# Diagnostics provider — registers at import time
# ---------------------------------------------------------------------------


def _snapshot() -> dict[str, Any]:
    """Stable diagnostics snapshot for ``!platform provisioning``.

    Returns counts + findings counts only. Operators wanting the full
    options list call :func:`get_cached_provisioning_catalogue` from a
    REPL or a future admin command.
    """
    cat = _CACHED
    if cat is None:
        return {
            "status": "not_built",
            "hint": (
                "call resource_provisioning_catalogue."
                "build_provisioning_catalogue() after schemas register."
            ),
        }
    by_priority: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    by_subsystem: dict[str, int] = {}
    for option in cat.options:
        by_priority[option.priority] = by_priority.get(option.priority, 0) + 1
        by_kind[option.kind] = by_kind.get(option.kind, 0) + 1
        by_subsystem[option.subsystem] = by_subsystem.get(option.subsystem, 0) + 1
    return {
        "status": "built",
        "version": cat.version,
        "built_at": cat.built_at.isoformat(),
        "option_count": len(cat.options),
        "subsystem_count": len(by_subsystem),
        "by_priority": by_priority,
        "by_kind": by_kind,
        "by_subsystem": by_subsystem,
        "findings_total": cat.findings.total,
        "findings": {
            "orphan_requirements": len(cat.findings.orphan_requirements),
            "binding_targets_unknown": len(cat.findings.binding_targets_unknown),
            "duplicate_options": len(cat.findings.duplicate_options),
            "kind_mismatch": len(cat.findings.kind_mismatch),
        },
    }


def _register_diagnostics() -> None:
    from services import diagnostics_service

    diagnostics_service.register("resource_provisioning_catalogue", _snapshot)


_register_diagnostics()


__all__ = [
    "ProvisioningCatalogue",
    "ProvisioningFindings",
    "ProvisioningOption",
    "build_provisioning_catalogue",
    "get_cached_provisioning_catalogue",
]
