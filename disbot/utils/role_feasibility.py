"""Pure role-feasibility evaluation shared by selectors, services, and diagnostics.

Answers two questions about a guild role as *structured findings* rather than
ad-hoc strings:

* **Is it a sensible selection target?** — :func:`not_everyone` (the default
  filter every role picker should use; ``@everyone`` is almost never a useful
  pick).
* **Can the bot (and optionally an acting member) manage it?** —
  :func:`evaluate_role` / :func:`manageable_roles`, yielding a reason code when
  not (hierarchy, missing permission, managed integration role, …).

This module is **pure**: no I/O and no service/cog/view imports (``utils`` may
import stdlib + ``discord`` only).  The manageability checks mirror the logic
already embedded in ``services.role_automation.check_preflight`` and
``services.resource_health._inspect_role`` — decomposed here so a single
source of truth can be reused by the shared selectors (PR2) and the role
lifecycle / assignment surfaces that follow, instead of each surface
re-deriving "can I touch this role?".
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

import discord

RoleFilter = Callable[[discord.Role], bool]

# ---------------------------------------------------------------------------
# Reason codes
# ---------------------------------------------------------------------------

SELECTABLE = "selectable"  # ok=True — nothing blocks managing this role
EVERYONE = "everyone"  # the @everyone / default role
MANAGED = "managed"  # integration / bot-managed (not operator-editable)
ABOVE_BOT = "above_bot"  # at or above the bot's highest role
BOT_MISSING_MANAGE_ROLES = "bot_missing_manage_roles"  # bot lacks Manage Roles
ABOVE_ACTOR = "above_actor"  # at or above the acting member's highest role

_REASONS: dict[str, str] = {
    EVERYONE: "the @everyone role can't be targeted",
    MANAGED: "managed by an integration — not operator-editable",
    ABOVE_BOT: "above my highest role — I can't manage it",
    BOT_MISSING_MANAGE_ROLES: "I lack the Manage Roles permission",
    ABOVE_ACTOR: "above your highest role",
}

# Short human labels for exclusion summaries (footers / embeds).
_SHORT: dict[str, str] = {
    EVERYONE: "@everyone",
    MANAGED: "managed",
    ABOVE_BOT: "above my top role",
    BOT_MISSING_MANAGE_ROLES: "missing Manage Roles",
    ABOVE_ACTOR: "above your top role",
}


@dataclass(frozen=True)
class RoleFeasibility:
    """Structured verdict for a single role."""

    role_id: int
    role_name: str
    ok: bool
    code: str
    reason: str


def _has_manage_roles(member: object) -> bool:
    perms = getattr(member, "guild_permissions", None)
    return bool(getattr(perms, "manage_roles", False))


def _position(obj: object) -> int:
    return int(getattr(obj, "position", 0) or 0)


def _at_or_above(role: object, other: object) -> bool:
    """True when ``role`` sits at or above ``other`` in Discord's role hierarchy
    (so a member/bot whose top role is ``other`` can **not** manage ``role``).

    Discord role ``position`` values are **not unique**: when two roles share a
    position, Discord — and discord.py's ``Role`` comparison — break the tie by
    **id**, ranking the older role (smaller id) higher.  Comparing raw
    ``position`` alone therefore mis-flags a role that merely *ties* the top
    role's position (roles created by the bot commonly all sit at position 1,
    yet the bot's managed role still outranks the ones it created).  This mirrors
    ``Role.__lt__``: ``role`` is strictly *below* ``other`` iff
    ``role.position < other.position`` or (equal position and ``role.id >
    other.id``); "at or above" is the negation.
    """
    rp, op = _position(role), _position(other)
    if rp != op:
        return rp > op
    # Equal position → tie broken by id (older/smaller id ranks higher).  With
    # ids absent (test fakes default to 0) this preserves the legacy ``>=``
    # behaviour (0 <= 0 → treated as at-or-above).
    rid = int(getattr(role, "id", 0) or 0)
    oid = int(getattr(other, "id", 0) or 0)
    return rid <= oid


def is_below(role: object, other: object) -> bool:
    """True when ``role`` is strictly *below* ``other`` in Discord's role
    hierarchy — i.e. a member/bot whose top role is ``other`` can manage ``role``
    (hierarchy-wise).  Inverse of :func:`_at_or_above`; uses the (position, id)
    tiebreak rather than raw ``position`` so tied positions are ranked correctly.
    """
    return not _at_or_above(role, other)


def _is_default(role: object) -> bool:
    is_default = getattr(role, "is_default", None)
    if callable(is_default):
        return bool(is_default())
    return bool(is_default)


def evaluate_role(
    role: discord.Role,
    *,
    bot_member: object | None = None,
    actor: object | None = None,
) -> RoleFeasibility:
    """Return a :class:`RoleFeasibility` for *role*.

    ``bot_member`` (``guild.me``) enables the bot-hierarchy / permission
    checks; ``actor`` enables the staff-hierarchy check for manual actions.
    With neither supplied, only the intrinsic checks (``@everyone``,
    ``managed``) can fail.  The first blocking reason in precedence order
    (@everyone → managed → bot permission → bot hierarchy → actor hierarchy)
    is reported.
    """
    rid = int(getattr(role, "id", 0) or 0)
    name = str(getattr(role, "name", "") or "")

    def _verdict(code: str) -> RoleFeasibility:
        ok = code == SELECTABLE
        reason = "" if ok else _REASONS.get(code, code)
        return RoleFeasibility(rid, name, ok, code, reason)

    if _is_default(role):
        return _verdict(EVERYONE)
    if bool(getattr(role, "managed", False)):
        return _verdict(MANAGED)
    if bot_member is not None:
        if not _has_manage_roles(bot_member):
            return _verdict(BOT_MISSING_MANAGE_ROLES)
        bot_top = getattr(bot_member, "top_role", None)
        if bot_top is not None and _at_or_above(role, bot_top):
            return _verdict(ABOVE_BOT)
    if actor is not None:
        actor_top = getattr(actor, "top_role", None)
        if actor_top is not None and _at_or_above(role, actor_top):
            return _verdict(ABOVE_ACTOR)
    return _verdict(SELECTABLE)


def manageable_roles(
    roles: Iterable[discord.Role],
    *,
    bot_member: object,
    actor: object | None = None,
) -> tuple[list[discord.Role], list[RoleFeasibility]]:
    """Partition *roles* into ``(manageable, excluded)``.

    ``manageable`` is the roles the bot (and ``actor`` if given) can act on;
    ``excluded`` is a :class:`RoleFeasibility` per skipped role carrying the
    reason.  Intended for assignment / lifecycle surfaces that must only offer
    roles they can actually mutate.
    """
    manageable: list[discord.Role] = []
    excluded: list[RoleFeasibility] = []
    for role in roles:
        verdict = evaluate_role(role, bot_member=bot_member, actor=actor)
        if verdict.ok:
            manageable.append(role)
        else:
            excluded.append(verdict)
    return manageable, excluded


def not_everyone(role: discord.Role) -> bool:
    """Default role-picker filter: keep everything except ``@everyone``.

    Shared so every selector agrees on what a "targetable" role is.
    """
    return not _is_default(role)


def summarize_exclusions(excluded: Iterable[RoleFeasibility]) -> str:
    """Render a compact "N hidden: …" summary for a footer / embed line.

    Returns an empty string when nothing was excluded.
    """
    items = list(excluded)
    if not items:
        return ""
    counts: dict[str, int] = {}
    for f in items:
        counts[f.code] = counts.get(f.code, 0) + 1
    parts = [f"{n} {_SHORT.get(code, code)}" for code, n in counts.items()]
    return f"{len(items)} hidden: " + ", ".join(parts)


__all__ = [
    "ABOVE_ACTOR",
    "ABOVE_BOT",
    "BOT_MISSING_MANAGE_ROLES",
    "EVERYONE",
    "MANAGED",
    "SELECTABLE",
    "RoleFeasibility",
    "RoleFilter",
    "evaluate_role",
    "is_below",
    "manageable_roles",
    "not_everyone",
    "summarize_exclusions",
]
