"""Karma subsystem schema — operator config for peer reputation.

Declares the typed guild-config schema for karma: a master switch, the
per-(giver -> receiver) cooldown, and the per-giver daily cap.  All three
are scalar guild settings (the legacy KV table) — the keys live in
:mod:`utils.settings_keys.karma` and are operator-editable through the
existing ``!settings`` widget.

The ``default=`` values and validator bounds come from
:mod:`services.karma_config` (the single source of truth shared with
:func:`services.karma_config.load_policy`), so a spec default and a policy
default can never silently drift — pinned by ``test_karma_schemas``.
"""

from __future__ import annotations

from core.runtime.subsystem_schema import (
    SettingSpec,
    SubsystemSchema,
)
from services.karma_config import (
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_DAILY_CAP,
    DEFAULT_ENABLED,
    DEFAULT_REACTION_EMOJI,
    MAX_COOLDOWN_SECONDS,
    MAX_DAILY_CAP,
    MAX_REACTION_EMOJI_LEN,
    MIN_COOLDOWN_SECONDS,
    MIN_DAILY_CAP,
)
from utils.settings_keys import (
    KARMA_COOLDOWN,
    KARMA_DAILY_CAP,
    KARMA_ENABLED,
    KARMA_REACTION_EMOJI,
)

_KARMA_CAPABILITY = "karma.settings.configure"


def _validate_bool(value: object) -> None:
    # ``isinstance(True, int)`` is True, so guard the bool type explicitly.
    if not isinstance(value, bool):
        raise ValueError(f"expected bool, got {value!r}")


def _bounded_int(value: object, lo: int, hi: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"expected int, got {value!r}")
    if not (lo <= value <= hi):
        raise ValueError(f"must be between {lo} and {hi}")


def _validate_cooldown(value: object) -> None:
    _bounded_int(value, MIN_COOLDOWN_SECONDS, MAX_COOLDOWN_SECONDS)


def _validate_daily_cap(value: object) -> None:
    _bounded_int(value, MIN_DAILY_CAP, MAX_DAILY_CAP)


def _validate_reaction_emoji(value: object) -> None:
    # A free-text emoji trigger: a single unicode emoji or a custom
    # ``<:name:id>`` form.  Empty string = OFF (the default).  We keep the
    # check permissive (Discord validates the actual reaction at add-time);
    # the guard is only against absurd lengths / wrong type.
    if not isinstance(value, str):
        raise ValueError(f"expected str, got {value!r}")
    if len(value) > MAX_REACTION_EMOJI_LEN:
        raise ValueError(f"emoji must be at most {MAX_REACTION_EMOJI_LEN} characters")


KARMA_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="enabled",
        value_type=bool,
        default=DEFAULT_ENABLED,
        settings_key=KARMA_ENABLED,
        capability_required=_KARMA_CAPABILITY,
        hint=(
            "Master switch for karma. When off, the !thanks / !karma give "
            "commands politely decline. On by default."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="cooldown_seconds",
        value_type=int,
        default=DEFAULT_COOLDOWN_SECONDS,
        settings_key=KARMA_COOLDOWN,
        capability_required=_KARMA_CAPABILITY,
        hint=(
            "How long a member must wait before thanking the same recipient "
            "again (seconds). The main anti-farm guard. 0 disables the cooldown."
        ),
        validator=_validate_cooldown,
        input_hint="numeric_presets",
        presets=(1800, 3600, 86400),
    ),
    SettingSpec(
        name="daily_cap",
        value_type=int,
        default=DEFAULT_DAILY_CAP,
        settings_key=KARMA_DAILY_CAP,
        capability_required=_KARMA_CAPABILITY,
        hint="Maximum karma grants one member can give per rolling 24 hours.",
        validator=_validate_daily_cap,
        input_hint="numeric_presets",
        presets=(5, 10, 25),
    ),
    SettingSpec(
        name="reaction_emoji",
        value_type=str,
        default=DEFAULT_REACTION_EMOJI,
        settings_key=KARMA_REACTION_EMOJI,
        capability_required=_KARMA_CAPABILITY,
        hint=(
            "React-to-thank: set an emoji (e.g. ✨) and reacting with it on a "
            "message grants karma to that message's author — same cooldown and "
            "daily cap as !thanks. Leave empty to disable (the default)."
        ),
        validator=_validate_reaction_emoji,
    ),
)

KARMA_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="karma",
    bindings=(),
    settings=KARMA_SETTINGS,
    resource_requirements=(),
    version=1,
)


def register_schemas() -> None:
    """Register the karma subsystem schema. Idempotent."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(KARMA_CONFIG_SCHEMA)


__all__ = [
    "KARMA_CONFIG_SCHEMA",
    "KARMA_SETTINGS",
    "register_schemas",
]
