"""Blackjack subsystem schemas — PR 8.

Declares the Settings the operator can configure for the Blackjack
subsystem. PR 8 adds one setting per game per the plan §2.12 hard
rule — only settings the runtime actually reads land here:

* ``default_entry_fee`` — read by :meth:`BlackjackCog.bjtournament`
  when the operator does not pass an explicit ``entry_fee`` argument.

Future settings (default rounds / duration / category name / announce
channel) land here as the runtime grows read paths for them.
"""

from __future__ import annotations

from core.runtime.subsystem_schema import (
    SettingSpec,
    SubsystemSchema,
)
from utils.settings_keys import BLACKJACK_DEFAULT_ENTRY_FEE


def _validate_non_negative_int(value: object) -> None:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"expected non-negative int, got {value!r}")


BLACKJACK_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="default_entry_fee",
        value_type=int,
        default=0,
        settings_key=BLACKJACK_DEFAULT_ENTRY_FEE,
        capability_required="blackjack.tournament.manage",
        hint=(
            "Default entry fee (🪙 coins) applied when an admin runs "
            "`!bjtournament` without an explicit entry_fee argument."
        ),
        validator=_validate_non_negative_int,
        input_hint="numeric_presets",
        presets=(0, 10, 25, 50, 100),
    ),
)


BLACKJACK_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="blackjack",
    settings=BLACKJACK_SETTINGS,
    version=1,
)


def register_schemas() -> None:
    """Register the Blackjack schema — called from
    :meth:`BlackjackCog.cog_load`. Idempotent.
    """
    from core.runtime import subsystem_schema

    subsystem_schema.register(BLACKJACK_CONFIG_SCHEMA)


__all__ = [
    "BLACKJACK_CONFIG_SCHEMA",
    "BLACKJACK_SETTINGS",
    "register_schemas",
]
