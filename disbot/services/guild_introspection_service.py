"""Read-only guild introspection shaped for the AI tool layer.

Turns a live ``discord.Guild`` (and the asking member) into small,
JSON-serialisable dicts the natural-language AI tools hand to the
model so it can answer "tell me about this server" questions — roles,
channels, a high-level overview, and (opt-in) member lookups.

Why this is separate from :mod:`services.guild_snapshot`
-------------------------------------------------------
``guild_snapshot`` builds the *setup advisor's* metadata snapshot:
bot-relative permission flags, settings/bindings catalogues, and a
resource-health pass. The AI tools need a different shape — channel
visibility relative to the *asking member* (so the model never
describes a staff channel the asker cannot see), per-role member
counts, and a by-name member lookup. Bundling those into the snapshot
dataclass would widen its closed, privacy-pinned field set. Keeping
them here isolates the AI-facing read model from the advisor's.

Privacy
-------
Roles, channels, and the high-level overview are all visible to anyone
already in the server via the Discord client, so surfacing them to the
in-server asker discloses nothing new. Member *enumeration* and the
aggregate member count are treated as the sensitive tier: they are
emitted only when the caller passes ``include_members=True``, which the
tool layer gates behind an explicit opt-in feature flag (default off),
mirroring the "members excluded by default" stance documented in
:mod:`services.guild_snapshot`.

Every output is capped so one large guild cannot blow the model's
token budget. Read-only: never mutates Discord or the DB.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger("bot.services.guild_introspection")

# Output caps — large enough to be useful, small enough to stay within
# the model's prompt budget after the rest of the stack is assembled.
_ROLE_CAP = 60
_CHANNEL_CAP = 80
_MEMBER_MATCH_CAP = 10


def _iso_date(value: Any) -> str | None:
    """Return the date portion of a datetime-like value, or ``None``."""
    if not isinstance(value, datetime):
        return None
    return value.date().isoformat()


def _display_name(obj: Any) -> str:
    """Best-effort display name for a member/user-like object."""
    for attr in ("display_name", "name", "global_name"):
        val = getattr(obj, attr, None)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return "unknown"


def server_overview(guild: Any, *, include_members: bool = False) -> dict[str, Any]:
    """High-level summary of ``guild``.

    Channel / category / role counts, owner, creation date, and boost
    status are always included (all operator-visible). The aggregate
    ``member_count`` is included only when ``include_members`` is true.
    """
    text_channels = list(getattr(guild, "text_channels", ()) or ())
    voice_channels = list(getattr(guild, "voice_channels", ()) or ())
    categories = list(getattr(guild, "categories", ()) or ())
    roles = list(getattr(guild, "roles", ()) or ())

    owner = getattr(guild, "owner", None)
    overview: dict[str, Any] = {
        "name": getattr(guild, "name", None),
        "description": getattr(guild, "description", None) or None,
        "owner": _display_name(owner) if owner is not None else "unknown",
        "created": _iso_date(getattr(guild, "created_at", None)),
        "counts": {
            "text_channels": len(text_channels),
            "voice_channels": len(voice_channels),
            "categories": len(categories),
            # ``roles`` includes @everyone; report the human-facing total
            # (roles the operator actually created) by dropping it.
            "roles": max(0, len(roles) - 1),
        },
        "boost_level": getattr(guild, "premium_tier", None),
        "boost_count": getattr(guild, "premium_subscription_count", None),
    }
    if include_members:
        overview["member_count"] = getattr(guild, "member_count", None)
    return overview


def _role_permission_summary(role: Any) -> str:
    """Compact privilege label for a role (admin / manage / none)."""
    perms = getattr(role, "permissions", None)
    if perms is None:
        return "none"
    if getattr(perms, "administrator", False):
        return "administrator"
    elevated = [
        name
        for name in (
            "manage_guild",
            "manage_roles",
            "manage_channels",
            "ban_members",
            "kick_members",
            "manage_messages",
        )
        if getattr(perms, name, False)
    ]
    return ", ".join(elevated) if elevated else "none"


def list_roles(
    guild: Any,
    *,
    include_member_counts: bool = False,
    limit: int = _ROLE_CAP,
) -> dict[str, Any]:
    """List the guild's roles, highest first, with a privilege summary.

    Per-role member counts are emitted only when
    ``include_member_counts`` is true (the member-data opt-in tier).
    """
    roles = [
        r
        for r in (getattr(guild, "roles", ()) or ())
        if getattr(r, "name", "") != "@everyone"
    ]
    roles.sort(key=lambda r: getattr(r, "position", 0), reverse=True)
    truncated = len(roles) > limit
    out: list[dict[str, Any]] = []
    for role in roles[:limit]:
        entry: dict[str, Any] = {
            "name": getattr(role, "name", "?"),
            "privileges": _role_permission_summary(role),
            "hoisted": bool(getattr(role, "hoist", False)),
            "mentionable": bool(getattr(role, "mentionable", False)),
        }
        if include_member_counts:
            members = getattr(role, "members", None)
            entry["member_count"] = len(list(members)) if members is not None else None
        out.append(entry)
    return {"roles": out, "total": len(roles), "truncated": truncated}


def list_channels(
    guild: Any,
    member: Any = None,
    *,
    limit: int = _CHANNEL_CAP,
) -> dict[str, Any]:
    """List text/voice channels the ``member`` can view, grouped by category.

    When ``member`` is provided, channels they cannot view are omitted so
    the model never describes a channel hidden from the asker. When it is
    ``None`` (no member context), all channels are listed.
    """
    entries: list[dict[str, Any]] = []
    text_channels = list(getattr(guild, "text_channels", ()) or ())
    voice_channels = list(getattr(guild, "voice_channels", ()) or ())

    def _visible(channel: Any) -> bool:
        if member is None:
            return True
        perms_for = getattr(channel, "permissions_for", None)
        if perms_for is None:
            return True
        try:
            perms = perms_for(member)
        except Exception:  # noqa: BLE001 — defensive per-channel
            return False
        return bool(getattr(perms, "view_channel", False))

    for channel, kind in (
        *((c, "text") for c in text_channels),
        *((c, "voice") for c in voice_channels),
    ):
        if not _visible(channel):
            continue
        parent = getattr(channel, "category", None)
        entries.append(
            {
                "name": getattr(channel, "name", "?"),
                "type": kind,
                "category": (
                    getattr(parent, "name", None) if parent is not None else None
                ),
                "topic": (
                    (getattr(channel, "topic", None) or None)
                    if kind == "text"
                    else None
                ),
            },
        )
    truncated = len(entries) > limit
    return {"channels": entries[:limit], "total": len(entries), "truncated": truncated}


def lookup_member(guild: Any, query: str, *, requester: Any = None) -> dict[str, Any]:
    """Resolve members matching ``query`` (display name / username substring).

    Returns each match's display name, server join date, and role names —
    all visible to any server member via the Discord client. Caller is
    responsible for gating this behind the member-data opt-in. Matches are
    capped at :data:`_MEMBER_MATCH_CAP`.
    """
    needle = (query or "").strip().lower()
    if not needle:
        return {"found": False, "matches": [], "note": "empty query"}
    members = list(getattr(guild, "members", ()) or ())
    matches: list[dict[str, Any]] = []
    owner_id = getattr(guild, "owner_id", None)
    for member in members:
        names = [
            str(getattr(member, attr, "") or "").lower()
            for attr in ("display_name", "name", "global_name")
        ]
        if not any(needle in name for name in names if name):
            continue
        role_names = [
            getattr(r, "name", "")
            for r in (getattr(member, "roles", ()) or ())
            if getattr(r, "name", "") != "@everyone"
        ]
        matches.append(
            {
                "display_name": _display_name(member),
                "joined": _iso_date(getattr(member, "joined_at", None)),
                "is_bot": bool(getattr(member, "bot", False)),
                "is_owner": getattr(member, "id", None) == owner_id,
                "roles": role_names,
            },
        )
        if len(matches) >= _MEMBER_MATCH_CAP:
            break
    return {"found": bool(matches), "matches": matches}


__all__ = [
    "list_channels",
    "list_roles",
    "lookup_member",
    "server_overview",
]
