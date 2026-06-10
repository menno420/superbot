"""Cleanup SubsystemSchema (Settings Phase 2).

Cleanup's real configuration is **domain config**, not scalar settings:
prohibited-word policy + cleanup behavior live in the governance
``cleanup_policies`` tables (written only by
:class:`~governance.writes.GovernanceMutationPipeline`) and are operated
through the dedicated cleanup panel.  This schema declares exactly that —
a :class:`~core.runtime.subsystem_schema.DomainPanelSpec` and no scalar
settings — so the Settings hub discovers cleanup as a *domain
configuration group* through the real declaration mechanism instead of
the retired Phase 1 ``DOMAIN_CONFIG_SUBSYSTEMS`` curated table
(settings audit §10.2 step 4; consolidated plan Batch 4).
"""

from __future__ import annotations

from core.runtime.subsystem_schema import DomainPanelSpec, SubsystemSchema

CLEANUP_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="cleanup",
    domain_panels=(
        DomainPanelSpec(
            name="Cleanup policies",
            description=(
                "Prohibited words and message-cleanup behavior — configured "
                "in the dedicated cleanup panel (governance-audited); the "
                "Settings group routes there."
            ),
            capability_required="cleanup.settings.configure",
        ),
    ),
    version=1,
)


def register_schemas() -> None:
    """Register the cleanup subsystem schema. Idempotent."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(CLEANUP_CONFIG_SCHEMA)


__all__ = ["CLEANUP_CONFIG_SCHEMA", "register_schemas"]
