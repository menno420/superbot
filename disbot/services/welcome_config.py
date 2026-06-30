"""Welcome policy — the config read model for welcome v1.

welcome v1 (owner decision Q-0110): the member-greeting layer.  Mirrors
:mod:`services.automod_config` and :mod:`services.server_logging_config`
exactly — the behaviour is loaded **once** into a frozen read model so the cog
listeners share identical config resolution.  This module owns:

* the canonical **default constants** (one source of truth shared by the
  :class:`SettingSpec` declarations in ``cogs/welcome/schemas.py`` and by
  :func:`load_policy`'s fallbacks);
* :class:`WelcomePolicy`, the frozen read model;
* :func:`load_policy`, which composes the typed values via
  :func:`services.settings_resolution.resolve_value`;
* :func:`render_template`, the injection-safe ``{user}/{server}/{count}``
  placeholder substitution shared by the embed builders and the status panel.

The settings are stored as ordinary scalar guild settings (the legacy KV
table); there is **no migration** — the keys live in
:mod:`utils.settings_keys.welcome` and are operator-editable through the
existing ``!settings`` widget dispatcher.

Cycle discipline (mirrors :mod:`services.automod_config`): the only
cross-package import (``settings_resolution``) is function-local; top-level
imports are stdlib only.
"""

from __future__ import annotations

import datetime as dt
import random
import re
from dataclasses import dataclass

SUBSYSTEM = "welcome"

# ---------------------------------------------------------------------------
# Canonical defaults — the single source of truth.
#
# ``cogs/welcome/schemas.py`` imports these for its SettingSpec ``default=``
# values; :func:`load_policy` uses them as the ``resolve_value`` fallback, so a
# spec default and a policy default can never silently drift (pinned by the
# schema test).  The master switch defaults OFF so a fresh guild is unaffected;
# join greeting defaults ON *under* the master switch (an operator who turns
# welcome on almost always wants joins greeted), farewell defaults OFF (more
# divisive — opt in).
# ---------------------------------------------------------------------------

DEFAULT_ENABLED = False  # master switch
DEFAULT_JOIN_ENABLED = True
DEFAULT_LEAVE_ENABLED = False
DEFAULT_CHANNEL = ""  # channel id string; empty disables posting
DEFAULT_ENTRY_ROLE = ""  # role id string; empty grants none
DEFAULT_JOIN_MESSAGE = "👋 Welcome {user} to **{server}**! You're member #{count}."
DEFAULT_LEAVE_MESSAGE = "👋 **{user}** has left {server}. We're now {count} members."

# Welcome phase 2 (Q-0110): attach a rendered greeting card to the join embed.
# Off by default — the embed-first v1 behaviour is unchanged for every guild
# until an operator opts the card in.
DEFAULT_CARD_ENABLED = False

# DM greeting (completion punch-list #2): also send the joining member the
# greeting as a direct message.  Off by default — needs no channel; supports
# the same placeholders + "---" random variants as the channel greeting.
DEFAULT_DM_ENABLED = False
DEFAULT_DM_MESSAGE = (
    "👋 Welcome to **{server}**, {user}! Glad to have you — you're member #{count}."
)

# Join-delay age-gating (completion punch-list #2 remainder): skip the whole
# welcome action (channel greeting, DM greeting, AND the entry-role grant) for a
# joining member whose Discord account is younger than this many days.  An
# anti-raid guard — fresh throwaway accounts in a raid don't get auto-greeted or
# auto-roled into the server.  ``0`` disables it (every account greeted), so a
# fresh guild behaves byte-identically.  Capped at one year (well past any sane
# verification window) so a typo can't lock the server out of greetings forever.
DEFAULT_MIN_ACCOUNT_AGE_DAYS = 0
MIN_MIN_ACCOUNT_AGE_DAYS = 0
MAX_MIN_ACCOUNT_AGE_DAYS = 365

# Ping-then-delete (completion punch-list #2 remainder): auto-delete the
# **channel** greeting/farewell message this many seconds after it posts (via
# discord.py's native ``delete_after``), so a high-traffic join/leave channel
# stays uncluttered.  ``0`` keeps the message forever (the v1 behaviour).  The
# DM greeting is never affected.  Capped at one hour.
DEFAULT_DELETE_AFTER_SECONDS = 0
MIN_DELETE_AFTER_SECONDS = 0
MAX_DELETE_AFTER_SECONDS = 3600

# Template length cap — keeps an embed description well within Discord's limit
# even after placeholder expansion.  Applied **per variant** (see below): with
# multiple random variants only one renders at a time, so each is capped, not
# the combined stored value.
MAX_MESSAGE_LENGTH = 500

