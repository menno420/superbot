"""Automod subsystem schema — operator config for the automod message stage.

Declares the typed guild-config schema for automod v1 (Q-0108): a master switch,
four per-rule enable flags, the rule thresholds, and the exempt role/channel
safety valve.  All settings are scalar guild settings (the legacy KV table) —
**no migration**.  Declaring the :class:`SubsystemSchema` makes automod an
actionable Settings group surfaced through the existing ``!settings`` widget.

The ``default=`` values and validator bounds come from
:mod:`services.automod_config` (the single source of truth shared with
:func:`services.automod_config.load_policy`), so a spec default and a policy
default can never silently drift — pinned by ``test_automod_schemas``.

Edit authority borrows the moderation configure capability
(``moderation.settings.configure``): automod *is* moderation's automated layer,
so the same staff who configure moderation configure automod.
"""

from __future__ import annotations

from core.runtime.subsystem_schema import (
    SettingSpec,
    SubsystemSchema,
)
from services.automod_config import (
    DEFAULT_CAPS_ENABLED,
    DEFAULT_CAPS_PERCENT,
    DEFAULT_CROSS_CHANNEL_SPAM_COUNT,
    DEFAULT_CROSS_CHANNEL_SPAM_ENABLED,
    DEFAULT_DUPLICATE_COUNT,
    DEFAULT_DUPLICATE_ENABLED,
    DEFAULT_ENABLED,
    DEFAULT_EXEMPT_CHANNELS,
    DEFAULT_EXEMPT_ROLES,
    DEFAULT_INVITES_ENABLED,
    DEFAULT_MENTIONS_COUNT,
    DEFAULT_MENTIONS_ENABLED,
    DEFAULT_SPAM_COUNT,
    DEFAULT_SPAM_ENABLED,
    DEFAULT_SPAM_WINDOW_SECONDS,
    MAX_CAPS_PERCENT,
    MAX_CROSS_CHANNEL_SPAM_COUNT,
    MAX_DUPLICATE_COUNT,
    MAX_MENTIONS_COUNT,
    MAX_SPAM_COUNT,
    MAX_SPAM_WINDOW_SECONDS,
    MIN_CAPS_PERCENT,
    MIN_CROSS_CHANNEL_SPAM_COUNT,
    MIN_DUPLICATE_COUNT,
    MIN_MENTIONS_COUNT,
    MIN_SPAM_COUNT,
    MIN_SPAM_WINDOW_SECONDS,
    parse_id_csv,
)
from utils.settings_keys import (
    AUTOMOD_CAPS_ENABLED,
    AUTOMOD_CAPS_PERCENT,
    AUTOMOD_CROSS_CHANNEL_SPAM_COUNT,
    AUTOMOD_CROSS_CHANNEL_SPAM_ENABLED,
    AUTOMOD_DUPLICATE_COUNT,
    AUTOMOD_DUPLICATE_ENABLED,
    AUTOMOD_ENABLED,
    AUTOMOD_EXEMPT_CHANNELS,
    AUTOMOD_EXEMPT_ROLES,
    AUTOMOD_INVITES_ENABLED,
    AUTOMOD_MENTIONS_COUNT,
    AUTOMOD_MENTIONS_ENABLED,
    AUTOMOD_SPAM_COUNT,
    AUTOMOD_SPAM_ENABLED,
    AUTOMOD_SPAM_WINDOW_SECONDS,
)

_AUTOMOD_CAPABILITY = "moderation.settings.configure"


def _validate_bool(value: object) -> None:
    # ``isinstance(True, int)`` is True, so guard the bool type explicitly.
    if not isinstance(value, bool):
        raise ValueError(f"expected bool, got {value!r}")


def _bounded_int(value: object, lo: int, hi: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"expected int, got {value!r}")
    if not (lo <= value <= hi):
        raise ValueError(f"must be between {lo} and {hi}")


def _validate_spam_count(value: object) -> None:
    _bounded_int(value, MIN_SPAM_COUNT, MAX_SPAM_COUNT)


def _validate_spam_window(value: object) -> None:
    _bounded_int(value, MIN_SPAM_WINDOW_SECONDS, MAX_SPAM_WINDOW_SECONDS)


