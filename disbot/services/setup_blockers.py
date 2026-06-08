"""Dynamic setup-readiness blocker registry — PR-03.

Replaces the static ``SETUP_READINESS_BLOCKERS`` tuple of bare strings
in ``services.platform_consistency`` with a typed registry whose
status is computed from cached foundation state.  ``platform_consistency``
re-exports the constant as a derived tuple of IDs for backward compat
so existing callers still work.

Design rules (matching the source plan and PR-03's stop conditions):

* Every ``status_provider`` is **sync** and **never performs I/O**.
  It reads cached in-process state (cached ledger, cached registry,
  module existence) and returns one of ``"resolved" | "in_progress" |
  "pending" | "blocked" | "unknown"``.
* A provider that raises is caught and rendered as ``"unknown"`` —
  the registry is fail-safe so one bad provider does not blank the
  whole report.
* All imports are function-local inside each provider so this module
  itself does not trigger a cycle with ``core.runtime`` at import
  time (the consistency report's collectors enforce the same
  discipline).

Public surface::

    BlockerStatus       — Literal type
    BlockerSpec         — frozen dataclass per blocker
    BLOCKERS            — canonical tuple of every blocker spec
    blocker_ids()       — derived tuple of IDs (re-exported by
                          platform_consistency.SETUP_READINESS_BLOCKERS)
    status_for(spec)    — invoke the provider with the unknown fallback
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger("bot.setup_blockers")

BlockerStatus = Literal[
    "resolved",
    "in_progress",
    "pending",
    "blocked",
    "unknown",
]


@dataclass(frozen=True)
class BlockerSpec:
    """A single setup-readiness blocker with metadata + status provider.

    The ``status_provider`` is a zero-arg sync callable that consults
    cached in-process state.  ``status_for`` wraps it with a
    fail-safe so a raising provider becomes ``"unknown"`` rather than
    crashing the consistency report.

    Fields mirror the plan's BlockerSpec shape:

    * ``id`` — stable snake_case ID (matches the original
      ``SETUP_READINESS_BLOCKERS`` strings for backward compat).
    * ``owner_project`` — the project area responsible.
      ``"UNCONFIRMED"`` is allowed for blockers whose owner the
      reviewer must assign.
    * ``refactor_layer`` — short tag like ``"registries"``,
      ``"runtime"``, ``"ui"`` to help readers group them.
    * ``severity`` — ``"blocks_release"`` | ``"blocks_phase"`` |
      ``"informational"``.  Today every blocker is
      ``"informational"`` to preserve the section's
      ``informational=True`` semantics.
    * ``unlocks`` / ``blocked_by`` — other blocker IDs by name.
    * ``doc_anchor`` — anchor in
      ``docs/archive/phase-2-completion-readiness.md`` (without the leading
      ``#``) for "where do I read more?"
    """

    id: str
    owner_project: str
    refactor_layer: str
    status_provider: Callable[[], BlockerStatus]
    severity: Literal["blocks_release", "blocks_phase", "informational"]
    unlocks: tuple[str, ...] = ()
    blocked_by: tuple[str, ...] = ()
    doc_anchor: str = ""


# ---------------------------------------------------------------------------
# Status providers (all sync; all imports function-local)
# ---------------------------------------------------------------------------


def _command_surface_ledger_status() -> BlockerStatus:
    from core.runtime import command_surface_ledger

    return "resolved" if command_surface_ledger.get_cached_ledger() else "pending"


def _settings_registry_status() -> BlockerStatus:
    from core.runtime import settings_registry

    return "resolved" if settings_registry.get_cached_registry() else "pending"


def _settings_mutation_pipeline_status() -> BlockerStatus:
    """Resolved if ``services.settings_mutation`` exposes the pipeline.

    The module exists today and exports ``SettingsMutationPipeline``;
    that is the contract setup_operations depends on.
    """
    import importlib
    import importlib.util

    spec = importlib.util.find_spec("services.settings_mutation")
    if spec is None:
        return "pending"
    module = importlib.import_module("services.settings_mutation")
    return "resolved" if hasattr(module, "SettingsMutationPipeline") else "in_progress"


def _setup_wizard_status() -> BlockerStatus:
    """Resolved if the setup cog module is importable.

    The cog is loaded at runtime; "importable" is the safest sync
    signal that the wizard surface exists.  A fully end-user-facing
    wizard is still in iteration, hence ``in_progress`` if the
    customization catalogue has not been built yet.
    """
    import importlib
    import importlib.util

    spec = importlib.util.find_spec("cogs.setup_cog")
    if spec is None:
        return "pending"
    # If the customization catalogue is built, the wizard surface has
    # all of its inputs available.
    try:
        from services import customization_catalogue

        if customization_catalogue.get_cached_catalogue() is not None:
            return "resolved"
    except Exception:  # noqa: BLE001 — best-effort sync check
        pass
    return "in_progress"


def _governance_trusted_role_schema_status() -> BlockerStatus:
    """Resolved if the governance subsystem declares ``trusted_role``.

    Checks the in-process subsystem_schema registry for the binding
    spec; if the schema module is not built or the binding is
    missing, marked ``pending``.
    """
    try:
        from core.runtime import subsystem_schema

        schemas = subsystem_schema.all_schemas()
    except Exception:  # noqa: BLE001 — best-effort sync check
        return "unknown"
    gov = schemas.get("governance") if isinstance(schemas, dict) else None
    if gov is None:
        return "pending"
    bindings = getattr(gov, "bindings", ()) or ()
    for b in bindings:
        if getattr(b, "name", None) == "trusted_role":
            return "resolved"
    return "pending"


def _panel_registry_status() -> BlockerStatus:
    """Panel registry — module exists today as ``panel_manager``.

    ``panel_manager`` provides the version-stamped persistent-view
    registration.  Treat the module's importability as the resolution
    signal; absence is ``pending``.
    """
    import importlib
    import importlib.util

    spec = importlib.util.find_spec("core.runtime.panel_manager")
    if spec is None:
        return "pending"
    return "resolved"


def _pending_doc_anchor() -> BlockerStatus:
    """Default provider for blockers with no cached resolution signal.

    Always returns ``pending``; consult the doc anchor for rationale.
    """
    return "pending"


# ---------------------------------------------------------------------------
# Canonical registry
# ---------------------------------------------------------------------------


BLOCKERS: tuple[BlockerSpec, ...] = (
    BlockerSpec(
        id="command_surface_ledger",
        owner_project="Core Platform",
        refactor_layer="registries",
        status_provider=_command_surface_ledger_status,
        severity="informational",
        unlocks=("slash_panel_entrypoints", "setup_wizard"),
        doc_anchor="command-surface-ledger",
    ),
    BlockerSpec(
        id="panel_registry",
        owner_project="Core Platform",
        refactor_layer="registries",
        status_provider=_panel_registry_status,
        severity="informational",
        unlocks=("slash_panel_entrypoints", "setup_wizard"),
        doc_anchor="panel-registry",
    ),
    BlockerSpec(
        id="settings_registry",
        owner_project="Core Platform",
        refactor_layer="registries",
        status_provider=_settings_registry_status,
        severity="informational",
        unlocks=("settings_mutation_pipeline", "setup_wizard"),
        doc_anchor="settings-registry",
    ),
    BlockerSpec(
        id="settings_mutation_pipeline",
        owner_project="Core Platform",
        refactor_layer="services",
        status_provider=_settings_mutation_pipeline_status,
        severity="informational",
        blocked_by=("settings_registry",),
        unlocks=("setup_wizard",),
        doc_anchor="settings-mutation-pipeline",
    ),
    BlockerSpec(
        id="governance_trusted_role_schema",
        owner_project="Core Platform",
        refactor_layer="config",
        status_provider=_governance_trusted_role_schema_status,
        severity="informational",
        doc_anchor="governance-trusted-role-schema",
    ),
    BlockerSpec(
        id="role_service_extraction",
        owner_project="Core Platform",
        refactor_layer="services",
        status_provider=_pending_doc_anchor,
        severity="informational",
        doc_anchor="role-service-extraction",
    ),
    BlockerSpec(
        id="cleanup_policy_extraction",
        owner_project="Core Platform",
        refactor_layer="services",
        status_provider=_pending_doc_anchor,
        severity="informational",
        doc_anchor="cleanup-policy-extraction",
    ),
    BlockerSpec(
        id="logging_settings_integration",
        owner_project="Core Platform",
        refactor_layer="services",
        status_provider=_pending_doc_anchor,
        severity="informational",
        blocked_by=("settings_registry",),
        doc_anchor="logging-settings-integration",
    ),
    BlockerSpec(
        id="slash_panel_entrypoints",
        owner_project="Help & Navigation",
        refactor_layer="ui",
        status_provider=_pending_doc_anchor,
        severity="informational",
        blocked_by=("panel_registry", "command_surface_ledger"),
        doc_anchor="slash-panel-entrypoints",
    ),
    BlockerSpec(
        # NOTE: owner UNCONFIRMED per the PR-03 revision plan — reviewer
        # to assign during PR review.
        id="setup_wizard_readiness_bridge",
        owner_project="UNCONFIRMED",
        refactor_layer="services",
        status_provider=_pending_doc_anchor,
        severity="informational",
        doc_anchor="setup-wizard-readiness-bridge",
    ),
    BlockerSpec(
        id="setup_wizard",
        owner_project="Setup Wizard",
        refactor_layer="ui",
        status_provider=_setup_wizard_status,
        severity="informational",
        blocked_by=(
            "settings_registry",
            "settings_mutation_pipeline",
            "panel_registry",
        ),
        doc_anchor="setup-wizard",
    ),
)


def blocker_ids() -> tuple[str, ...]:
    """Derived tuple of every blocker's ID.

    ``services.platform_consistency.SETUP_READINESS_BLOCKERS`` is
    re-exported from this view so the bare-string contract is
    preserved for backwards-compatible callers.
    """
    return tuple(b.id for b in BLOCKERS)


def status_for(spec: BlockerSpec) -> BlockerStatus:
    """Invoke ``spec.status_provider`` with a fail-safe wrapper.

    A raising provider becomes ``"unknown"`` so a broken cached-state
    accessor cannot blank the readiness section.
    """
    try:
        return spec.status_provider()
    except Exception as exc:  # noqa: BLE001 — registry is fail-safe
        logger.warning(
            "setup_blockers: status_provider for %r raised %s",
            spec.id,
            exc,
        )
        return "unknown"


__all__ = [
    "BLOCKERS",
    "BlockerSpec",
    "BlockerStatus",
    "blocker_ids",
    "status_for",
]
