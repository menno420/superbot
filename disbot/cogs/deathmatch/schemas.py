"""Deathmatch subsystem schemas — PR 8.

Declares the Settings the operator can configure for the Deathmatch
subsystem. PR 8 adds one setting per game per the plan §2.12 hard
rule — only settings the runtime actually reads land here:

* ``turn_timeout`` — read by ``_ChallengeView.btn_accept`` when
  spawning a ``_DuelView``. Controls how long each player has to
  respond before the duel times out and the opponent wins by default.

Future settings (base_hp / attack_damage / critical_chance /
defense_reduction / bot_enabled / bot_difficulty) land here as the
runtime grows read paths for them — most are still hardcoded in
``_Duel`` today and a per-setting read would mean threading the
value through ``_Duel.__init__``.
"""

from __future__ import annotations

from core.runtime.subsystem_schema import (
    SettingSpec,
    SubsystemSchema,
)
from utils.settings_keys import DEATHMATCH_TURN_TIMEOUT


def _validate_positive_int(value: object) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"expected positive int, got {value!r}")


DEATHMATCH_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="turn_timeout",
        value_type=int,
        default=60,
        settings_key=DEATHMATCH_TURN_TIMEOUT,
        capability_required="deathmatch.game.challenge",
        hint=(
            "Seconds each player has to respond on their turn before "
            "the duel times out and the opponent wins by default."
        ),
        validator=_validate_positive_int,
        input_hint="numeric_presets",
        presets=(30, 60, 120, 300),
    ),
)


DEATHMATCH_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="deathmatch",
    settings=DEATHMATCH_SETTINGS,
    version=1,
)


def register_schemas() -> None:
    """Register the Deathmatch schema — called from
    :meth:`Deathmatch.cog_load`. Idempotent.
    """
    from core.runtime import subsystem_schema

    subsystem_schema.register(DEATHMATCH_CONFIG_SCHEMA)


__all__ = [
    "DEATHMATCH_CONFIG_SCHEMA",
    "DEATHMATCH_SETTINGS",
    "register_schemas",
]
