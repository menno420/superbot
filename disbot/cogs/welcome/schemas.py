"""Welcome subsystem schema — operator config for member greetings.

Declares the typed guild-config schema for welcome v1 (Q-0110): a master
switch, two per-event enable flags, the destination channel, the join/leave
message templates, and the optional entry role.  All settings are scalar guild
settings (the legacy KV table) — **no migration**.  Declaring the
:class:`SubsystemSchema` makes welcome an actionable Settings group surfaced
through the existing ``!settings`` widget.

The ``default=`` values come from :mod:`services.welcome_config` (the single
source of truth shared with :func:`services.welcome_config.load_policy`), so a
spec default and a policy default can never silently drift — pinned by
``test_welcome_schemas``.

The channel/role settings carry ``input_hint`` so the S6 edit-flow renders a
Discord channel/role picker; the stored value is the id as a string (the same
``channel-id-as-str`` duality the xp/economy log-channel settings use).
"""

from __future__ import annotations

from core.runtime.subsystem_schema import (
    SettingSpec,
    SubsystemSchema,
)
from services.welcome_config import (
    DEFAULT_CARD_ENABLED,
    DEFAULT_CHANNEL,
    DEFAULT_DELETE_AFTER_SECONDS,
    DEFAULT_DM_ENABLED,
    DEFAULT_DM_MESSAGE,
    DEFAULT_ENABLED,
    DEFAULT_ENTRY_ROLE,
    DEFAULT_JOIN_ENABLED,
    DEFAULT_JOIN_MESSAGE,
    DEFAULT_LEAVE_ENABLED,
    DEFAULT_LEAVE_MESSAGE,
    DEFAULT_MIN_ACCOUNT_AGE_DAYS,
    MAX_DELETE_AFTER_SECONDS,
    MAX_MESSAGE_LENGTH,
    MAX_MESSAGE_VARIANTS,
    MAX_MIN_ACCOUNT_AGE_DAYS,
    MIN_DELETE_AFTER_SECONDS,
    MIN_MIN_ACCOUNT_AGE_DAYS,
    split_message_variants,
)
from utils.settings_keys import (
    WELCOME_CARD_ENABLED,
    WELCOME_CHANNEL,
    WELCOME_DELETE_AFTER_SECONDS,
    WELCOME_DM_ENABLED,
    WELCOME_DM_MESSAGE,
    WELCOME_ENABLED,
    WELCOME_ENTRY_ROLE,
    WELCOME_JOIN_ENABLED,
    WELCOME_JOIN_MESSAGE,
    WELCOME_LEAVE_ENABLED,
    WELCOME_LEAVE_MESSAGE,
    WELCOME_MIN_ACCOUNT_AGE_DAYS,
)

_WELCOME_CAPABILITY = "welcome.settings.configure"


def _validate_bool(value: object) -> None:
    # ``isinstance(True, int)`` is True, so guard the bool type explicitly.
    if not isinstance(value, bool):
        raise ValueError(f"expected bool, got {value!r}")


def _validate_id(value: object) -> None:
    """Accept an empty string (unset) or a single numeric id.

    The read model's ``parse_id`` is tolerant (it must never raise); this is
    the loud *write*-time gate so a fat-fingered channel/role id is rejected
    with feedback instead of silently degrading to "unset".
    """
    if not isinstance(value, str):
        raise ValueError(f"expected a channel/role id string, got {value!r}")
    token = value.strip()
    if not token:
        return  # empty = unset
    try:
        int(token)
    except ValueError:
        raise ValueError(f"'{token}' is not a numeric id") from None


def _bounded_int(value: object, lo: int, hi: int) -> None:
    # ``isinstance(True, int)`` is True, so guard the bool type explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"expected int, got {value!r}")
    if not (lo <= value <= hi):
        raise ValueError(f"must be between {lo} and {hi}")


def _validate_min_account_age_days(value: object) -> None:
    _bounded_int(value, MIN_MIN_ACCOUNT_AGE_DAYS, MAX_MIN_ACCOUNT_AGE_DAYS)


def _validate_delete_after_seconds(value: object) -> None:
    _bounded_int(value, MIN_DELETE_AFTER_SECONDS, MAX_DELETE_AFTER_SECONDS)


def _validate_message(value: object) -> None:
    """One or more non-empty variants, each within the per-variant length cap.

    Placeholders (``{user}``/``{server}``/``{count}``) are substituted at
    render time by ``welcome_config.render_template`` (injection-safe), so any
    text is accepted here — only emptiness, variant count, and per-variant
    length are gated.  Multiple ``---``-separated variants are picked from at
    random on each greeting; a single message (no separator) validates exactly
    as before (one variant, capped at ``MAX_MESSAGE_LENGTH``).
    """
    if not isinstance(value, str):
        raise ValueError(f"expected a message template string, got {value!r}")
    variants = split_message_variants(value)
    if not variants:
        raise ValueError("message template cannot be empty")
    if len(variants) > MAX_MESSAGE_VARIANTS:
        raise ValueError(
            f"at most {MAX_MESSAGE_VARIANTS} message variants "
            f"(separate them with a '---' line), got {len(variants)}",
        )
    for variant in variants:
        if len(variant) > MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"each message variant must be <= {MAX_MESSAGE_LENGTH} characters",
            )


