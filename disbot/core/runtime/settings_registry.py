"""Read-only Settings registry — S1 of the Global Settings & Customization Manager.

A frozen, in-memory catalogue of every :class:`SettingSpec` declared across
all registered subsystems. Mirrors the
:mod:`core.runtime.command_surface_ledger` pattern: ``build_registry()``
walks ``subsystem_schema.all_schemas()`` once, returns a frozen
:class:`SettingsRegistry`, and caches it for later diagnostics access.
Read-only — there is no mutation surface in this module.

Why this lives in ``core/runtime/`` rather than ``services/``:

* The registry is a runtime primitive consumed by future read/write services
  (``SettingsResolution`` in S3, ``SettingsMutationPipeline`` in S4) and by
  the ``CustomizationCatalogue`` (S2) which composes it with the command
  surface ledger.
* Mirroring the ``command_surface_ledger`` placement keeps cycle-discipline
  consistent: this module imports from ``core.runtime.subsystem_schema``
  (sibling) and from ``utils.subsystem_registry`` only via deferred function-
  local imports — never at module scope.

Public surface:

    SettingEntry         — frozen dataclass per declared SettingSpec
    RegistryFindings     — frozen dataclass with cross-cutting findings
    SettingsRegistry     — frozen aggregate snapshot
    build_registry()     — walks subsystem_schema, caches, returns snapshot
    get_cached_registry() — last-built registry, or None

Diagnostics provider name: ``"settings_registry"``.
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from typing import Any

from core.runtime.subsystem_schema import SettingSpec, all_schemas

logger = logging.getLogger("bot.runtime.settings_registry")


_REGISTRY_VERSION = 1


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SettingEntry:
    """A single declared :class:`SettingSpec`, snapshotted at build time."""

    subsystem: str
    name: str
    value_type_name: str
    default_repr: str
    settings_key: str
    capability_required: str
    hint: str
    has_validator: bool


@dataclass(frozen=True)
class RegistryFindings:
    """Cross-cutting checks computed at build time."""

    settings_without_settings_key: tuple[str, ...] = ()
    settings_without_capability: tuple[str, ...] = ()
    duplicate_qualified_names: tuple[str, ...] = ()
    duplicate_settings_keys: tuple[str, ...] = ()

    @property
    def total(self) -> int:
        return (
            len(self.settings_without_settings_key)
            + len(self.settings_without_capability)
            + len(self.duplicate_qualified_names)
            + len(self.duplicate_settings_keys)
        )


@dataclass(frozen=True)
class SettingsRegistry:
    """An immutable snapshot of every declared SettingSpec."""

    version: int
    built_at: datetime.datetime
    entries: tuple[SettingEntry, ...]
    findings: RegistryFindings

    def by_subsystem(self, subsystem: str) -> tuple[SettingEntry, ...]:
        return tuple(e for e in self.entries if e.subsystem == subsystem)

    def find(self, subsystem: str, name: str) -> SettingEntry | None:
        for entry in self.entries:
            if entry.subsystem == subsystem and entry.name == name:
                return entry
        return None

    def find_by_settings_key(self, settings_key: str) -> SettingEntry | None:
        if not settings_key:
            return None
        for entry in self.entries:
            if entry.settings_key == settings_key:
                return entry
        return None


# ---------------------------------------------------------------------------
# Module state — cached last-built registry
# ---------------------------------------------------------------------------

_CACHED: SettingsRegistry | None = None


def _reset_for_tests() -> None:
    global _CACHED
    _CACHED = None


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def _entry_from(subsystem: str, spec: SettingSpec) -> SettingEntry:
    value_type_name = getattr(spec.value_type, "__name__", repr(spec.value_type))
    return SettingEntry(
        subsystem=subsystem,
        name=spec.name,
        value_type_name=value_type_name,
        default_repr=repr(spec.default),
        settings_key=spec.settings_key,
        capability_required=spec.capability_required,
        hint=spec.hint,
        has_validator=spec.validator is not None,
    )


def _compute_findings(entries: tuple[SettingEntry, ...]) -> RegistryFindings:
    """Cross-cutting checks once the entry list is in hand."""
    missing_key: list[str] = []
    missing_cap: list[str] = []
    for entry in entries:
        qualified = f"{entry.subsystem}.{entry.name}"
        if not entry.settings_key:
            missing_key.append(qualified)
        if not entry.capability_required:
            missing_cap.append(qualified)

    qualified_counts: dict[str, int] = {}
    for entry in entries:
        qualified = f"{entry.subsystem}.{entry.name}"
        qualified_counts[qualified] = qualified_counts.get(qualified, 0) + 1
    duplicate_qualified = tuple(
        sorted(q for q, count in qualified_counts.items() if count > 1),
    )

    key_owners: dict[str, list[str]] = {}
    for entry in entries:
        if not entry.settings_key:
            continue
        key_owners.setdefault(entry.settings_key, []).append(
            f"{entry.subsystem}.{entry.name}",
        )
    duplicate_keys = tuple(
        sorted(k for k, owners in key_owners.items() if len(owners) > 1),
    )

    return RegistryFindings(
        settings_without_settings_key=tuple(sorted(missing_key)),
        settings_without_capability=tuple(sorted(missing_cap)),
        duplicate_qualified_names=duplicate_qualified,
        duplicate_settings_keys=duplicate_keys,
    )


def build_registry() -> SettingsRegistry:
    """Walk every registered subsystem schema and return a frozen snapshot.

    Caches the result for later diagnostics access; call again to refresh
    after a hot-reload. The function is sync-safe: it does not perform I/O.
    """
    schemas = all_schemas()
    entries: list[SettingEntry] = []
    for subsystem in sorted(schemas):
        schema = schemas[subsystem]
        for spec in schema.settings:
            entries.append(_entry_from(subsystem, spec))
    entries_tuple = tuple(entries)
    findings = _compute_findings(entries_tuple)
    registry = SettingsRegistry(
        version=_REGISTRY_VERSION,
        built_at=datetime.datetime.now(tz=datetime.timezone.utc),
        entries=entries_tuple,
        findings=findings,
    )
    global _CACHED
    _CACHED = registry
    logger.info(
        "settings_registry: built v%d — %d entries across %d subsystems, %d findings",
        registry.version,
        len(entries_tuple),
        len({e.subsystem for e in entries_tuple}),
        findings.total,
    )
    return registry


def get_cached_registry() -> SettingsRegistry | None:
    """Return the last-built registry, or ``None`` if not yet built."""
    return _CACHED


# ---------------------------------------------------------------------------
# Diagnostics provider — registers at import time
# ---------------------------------------------------------------------------


def _snapshot() -> dict[str, Any]:
    """Stable diagnostics snapshot for ``!platform settings-registry``.

    Returns counts + findings counts only. Operators wanting the full
    entries list call :func:`get_cached_registry` from a REPL or a future
    admin command.
    """
    registry = _CACHED
    if registry is None:
        return {
            "status": "not_built",
            "hint": "call settings_registry.build_registry() after cogs load.",
        }
    by_subsystem: dict[str, int] = {}
    for entry in registry.entries:
        by_subsystem[entry.subsystem] = by_subsystem.get(entry.subsystem, 0) + 1
    return {
        "status": "built",
        "version": registry.version,
        "built_at": registry.built_at.isoformat(),
        "entry_count": len(registry.entries),
        "subsystems": len(by_subsystem),
        "by_subsystem": by_subsystem,
        "findings_total": registry.findings.total,
        "findings": {
            "settings_without_settings_key": len(
                registry.findings.settings_without_settings_key,
            ),
            "settings_without_capability": len(
                registry.findings.settings_without_capability,
            ),
            "duplicate_qualified_names": len(
                registry.findings.duplicate_qualified_names,
            ),
            "duplicate_settings_keys": len(registry.findings.duplicate_settings_keys),
        },
    }


def _register_diagnostics() -> None:
    from services import diagnostics_service

    diagnostics_service.register("settings_registry", _snapshot)


_register_diagnostics()


__all__ = [
    "RegistryFindings",
    "SettingEntry",
    "SettingsRegistry",
    "build_registry",
    "get_cached_registry",
]
