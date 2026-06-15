"""Security subsystem schema — operator config for tiers 1+2 (Q-0111).

Declares the typed guild-config schema for raid detection + the account-age
filter: a master switch, the two per-tier enable flags, their numeric
thresholds, the action enum, and two channel pointers (the staff-alert channel
and the raid-slowmode channel). All settings are scalar guild settings (the
legacy KV table) — **no migration**. Declaring the :class:`SubsystemSchema`
makes security an actionable Settings group surfaced through ``!settings``.

The ``default=`` values come from :mod:`services.security_config` (the single
source of truth shared with :func:`services.security_config.load_policy`), so a
spec default and a policy default can never silently drift — pinned by
``test_security_schemas``. The two DECLINED tiers own no specs here.
"""

from __future__ import annotations

from core.runtime.subsystem_schema import SettingSpec, SubsystemSchema
from services.security_config import (
    AGE_ACTIONS,
    DEFAULT_AGE_ACTION,
    DEFAULT_AGE_ENABLED,
    DEFAULT_AGE_MIN_DAYS,
    DEFAULT_ALERT_CHANNEL,
    DEFAULT_ENABLED,
    DEFAULT_RAID_ENABLED,
    DEFAULT_RAID_JOIN_COUNT,
    DEFAULT_RAID_LOCKDOWN_SECONDS,
    DEFAULT_RAID_SLOWMODE_CHANNEL,
    DEFAULT_RAID_SLOWMODE_SECONDS,
    DEFAULT_RAID_WINDOW_SECONDS,
    MAX_AGE_DAYS,
    MAX_LOCKDOWN_SECONDS,
    MAX_RAID_JOIN_COUNT,
    MAX_RAID_WINDOW_SECONDS,
    MAX_SLOWMODE_SECONDS,
    MIN_AGE_DAYS,
    MIN_RAID_JOIN_COUNT,
    MIN_RAID_WINDOW_SECONDS,
)
from utils.settings_keys import (
    SECURITY_AGE_ACTION,
    SECURITY_AGE_ENABLED,
    SECURITY_AGE_MIN_DAYS,
    SECURITY_ALERT_CHANNEL,
    SECURITY_ENABLED,
    SECURITY_RAID_ENABLED,
    SECURITY_RAID_JOIN_COUNT,
    SECURITY_RAID_LOCKDOWN_SECONDS,
    SECURITY_RAID_SLOWMODE_CHANNEL,
    SECURITY_RAID_SLOWMODE_SECONDS,
    SECURITY_RAID_WINDOW_SECONDS,
)

_SECURITY_CAPABILITY = "security.settings.configure"


def _validate_bool(value: object) -> None:
    # ``isinstance(True, int)`` is True, so guard the bool type explicitly.
    if not isinstance(value, bool):
        raise ValueError(f"expected bool, got {value!r}")


def _int_validator(low: int, high: int):
    """A loud write-time gate for an int setting bounded to ``[low, high]``."""

    def _validate(value: object) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"expected an integer, got {value!r}")
        if not low <= value <= high:
            raise ValueError(f"value must be between {low} and {high}")

    return _validate


def _validate_action(value: object) -> None:
    if not isinstance(value, str) or value.strip().lower() not in AGE_ACTIONS:
        raise ValueError(f"action must be one of {AGE_ACTIONS}, got {value!r}")


def _validate_id(value: object) -> None:
    """Accept an empty string (unset) or a single numeric id."""
    if not isinstance(value, str):
        raise ValueError(f"expected a channel id string, got {value!r}")
    token = value.strip()
    if not token:
        return  # empty = unset
    try:
        int(token)
    except ValueError:
        raise ValueError(f"'{token}' is not a numeric id") from None


