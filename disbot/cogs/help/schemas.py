"""Help SubsystemSchema — the "Help appearance" domain panel (audit Phase 5).

Help's guild configuration is the HLP-3 overlay (hide / rename /
re-describe, stored in ``help_overlay`` behind the audited
``services/help_overlay_mutation`` seam) — a dedicated-panel domain, not
scalar settings. Declaring a :class:`DomainPanelSpec` makes the Settings
hub discover **Help appearance** as a domain-config group (the #654
declaration model), routing operators to the same editor the staff hub's
``✏️ Help editor`` button opens.
"""

from __future__ import annotations

from core.runtime.subsystem_schema import DomainPanelSpec, SubsystemSchema

HELP_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="help",
    domain_panels=(
        DomainPanelSpec(
            name="Help appearance",
            description=(
                "Hide, rename, or re-describe Help entries for this server "
                "(display-only — never affects permissions or execution). "
                "Edited in the Help editor panel; every write is audited."
            ),
            capability_required="help.settings.configure",
        ),
    ),
    version=1,
)


def register_schemas() -> None:
    """Register the Help subsystem schema. Idempotent."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(HELP_CONFIG_SCHEMA)


__all__ = ["HELP_CONFIG_SCHEMA", "register_schemas"]
