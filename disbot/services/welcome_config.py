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

# Template length cap — keeps an embed description well within Discord's limit
# even after placeholder expansion.
MAX_MESSAGE_LENGTH = 500


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
    def any_action_enabled(self) -> bool:
        """True when at least one welcome action could fire (gated by enabled)."""
        return self.greet_on_join or self.greet_on_leave or self.assigns_entry_role


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

    return WelcomePolicy(
        enabled=enabled,
        join_enabled=join_enabled,
        leave_enabled=leave_enabled,
        channel_id=parse_id(channel_raw),
        entry_role_id=parse_id(entry_role_raw),
        join_message=join_message,
        leave_message=leave_message,
        card_enabled=card_enabled,
    )


__all__ = [
    "DEFAULT_CARD_ENABLED",
    "DEFAULT_CHANNEL",
    "DEFAULT_ENABLED",
    "DEFAULT_ENTRY_ROLE",
    "DEFAULT_JOIN_ENABLED",
    "DEFAULT_JOIN_MESSAGE",
    "DEFAULT_LEAVE_ENABLED",
    "DEFAULT_LEAVE_MESSAGE",
    "MAX_MESSAGE_LENGTH",
    "WelcomePolicy",
    "load_policy",
    "parse_id",
    "render_template",
]
