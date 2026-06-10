"""Help subsystem configuration declaration (Settings Phase 2 pattern).

The Help *overlay* (display-hide / rename / re-describe; the Q-0059 Home
message follows in PR B) is configured in the dedicated Help editor — a
domain panel, not scalar settings. Declaring it here makes "Help appearance"
an actionable Settings-hub group (editor plan §4.1) while the audited seam
(``services/help_overlay_mutation``) stays the only writer. Discovery-only
by the ``DomainPanelSpec`` contract: the editor re-checks authority at every
interaction regardless of this declaration.
"""

from __future__ import annotations

from core.runtime.subsystem_schema import DomainPanelSpec, SubsystemSchema

HELP_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="help",
    domain_panels=(
        DomainPanelSpec(
            name="Help appearance",
            description=(
                "Per-guild Help presentation — hide, rename, or re-describe "
                "hubs and subsystems (display-only; execution is never "
                "affected). Edit via `!servermanagement` → ✏️ Help editor; "
                "verify with 👁 Help Preview."
            ),
            capability_required="help.settings.configure",
        ),
    ),
    version=1,
)


def register_schemas() -> None:
    """Register the help subsystem schema. Idempotent."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(HELP_CONFIG_SCHEMA)


__all__ = ["HELP_CONFIG_SCHEMA", "register_schemas"]