def _validate_caps_percent(value: object) -> None:
    _bounded_int(value, MIN_CAPS_PERCENT, MAX_CAPS_PERCENT)


def _validate_mentions_count(value: object) -> None:
    _bounded_int(value, MIN_MENTIONS_COUNT, MAX_MENTIONS_COUNT)


def _validate_cross_channel_spam_count(value: object) -> None:
    _bounded_int(value, MIN_CROSS_CHANNEL_SPAM_COUNT, MAX_CROSS_CHANNEL_SPAM_COUNT)


def _validate_duplicate_count(value: object) -> None:
    _bounded_int(value, MIN_DUPLICATE_COUNT, MAX_DUPLICATE_COUNT)


def _validate_id_csv(value: object) -> None:
    """Reject non-numeric tokens so a typo'd exempt list fails loudly.

    ``parse_id_csv`` itself is tolerant (it powers the read model and must
    never raise); this validator is the *write*-time gate that gives the
    operator feedback instead of silently dropping a bad id.
    """
    if not isinstance(value, str):
        raise ValueError(f"expected a comma-separated id string, got {value!r}")
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            int(token)
        except ValueError:
            raise ValueError(
                f"'{token}' is not a numeric id — use comma-separated ids",
            ) from None


AUTOMOD_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="enabled",
        value_type=bool,
        default=DEFAULT_ENABLED,
        settings_key=AUTOMOD_ENABLED,
        capability_required=_AUTOMOD_CAPABILITY,
        hint=(
            "Master switch for automod.  When off, no rule acts regardless of "
            "the per-rule toggles.  Off by default — a fresh server is "
            "unaffected."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="spam_enabled",
        value_type=bool,
        default=DEFAULT_SPAM_ENABLED,
        settings_key=AUTOMOD_SPAM_ENABLED,
        capability_required=_AUTOMOD_CAPABILITY,
        hint="Delete + warn on a burst of messages from one member in a channel.",
        validator=_validate_bool,
    ),
    SettingSpec(
        name="invites_enabled",
        value_type=bool,
        default=DEFAULT_INVITES_ENABLED,
        settings_key=AUTOMOD_INVITES_ENABLED,
        capability_required=_AUTOMOD_CAPABILITY,
        hint="Delete + warn on Discord invite links (discord.gg/…).",
        validator=_validate_bool,
    ),
    SettingSpec(
        name="caps_enabled",
        value_type=bool,
        default=DEFAULT_CAPS_ENABLED,
        settings_key=AUTOMOD_CAPS_ENABLED,
        capability_required=_AUTOMOD_CAPABILITY,
        hint="Delete + warn on messages that are mostly uppercase (shouting).",
        validator=_validate_bool,
    ),
    SettingSpec(
        name="mentions_enabled",
        value_type=bool,
        default=DEFAULT_MENTIONS_ENABLED,
        settings_key=AUTOMOD_MENTIONS_ENABLED,
        capability_required=_AUTOMOD_CAPABILITY,
        hint="Delete + warn on messages with too many @mentions (mass-ping).",
        validator=_validate_bool,
    ),
    SettingSpec(
        name="cross_channel_spam_enabled",
        value_type=bool,
        default=DEFAULT_CROSS_CHANNEL_SPAM_ENABLED,
        settings_key=AUTOMOD_CROSS_CHANNEL_SPAM_ENABLED,
        capability_required=_AUTOMOD_CAPABILITY,
        hint=(
            "Delete + warn on a burst of messages from one member spread "
            "across MULTIPLE channels — the per-channel spam rule can't see "
            "this pattern since its window is scoped to one channel."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="duplicate_enabled",
        value_type=bool,
        default=DEFAULT_DUPLICATE_ENABLED,
        settings_key=AUTOMOD_DUPLICATE_ENABLED,
        capability_required=_AUTOMOD_CAPABILITY,
        hint=(
            "Delete + warn when the same message (any channel) repeats too "
            "many times — distinct from the spam rule, which is rate-only "
            "and doesn't look at what was actually said."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="spam_count",
        value_type=int,
        default=DEFAULT_SPAM_COUNT,
        settings_key=AUTOMOD_SPAM_COUNT,
        capability_required=_AUTOMOD_CAPABILITY,
        hint=(
            "Messages from one member in one channel within the spam window "
            "before the spam rule trips."
        ),
        validator=_validate_spam_count,
        input_hint="numeric_presets",
        presets=(3, 5, 8),
    ),
    SettingSpec(
        name="spam_window_seconds",
        value_type=int,
        default=DEFAULT_SPAM_WINDOW_SECONDS,
        settings_key=AUTOMOD_SPAM_WINDOW_SECONDS,
        capability_required=_AUTOMOD_CAPABILITY,
        hint="Sliding-window length (seconds) the spam count is measured over.",
        validator=_validate_spam_window,
        input_hint="numeric_presets",
        presets=(5, 7, 10),
    ),
    SettingSpec(
        name="caps_percent",
        value_type=int,
        default=DEFAULT_CAPS_PERCENT,
        settings_key=AUTOMOD_CAPS_PERCENT,
        capability_required=_AUTOMOD_CAPABILITY,
        hint=(
            "Percentage of letters that must be uppercase before the caps rule "
            "trips (only on messages with enough letters to judge)."
        ),
        validator=_validate_caps_percent,
        input_hint="numeric_presets",
        presets=(60, 70, 80),
    ),
    SettingSpec(
        name="mentions_count",
        value_type=int,
        default=DEFAULT_MENTIONS_COUNT,
        settings_key=AUTOMOD_MENTIONS_COUNT,
        capability_required=_AUTOMOD_CAPABILITY,
        hint="Number of @mentions in one message before the mass-mention rule trips.",
        validator=_validate_mentions_count,
        input_hint="numeric_presets",
        presets=(4, 5, 8),
    ),
    SettingSpec(
        name="cross_channel_spam_count",
        value_type=int,
        default=DEFAULT_CROSS_CHANNEL_SPAM_COUNT,
        settings_key=AUTOMOD_CROSS_CHANNEL_SPAM_COUNT,
        capability_required=_AUTOMOD_CAPABILITY,
        hint=(
            "Messages from one member across ANY channels within the spam "
            "window before the cross-channel spam rule trips."
        ),
        validator=_validate_cross_channel_spam_count,
        input_hint="numeric_presets",
        presets=(3, 4, 6),
    ),
    SettingSpec(
        name="duplicate_count",
        value_type=int,
        default=DEFAULT_DUPLICATE_COUNT,
        settings_key=AUTOMOD_DUPLICATE_COUNT,
        capability_required=_AUTOMOD_CAPABILITY,
        hint=(
            "Repeats of the same message (any channel) within the spam "
            "window before the duplicate-content rule trips."
        ),
        validator=_validate_duplicate_count,
        input_hint="numeric_presets",
        presets=(2, 3, 5),
    ),
    SettingSpec(
        name="exempt_roles",
        value_type=str,
        default=DEFAULT_EXEMPT_ROLES,
        settings_key=AUTOMOD_EXEMPT_ROLES,
        capability_required=_AUTOMOD_CAPABILITY,
        hint=(
            "Comma-separated role ids whose members are never acted on "
            "(staff, bots-with-a-role, …).  Leave empty for none."
        ),
        validator=_validate_id_csv,
    ),
    SettingSpec(
        name="exempt_channels",
        value_type=str,
        default=DEFAULT_EXEMPT_CHANNELS,
        settings_key=AUTOMOD_EXEMPT_CHANNELS,
        capability_required=_AUTOMOD_CAPABILITY,
        hint=(
            "Comma-separated channel ids automod never touches "
            "(announcements, memes, …).  Leave empty for none."
        ),
        validator=_validate_id_csv,
    ),
)


AUTOMOD_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="automod",
    settings=AUTOMOD_SETTINGS,
    version=1,
)


def register_schemas() -> None:
    """Register the automod subsystem schema. Idempotent."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(AUTOMOD_CONFIG_SCHEMA)


# Re-export the tolerant parser so callers import it from one place.
__all__ = [
    "AUTOMOD_CONFIG_SCHEMA",
    "AUTOMOD_SETTINGS",
    "parse_id_csv",
    "register_schemas",
]
