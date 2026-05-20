"""RPS subsystem schemas — PR 8.

Declares the Settings the operator can configure for the Rock Paper
Scissors subsystem. PR 8 adds one setting per game per the plan §2.12
hard rule — only settings the runtime actually reads land here:

* ``default_entry_fee`` — read by :meth:`RPSTournamentCog.rps_register`
  when the operator does not pass an explicit ``entry_fee`` argument.

Future settings (default mode / best-of / registration duration /
bot match enabled / tournament channel) land here as the runtime
grows read paths for them.

The canonical SUBSYSTEMS key remains ``rps_tournament`` per PR 3's
display-rename strategy (plan §13 acceptance checklist); the user-
facing display is "Rock Paper Scissors".
"""

from __future__ import annotations

from core.runtime.subsystem_schema import (
    SettingSpec,
    SubsystemSchema,
)
from utils.settings_keys import RPS_DEFAULT_ENTRY_FEE


def _validate_non_negative_int(value: object) -> None:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"expected non-negative int, got {value!r}")


RPS_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="default_entry_fee",
        value_type=int,
        default=0,
        settings_key=RPS_DEFAULT_ENTRY_FEE,
        capability_required="rps_tournament.tournament.manage",
        hint=(
            "Default entry fee (🪙 coins) applied when an admin runs "
            "`!rpsregister` without an explicit entry_fee argument."
        ),
        validator=_validate_non_negative_int,
        input_hint="numeric_presets",
        presets=(0, 10, 25, 50, 100),
    ),
)


RPS_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="rps_tournament",
    settings=RPS_SETTINGS,
    version=1,
)


def register_schemas() -> None:
    """Register the RPS schema — called from the cog's ``cog_load``.
    Idempotent.
    """
    from core.runtime import subsystem_schema

    subsystem_schema.register(RPS_CONFIG_SCHEMA)


async def resolve_default_entry_fee(guild_id: int) -> int:
    """Read ``RPS_DEFAULT_ENTRY_FEE`` for ``guild_id``; fall back to
    0 on missing/unparseable values. Used by the ``!rpsregister``
    body when the operator omits the explicit fee argument.
    """
    from utils import db

    raw = await db.get_setting(guild_id, RPS_DEFAULT_ENTRY_FEE, "0")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "RPS_CONFIG_SCHEMA",
    "RPS_SETTINGS",
    "register_schemas",
    "resolve_default_entry_fee",
]