# Multiple / random messages (completion punch-list #2): an operator may store
# several greeting/farewell variants in one message setting, separated by a
# line of three-or-more dashes (a markdown horizontal rule).  One variant is
# chosen at random per join/leave, so a server can rotate its greeting.  A
# single-variant value (the default, and every existing config) behaves
# byte-identically — the lone variant is always the chosen one.
MAX_MESSAGE_VARIANTS = 10

# A separator line is solely three-or-more dashes (after stripping surrounding
# whitespace), e.g. ``---``.  ``re.MULTILINE`` so ``^``/``$`` anchor each line.
_VARIANT_SEPARATOR_RE = re.compile(r"^\s*-{3,}\s*$", re.MULTILINE)


def split_message_variants(template: str) -> list[str]:
    """Split a message setting into its non-empty, stripped variants.

    Variants are separated by a ``---`` line (see :data:`_VARIANT_SEPARATOR_RE`).
    Returns the real variants in order; an empty list when the value holds no
    non-empty variant (only whitespace / bare separators) — the *write*-time
    validator rejects that case, and :func:`pick_message` falls back to the raw
    template so the render path stays fail-open.  A value with no separator
    yields a single-element list, so existing single-message configs are
    unchanged.
    """
    return [
        part.strip() for part in _VARIANT_SEPARATOR_RE.split(template) if part.strip()
    ]


def pick_message(template: str, *, rng: random.Random | None = None) -> str:
    """Choose one message variant at random (fail-open to the raw template).

    With a single variant the choice is deterministic (that variant), so an
    unchanged single-message config renders identically.  ``rng`` is injectable
    for deterministic tests; production uses the module-global ``random``.
    """
    variants = split_message_variants(template) or [template]
    chooser = rng if rng is not None else random
    return chooser.choice(variants)


def account_is_too_young(
    created_at: dt.datetime | None,
    *,
    min_age_days: int,
    now: dt.datetime,
) -> bool:
    """True when an account created at ``created_at`` is below the age gate.

    ``min_age_days <= 0`` disables the gate (always ``False``).  A ``None``
    ``created_at`` (unknown age) is treated as **old enough** — fail-open to a
    greeting, matching the read model's posture everywhere else (better to greet
    a legit member whose creation date we couldn't read than to silently drop
    them).  Both datetimes are expected tz-aware UTC (Discord's ``created_at``
    and :func:`discord.utils.utcnow` both are); a naive ``created_at`` is also
    tolerated by comparing only when both share awareness.
    """
    if min_age_days <= 0 or created_at is None:
        return False
    try:
        age = now - created_at
    except TypeError:
        # Mixed naive/aware comparison — don't gate on a malformed timestamp.
        return False
    return age < dt.timedelta(days=min_age_days)


@dataclass(frozen=True)
class WelcomePolicy:
    """Resolved welcome behaviour for one guild.

    ``frozen`` so it can be cached/compared safely.  The three action
    predicates below fold the master switch, the per-event flag, and the
    resource presence into the single question each handler asks.
    """

    enabled: bool = DEFAULT_ENABLED
    join_enabled: bool = DEFAULT_JOIN_ENABLED
    leave_enabled: bool = DEFAULT_LEAVE_ENABLED
    channel_id: int | None = None
    entry_role_id: int | None = None
    join_message: str = DEFAULT_JOIN_MESSAGE
    leave_message: str = DEFAULT_LEAVE_MESSAGE
    card_enabled: bool = DEFAULT_CARD_ENABLED
    dm_enabled: bool = DEFAULT_DM_ENABLED
    dm_message: str = DEFAULT_DM_MESSAGE
    min_account_age_days: int = DEFAULT_MIN_ACCOUNT_AGE_DAYS
    delete_after_seconds: int = DEFAULT_DELETE_AFTER_SECONDS

    @property
    def age_gate_enabled(self) -> bool:
        """True when the join-delay account-age gate is active."""
        return self.min_account_age_days > 0

    @property
    def greeting_delete_after(self) -> float | None:
        """Seconds after which a channel greeting/farewell self-deletes, or None.

        Returns ``None`` (keep forever — the v1 behaviour) when the setting is
        ``0``, else the value as a float for discord.py's ``delete_after``.
        """
        return (
            float(self.delete_after_seconds) if self.delete_after_seconds > 0 else None
        )

    @property
    def greet_on_join(self) -> bool:
        """True when a join should post a greeting (needs a destination)."""
        return self.enabled and self.join_enabled and self.channel_id is not None

    @property
    def greet_on_leave(self) -> bool:
        """True when a leave should post a farewell (needs a destination)."""
        return self.enabled and self.leave_enabled and self.channel_id is not None

    @property
    def show_join_card(self) -> bool:
        """True when a join greeting should carry the rendered welcome card."""
        return self.greet_on_join and self.card_enabled

    @property
    def assigns_entry_role(self) -> bool:
        """True when a join should grant the entry role."""
        return self.enabled and self.entry_role_id is not None

    @property
    def dm_on_join(self) -> bool:
        """True when a join should DM the member the greeting (no channel needed)."""
        return self.enabled and self.dm_enabled

    @property
    def any_action_enabled(self) -> bool:
        """True when at least one welcome action could fire (gated by enabled)."""
        return (
            self.greet_on_join
            or self.greet_on_leave
            or self.assigns_entry_role
            or self.dm_on_join
        )