SECURITY_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="enabled",
        value_type=bool,
        default=DEFAULT_ENABLED,
        settings_key=SECURITY_ENABLED,
        capability_required=_SECURITY_CAPABILITY,
        hint=(
            "Master switch for server security (raid detection + account-age "
            "filter). When off, neither tier runs regardless of its own toggle. "
            "Off by default — a fresh server is unaffected."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="alert_channel",
        value_type=str,
        default=DEFAULT_ALERT_CHANNEL,
        settings_key=SECURITY_ALERT_CHANNEL,
        capability_required=_SECURITY_CAPABILITY,
        hint=(
            "Channel where staff security alerts (raid suspected / young account) "
            "are posted. Leave unset to run detection silently (events still fire)."
        ),
        validator=_validate_id,
        input_hint="channel",
    ),
    # ── Tier 1 — raid detection ──────────────────────────────────────────
    SettingSpec(
        name="raid_enabled",
        value_type=bool,
        default=DEFAULT_RAID_ENABLED,
        settings_key=SECURITY_RAID_ENABLED,
        capability_required=_SECURITY_CAPABILITY,
        hint="Tier 1: watch the join rate and alert staff on a suspected raid.",
        validator=_validate_bool,
    ),
    SettingSpec(
        name="raid_join_count",
        value_type=int,
        default=DEFAULT_RAID_JOIN_COUNT,
        settings_key=SECURITY_RAID_JOIN_COUNT,
        capability_required=_SECURITY_CAPABILITY,
        hint=(
            f"Joins within the window that trigger a raid alert "
            f"({MIN_RAID_JOIN_COUNT}-{MAX_RAID_JOIN_COUNT})."
        ),
        validator=_int_validator(MIN_RAID_JOIN_COUNT, MAX_RAID_JOIN_COUNT),
    ),
    SettingSpec(
        name="raid_window_seconds",
        value_type=int,
        default=DEFAULT_RAID_WINDOW_SECONDS,
        settings_key=SECURITY_RAID_WINDOW_SECONDS,
        capability_required=_SECURITY_CAPABILITY,
        hint=(
            f"Sliding window in seconds for the join-rate count "
            f"({MIN_RAID_WINDOW_SECONDS}-{MAX_RAID_WINDOW_SECONDS})."
        ),
        validator=_int_validator(MIN_RAID_WINDOW_SECONDS, MAX_RAID_WINDOW_SECONDS),
    ),
    SettingSpec(
        name="raid_slowmode_channel",
        value_type=str,
        default=DEFAULT_RAID_SLOWMODE_CHANNEL,
        settings_key=SECURITY_RAID_SLOWMODE_CHANNEL,
        capability_required=_SECURITY_CAPABILITY,
        hint=(
            "Channel whose slowmode is raised during a raid lockdown. Leave unset "
            "for alert-only (no slowmode applied)."
        ),
        validator=_validate_id,
        input_hint="channel",
    ),
    SettingSpec(
        name="raid_slowmode_seconds",
        value_type=int,
        default=DEFAULT_RAID_SLOWMODE_SECONDS,
        settings_key=SECURITY_RAID_SLOWMODE_SECONDS,
        capability_required=_SECURITY_CAPABILITY,
        hint=(
            f"Slowmode (seconds) applied to the lockdown channel during a raid "
            f"(0-{MAX_SLOWMODE_SECONDS}; 0 disables slowmode)."
        ),
        validator=_int_validator(0, MAX_SLOWMODE_SECONDS),
    ),
    SettingSpec(
        name="raid_lockdown_seconds",
        value_type=int,
        default=DEFAULT_RAID_LOCKDOWN_SECONDS,
        settings_key=SECURITY_RAID_LOCKDOWN_SECONDS,
        capability_required=_SECURITY_CAPABILITY,
        hint=(
            f"How long a raid lockdown holds before slowmode is auto-restored "
            f"(0-{MAX_LOCKDOWN_SECONDS} seconds)."
        ),
        validator=_int_validator(0, MAX_LOCKDOWN_SECONDS),
    ),
    # ── Tier 2 — account-age filter ──────────────────────────────────────
    SettingSpec(
        name="age_enabled",
        value_type=bool,
        default=DEFAULT_AGE_ENABLED,
        settings_key=SECURITY_AGE_ENABLED,
        capability_required=_SECURITY_CAPABILITY,
        hint="Tier 2: screen joining accounts younger than the threshold.",
        validator=_validate_bool,
    ),
    SettingSpec(
        name="age_min_days",
        value_type=int,
        default=DEFAULT_AGE_MIN_DAYS,
        settings_key=SECURITY_AGE_MIN_DAYS,
        capability_required=_SECURITY_CAPABILITY,
        hint=(
            f"Minimum account age in days; younger accounts are acted on "
            f"({MIN_AGE_DAYS}-{MAX_AGE_DAYS})."
        ),
        validator=_int_validator(MIN_AGE_DAYS, MAX_AGE_DAYS),
    ),
    SettingSpec(
        name="age_action",
        value_type=str,
        default=DEFAULT_AGE_ACTION,
        settings_key=SECURITY_AGE_ACTION,
        capability_required=_SECURITY_CAPABILITY,
        hint=(
            "Action on a too-young account: 'alert' (staff alert only) or 'kick' "
            "(reject via moderation, with an alert)."
        ),
        validator=_validate_action,
        allowed_values=AGE_ACTIONS,
    ),
)


SECURITY_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="security",
    settings=SECURITY_SETTINGS,
    version=1,
)


def register_schemas() -> None:
    """Register the security subsystem schema. Idempotent."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(SECURITY_CONFIG_SCHEMA)


__all__ = [
    "SECURITY_CONFIG_SCHEMA",
    "SECURITY_SETTINGS",
    "register_schemas",
]
