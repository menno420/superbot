"""Role subsystem schemas — the two role-automation stacking toggles.

These booleans control whether each role-automation engine KEEPS or
REMOVES previously-earned tier roles. Both default to the historical
behaviour so existing guilds see no change until an operator flips them.

The per-role exemptions (``exempt_xp`` / ``exempt_time``) are NOT scalar
settings — they are structured, role-id-keyed rows in the
``role_automation_exemptions`` table (migration 052) and are edited
through the Roles settings UI (``views/roles/exemptions_panel.py``), not
through these specs.
"""

from __future__ import annotations

from core.runtime.subsystem_schema import (
    SettingSpec,
    SubsystemSchema,
)
from utils.settings_keys import TIME_ROLES_STACK, XP_ROLES_STACK

_CAPABILITY = "role.settings.configure"


def _validate_bool(value: object) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"expected bool, got {type(value).__name__}")


ROLE_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="time_roles_stack",
        value_type=bool,
        default=False,
        settings_key=TIME_ROLES_STACK,
        capability_required=_CAPABILITY,
        hint=(
            "When ON, members keep every tenure (time-based) role they have "
            "earned. When OFF (default), reaching a new tenure tier removes "
            "the previous one, so a member holds a single tenure role."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="xp_roles_stack",
        value_type=bool,
        default=True,
        settings_key=XP_ROLES_STACK,
        capability_required=_CAPABILITY,
        hint=(
            "When ON (default), members keep every XP/level role they earn — "
            "the roles stack. When OFF, reaching a higher level role removes "
            "the lower level roles, so a member holds a single level role."
        ),
        validator=_validate_bool,
    ),
)


ROLE_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="role",
    settings=ROLE_SETTINGS,
    version=1,
)


def register_schemas() -> None:
    """Register the Role subsystem schema. Called from ``RoleCog.cog_load``.

    Re-registration-safe (the underlying registry logs and replaces).
    """
    from core.runtime import subsystem_schema

    subsystem_schema.register(ROLE_CONFIG_SCHEMA)


__all__ = [
    "ROLE_CONFIG_SCHEMA",
    "ROLE_SETTINGS",
    "register_schemas",
]