WELCOME_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="enabled",
        value_type=bool,
        default=DEFAULT_ENABLED,
        settings_key=WELCOME_ENABLED,
        capability_required=_WELCOME_CAPABILITY,
        hint=(
            "Master switch for welcome.  When off, no greeting posts and no "
            "entry role is granted regardless of the per-event toggles.  Off "
            "by default — a fresh server is unaffected."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="join_enabled",
        value_type=bool,
        default=DEFAULT_JOIN_ENABLED,
        settings_key=WELCOME_JOIN_ENABLED,
        capability_required=_WELCOME_CAPABILITY,
        hint="Post a greeting embed in the welcome channel when a member joins.",
        validator=_validate_bool,
    ),
    SettingSpec(
        name="leave_enabled",
        value_type=bool,
        default=DEFAULT_LEAVE_ENABLED,
        settings_key=WELCOME_LEAVE_ENABLED,
        capability_required=_WELCOME_CAPABILITY,
        hint="Post a farewell embed in the welcome channel when a member leaves.",
        validator=_validate_bool,
    ),
    SettingSpec(
        name="channel",
        value_type=str,
        default=DEFAULT_CHANNEL,
        settings_key=WELCOME_CHANNEL,
        capability_required=_WELCOME_CAPABILITY,
        hint=(
            "Channel where greeting/farewell embeds are posted.  Leave unset "
            "to disable posting (the entry role still works)."
        ),
        validator=_validate_id,
        input_hint="channel",
    ),
    SettingSpec(
        name="join_message",
        value_type=str,
        default=DEFAULT_JOIN_MESSAGE,
        settings_key=WELCOME_JOIN_MESSAGE,
        capability_required=_WELCOME_CAPABILITY,
        hint=(
            "Greeting template.  Placeholders: {user} (mention), {server} "
            "(name), {count} (member number).  Add several variants separated "
            "by a '---' line to greet joiners with a random one each time."
        ),
        validator=_validate_message,
    ),
    SettingSpec(
        name="leave_message",
        value_type=str,
        default=DEFAULT_LEAVE_MESSAGE,
        settings_key=WELCOME_LEAVE_MESSAGE,
        capability_required=_WELCOME_CAPABILITY,
        hint=(
            "Farewell template.  Placeholders: {user} (name), {server} "
            "(name), {count} (remaining members).  Add several variants "
            "separated by a '---' line to post a random one each time."
        ),
        validator=_validate_message,
    ),
    SettingSpec(
        name="entry_role",
        value_type=str,
        default=DEFAULT_ENTRY_ROLE,
        settings_key=WELCOME_ENTRY_ROLE,
        capability_required=_WELCOME_CAPABILITY,
        hint=(
            "Role granted the moment a member joins (e.g. a base Member role).  "
            "Leave unset for none.  Granted through moderation's audited role "
            "path."
        ),
        validator=_validate_id,
        input_hint="role",
    ),
    SettingSpec(
        name="card_enabled",
        value_type=bool,
        default=DEFAULT_CARD_ENABLED,
        settings_key=WELCOME_CARD_ENABLED,
        capability_required=_WELCOME_CAPABILITY,
        hint=(
            "Attach a rendered welcome card image to the join greeting "
            "(phase 2).  Off by default; falls back to the embed-only "
            "greeting when image rendering is unavailable."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="dm_enabled",
        value_type=bool,
        default=DEFAULT_DM_ENABLED,
        settings_key=WELCOME_DM_ENABLED,
        capability_required=_WELCOME_CAPABILITY,
        hint=(
            "Also send the joining member a direct-message greeting (in "
            "addition to the channel greeting).  Off by default; needs no "
            "channel.  Silently skipped for members with DMs closed."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="dm_message",
        value_type=str,
        default=DEFAULT_DM_MESSAGE,
        settings_key=WELCOME_DM_MESSAGE,
        capability_required=_WELCOME_CAPABILITY,
        hint=(
            "Direct-message greeting template.  Placeholders: {user} (mention), "
            "{server} (name), {count} (member number).  Add several variants "
            "separated by a '---' line to DM a random one each time."
        ),
        validator=_validate_message,
    ),
    SettingSpec(
        name="min_account_age_days",
        value_type=int,
        default=DEFAULT_MIN_ACCOUNT_AGE_DAYS,
        settings_key=WELCOME_MIN_ACCOUNT_AGE_DAYS,
        capability_required=_WELCOME_CAPABILITY,
        hint=(
            "Anti-raid: skip the greeting, DM, and entry role for a joining "
            "member whose Discord account is younger than this many days.  "
            "0 disables it (every account is greeted)."
        ),
        validator=_validate_min_account_age_days,
        input_hint="numeric_presets",
        presets=(0, 1, 7),
    ),
    SettingSpec(
        name="delete_after_seconds",
        value_type=int,
        default=DEFAULT_DELETE_AFTER_SECONDS,
        settings_key=WELCOME_DELETE_AFTER_SECONDS,
        capability_required=_WELCOME_CAPABILITY,
        hint=(
            "Ping-then-delete: auto-delete the channel greeting/farewell this "
            "many seconds after it posts, to keep a busy channel tidy.  "
            "0 keeps the message.  The DM greeting is never deleted."
        ),
        validator=_validate_delete_after_seconds,
        input_hint="numeric_presets",
        presets=(0, 30, 60),
    ),
)


WELCOME_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="welcome",
    settings=WELCOME_SETTINGS,
    version=1,
)


def register_schemas() -> None:
    """Register the welcome subsystem schema. Idempotent."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(WELCOME_CONFIG_SCHEMA)


__all__ = [
    "WELCOME_CONFIG_SCHEMA",
    "WELCOME_SETTINGS",
    "register_schemas",
]
