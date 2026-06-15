"""Security policy — the config read model for security tiers 1+2.

Security tiers 1+2 (owner decision Q-0111): **raid detection** + **account-age
filter**, the two APPROVED tiers. Tiers 3+4 (alt-detection / VPN blocking) were
DECLINED (GDPR) and own no config here. Mirrors :mod:`services.welcome_config`
and :mod:`services.automod_config` exactly — behaviour is loaded **once** into a
frozen read model so the cog listener shares identical config resolution.

This module owns:

* the canonical **default constants** (one source of truth shared by the
  :class:`SettingSpec` declarations in ``cogs/security/schemas.py`` and by
  :func:`load_policy`'s fallbacks);
* :class:`SecurityPolicy`, the frozen read model, with the action predicates
  each handler folds the master switch + per-tier flag + resource presence into;
* :func:`load_policy`, which composes the typed values via
  :func:`services.settings_resolution.resolve_value`.

Settings are scalar guild settings (the legacy KV table) — **no migration** —
declared in :mod:`utils.settings_keys.security`. Cycle discipline (mirrors
:mod:`services.welcome_config`): the only cross-package import
(``settings_resolution``) is function-local; top-level imports are stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass

SUBSYSTEM = "security"

# ---------------------------------------------------------------------------
# Canonical defaults — the single source of truth (shared with the schema).
#
# The master switch + each tier flag default OFF, so a fresh guild behaves
# exactly as today. The numeric thresholds are sane starting points an operator
# can tune; they only matter once a tier is turned on under the master switch.
# ---------------------------------------------------------------------------

DEFAULT_ENABLED = False  # master switch

# Tier 1 — raid detection. >= JOIN_COUNT joins within WINDOW_SECONDS triggers a
# staff alert (+ optional auto-slowmode on the configured channel for
# LOCKDOWN_SECONDS, then auto-restored).
DEFAULT_RAID_ENABLED = False
DEFAULT_RAID_JOIN_COUNT = 10
DEFAULT_RAID_WINDOW_SECONDS = 60
DEFAULT_RAID_SLOWMODE_SECONDS = 10  # slowmode to apply during a raid; 0 = none
DEFAULT_RAID_LOCKDOWN_SECONDS = 300  # how long a raid lockdown holds before lifting
DEFAULT_RAID_SLOWMODE_CHANNEL = (
    ""  # channel id string; empty = alert-only (no slowmode)
)

# Tier 2 — account-age filter. An account younger than MIN_DAYS on join is acted
# on per ACTION. "alert" (default, safest) = staff alert only; "kick" = reject
# via moderation_service.kick (+ alert). "quarantine" (role isolation) is the
# documented phase-2 value — not wired in v1.
DEFAULT_AGE_ENABLED = False
DEFAULT_AGE_MIN_DAYS = 7
ACTION_ALERT = "alert"
ACTION_KICK = "kick"
AGE_ACTIONS = (ACTION_ALERT, ACTION_KICK)
DEFAULT_AGE_ACTION = ACTION_ALERT

# Shared — where staff alerts are posted. Empty disables alert posting (the
# detector still runs and emits its advisory event, but nothing is sent).
DEFAULT_ALERT_CHANNEL = ""

# Guardrails so a fat-fingered/hostile setting can never produce an absurd
# detector (e.g. a 0-second window that fires on every join, or a multi-hour
# slowmode). The read model clamps; the schema validator is the loud write gate.
MIN_RAID_JOIN_COUNT = 2
MAX_RAID_JOIN_COUNT = 100
MIN_RAID_WINDOW_SECONDS = 5
MAX_RAID_WINDOW_SECONDS = 3600
MIN_AGE_DAYS = 1
MAX_AGE_DAYS = 365
MAX_SLOWMODE_SECONDS = 21600  # Discord's per-channel slowmode ceiling
MAX_LOCKDOWN_SECONDS = 86400


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


@dataclass(frozen=True)
class SecurityPolicy:
    """Resolved security behaviour for one guild (frozen for safe caching).

    The action predicates below fold the master switch + the per-tier flag into
    the single question each handler asks, so a handler never re-derives the
    gate logic.
    """

    enabled: bool = DEFAULT_ENABLED
    # Tier 1.
    raid_enabled: bool = DEFAULT_RAID_ENABLED
    raid_join_count: int = DEFAULT_RAID_JOIN_COUNT
    raid_window_seconds: int = DEFAULT_RAID_WINDOW_SECONDS
    raid_slowmode_seconds: int = DEFAULT_RAID_SLOWMODE_SECONDS
    raid_lockdown_seconds: int = DEFAULT_RAID_LOCKDOWN_SECONDS
    raid_slowmode_channel_id: int | None = None
    # Tier 2.
    age_enabled: bool = DEFAULT_AGE_ENABLED
    age_min_days: int = DEFAULT_AGE_MIN_DAYS
    age_action: str = DEFAULT_AGE_ACTION
    # Shared.
    alert_channel_id: int | None = None

    @property
    def raid_detection_on(self) -> bool:
        """True when join-rate raid detection should run."""
        return self.enabled and self.raid_enabled

    @property
    def age_filter_on(self) -> bool:
        """True when the account-age filter should run."""
        return self.enabled and self.age_enabled

    @property
    def applies_raid_slowmode(self) -> bool:
        """True when a raid lockdown should raise slowmode on a real channel."""
        return (
            self.raid_slowmode_channel_id is not None and self.raid_slowmode_seconds > 0
        )

    @property
    def any_tier_enabled(self) -> bool:
        """True when at least one tier could fire (gated by the master switch)."""
        return self.raid_detection_on or self.age_filter_on


def parse_id(raw: object) -> int | None:
    """Parse a single id setting (channel) into an int, or ``None``.

    Tolerant: a blank or malformed value degrades to "unset" rather than
    raising, so a fat-fingered id never disables the whole policy load. The
    write-time validator (``cogs/security/schemas.py``) is the loud gate.
    """
    if raw is None:
        return None
    token = str(raw).strip()
    if not token:
        return None
    try:
        return int(token)
    except ValueError:
        return None


def _coerce_int(raw: object, default: int) -> int:
    """Coerce a stored value to int, falling back to ``default`` on garbage."""
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


async def load_policy(guild_id: int) -> SecurityPolicy:
    """Load the effective :class:`SecurityPolicy` for ``guild_id``.

    Each field resolves through
    :func:`services.settings_resolution.resolve_value`, so coercion, validation,
    and provenance stay centralised; a missing or malformed stored value falls
    back to the canonical default. Numeric thresholds are clamped to the
    guardrail ranges so no setting can produce an absurd detector.
    """
    from services.settings_resolution import resolve_value

    enabled = await resolve_value(guild_id, SUBSYSTEM, "enabled", DEFAULT_ENABLED)

    raid_enabled = await resolve_value(
        guild_id, SUBSYSTEM, "raid_enabled", DEFAULT_RAID_ENABLED,
    )
    raid_join_count = _coerce_int(
        await resolve_value(
            guild_id, SUBSYSTEM, "raid_join_count", DEFAULT_RAID_JOIN_COUNT,
        ),
        DEFAULT_RAID_JOIN_COUNT,
    )
    raid_window_seconds = _coerce_int(
        await resolve_value(
            guild_id, SUBSYSTEM, "raid_window_seconds", DEFAULT_RAID_WINDOW_SECONDS,
        ),
        DEFAULT_RAID_WINDOW_SECONDS,
    )
    raid_slowmode_seconds = _coerce_int(
        await resolve_value(
            guild_id,
            SUBSYSTEM,
            "raid_slowmode_seconds",
            DEFAULT_RAID_SLOWMODE_SECONDS,
        ),
        DEFAULT_RAID_SLOWMODE_SECONDS,
    )
    raid_lockdown_seconds = _coerce_int(
        await resolve_value(
            guild_id,
            SUBSYSTEM,
            "raid_lockdown_seconds",
            DEFAULT_RAID_LOCKDOWN_SECONDS,
        ),
        DEFAULT_RAID_LOCKDOWN_SECONDS,
    )
    raid_slowmode_channel_raw = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "raid_slowmode_channel",
        DEFAULT_RAID_SLOWMODE_CHANNEL,
    )

    age_enabled = await resolve_value(
        guild_id, SUBSYSTEM, "age_enabled", DEFAULT_AGE_ENABLED,
    )
    age_min_days = _coerce_int(
        await resolve_value(guild_id, SUBSYSTEM, "age_min_days", DEFAULT_AGE_MIN_DAYS),
        DEFAULT_AGE_MIN_DAYS,
    )
    age_action_raw = await resolve_value(
        guild_id, SUBSYSTEM, "age_action", DEFAULT_AGE_ACTION,
    )
    age_action = (
        str(age_action_raw).strip().lower()
        if str(age_action_raw).strip().lower() in AGE_ACTIONS
        else DEFAULT_AGE_ACTION
    )

    alert_channel_raw = await resolve_value(
        guild_id, SUBSYSTEM, "alert_channel", DEFAULT_ALERT_CHANNEL,
    )

    return SecurityPolicy(
        enabled=enabled,
        raid_enabled=raid_enabled,
        raid_join_count=_clamp(
            raid_join_count, MIN_RAID_JOIN_COUNT, MAX_RAID_JOIN_COUNT,
        ),
        raid_window_seconds=_clamp(
            raid_window_seconds, MIN_RAID_WINDOW_SECONDS, MAX_RAID_WINDOW_SECONDS,
        ),
        raid_slowmode_seconds=_clamp(raid_slowmode_seconds, 0, MAX_SLOWMODE_SECONDS),
        raid_lockdown_seconds=_clamp(raid_lockdown_seconds, 0, MAX_LOCKDOWN_SECONDS),
        raid_slowmode_channel_id=parse_id(raid_slowmode_channel_raw),
        age_enabled=age_enabled,
        age_min_days=_clamp(age_min_days, MIN_AGE_DAYS, MAX_AGE_DAYS),
        age_action=age_action,
        alert_channel_id=parse_id(alert_channel_raw),
    )


__all__ = [
    "ACTION_ALERT",
    "ACTION_KICK",
    "AGE_ACTIONS",
    "DEFAULT_AGE_ACTION",
    "DEFAULT_AGE_ENABLED",
    "DEFAULT_AGE_MIN_DAYS",
    "DEFAULT_ALERT_CHANNEL",
    "DEFAULT_ENABLED",
    "DEFAULT_RAID_ENABLED",
    "DEFAULT_RAID_JOIN_COUNT",
    "DEFAULT_RAID_LOCKDOWN_SECONDS",
    "DEFAULT_RAID_SLOWMODE_CHANNEL",
    "DEFAULT_RAID_SLOWMODE_SECONDS",
    "DEFAULT_RAID_WINDOW_SECONDS",
    "MAX_AGE_DAYS",
    "MAX_LOCKDOWN_SECONDS",
    "MAX_RAID_JOIN_COUNT",
    "MAX_RAID_WINDOW_SECONDS",
    "MAX_SLOWMODE_SECONDS",
    "MIN_AGE_DAYS",
    "MIN_RAID_JOIN_COUNT",
    "MIN_RAID_WINDOW_SECONDS",
    "SecurityPolicy",
    "load_policy",
    "parse_id",
]