def parse_id(raw: object) -> int | None:
    """Parse a single id setting (channel/role) into an int, or None.

    Tolerant: a blank or malformed value degrades to "unset" rather than
    raising, so a fat-fingered id never disables the whole policy load.  The
    *write*-time validator (``cogs/welcome/schemas.py``) is the loud gate.
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


def render_template(
    template: str,
    *,
    member_name: str,
    guild_name: str,
    member_count: int,
) -> str:
    """Substitute the ``{user}/{server}/{count}`` placeholders, injection-safe.

    Uses plain ``str.replace`` rather than ``str.format`` so an operator
    template containing stray ``{`` / ``}`` (or a ``{foo}`` typo) renders
    literally instead of raising ``KeyError``/``IndexError`` — the same
    fail-open posture the read model takes elsewhere.
    """
    return (
        template.replace("{user}", member_name)
        .replace("{server}", guild_name)
        .replace("{count}", f"{member_count:,}")
    )


async def load_policy(guild_id: int) -> WelcomePolicy:
    """Load the effective :class:`WelcomePolicy` for ``guild_id``.

    Each field resolves through :func:`services.settings_resolution.resolve_value`
    so coercion, validation, and provenance stay centralised; a missing or
    malformed stored value transparently falls back to the canonical default.
    """
    from services.settings_resolution import resolve_value

    enabled = await resolve_value(guild_id, SUBSYSTEM, "enabled", DEFAULT_ENABLED)
    join_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "join_enabled",
        DEFAULT_JOIN_ENABLED,
    )
    leave_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "leave_enabled",
        DEFAULT_LEAVE_ENABLED,
    )
    channel_raw = await resolve_value(guild_id, SUBSYSTEM, "channel", DEFAULT_CHANNEL)
    entry_role_raw = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "entry_role",
        DEFAULT_ENTRY_ROLE,
    )
    join_message = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "join_message",
        DEFAULT_JOIN_MESSAGE,
    )
    leave_message = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "leave_message",
        DEFAULT_LEAVE_MESSAGE,
    )
    card_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "card_enabled",
        DEFAULT_CARD_ENABLED,
    )
    dm_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "dm_enabled",
        DEFAULT_DM_ENABLED,
    )
    dm_message = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "dm_message",
        DEFAULT_DM_MESSAGE,
    )
    min_account_age_days = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "min_account_age_days",
        DEFAULT_MIN_ACCOUNT_AGE_DAYS,
    )
    delete_after_seconds = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "delete_after_seconds",
        DEFAULT_DELETE_AFTER_SECONDS,
    )

    return WelcomePolicy(
        enabled=enabled,
        join_enabled=join_enabled,
        leave_enabled=leave_enabled,
        channel_id=parse_id(channel_raw),
        entry_role_id=parse_id(entry_role_raw),
        join_message=join_message,
        leave_message=leave_message,
        card_enabled=card_enabled,
        dm_enabled=dm_enabled,
        dm_message=dm_message,
        min_account_age_days=min_account_age_days,
        delete_after_seconds=delete_after_seconds,
    )


__all__ = [
    "DEFAULT_CARD_ENABLED",
    "DEFAULT_CHANNEL",
    "DEFAULT_DELETE_AFTER_SECONDS",
    "DEFAULT_DM_ENABLED",
    "DEFAULT_DM_MESSAGE",
    "DEFAULT_ENABLED",
    "DEFAULT_ENTRY_ROLE",
    "DEFAULT_JOIN_ENABLED",
    "DEFAULT_JOIN_MESSAGE",
    "DEFAULT_LEAVE_ENABLED",
    "DEFAULT_LEAVE_MESSAGE",
    "DEFAULT_MIN_ACCOUNT_AGE_DAYS",
    "MAX_DELETE_AFTER_SECONDS",
    "MAX_MESSAGE_LENGTH",
    "MAX_MESSAGE_VARIANTS",
    "MAX_MIN_ACCOUNT_AGE_DAYS",
    "MIN_DELETE_AFTER_SECONDS",
    "MIN_MIN_ACCOUNT_AGE_DAYS",
    "WelcomePolicy",
    "account_is_too_young",
    "load_policy",
    "parse_id",
    "pick_message",
    "render_template",
    "split_message_variants",
]
