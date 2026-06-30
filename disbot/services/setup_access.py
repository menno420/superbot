"""Setup-wizard access checks — Phase 9e / Track 4 PR 8.

Read-only helpers that answer "who can do X in the setup wizard?".
Replaces the inline ``actor_id == guild.owner_id`` checks scattered
across Track 2 PR 6's :mod:`services.readiness_repair` with a single
typed surface.

Roles
-----
* **Server owner** — ``member.id == guild.owner_id``. Sees everything,
  can apply destructive (create/delete) actions.
* **Setup admin** — administrator-tier member OR a delegated_admin
  listed in the guild's :class:`SetupSession.delegated_admins`. Can
  run the readiness scan and view findings, but cannot apply
  owner-gated repairs.
* **Anyone else** — denied at the launcher.

The helpers accept either a :class:`discord.Member` (typical UI
path) or a raw ``(user_id, guild_owner_id, delegated_admins)`` tuple
(typical from setup-launcher button callbacks that don't have the
full member object yet). The two entry points are explicit so the
caller does not silently degrade authorisation.

These functions are synchronous and cache-only — no DB or Discord
API calls — so they are safe to call from any view callback. The
caller already holds the :class:`SetupSession` snapshot for the
``delegated_admins`` list.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from config import is_platform_owner

if TYPE_CHECKING:
    import discord

    from services.setup_session import SetupSession

logger = logging.getLogger("bot.services.setup_access")


def is_server_owner(member: discord.Member) -> bool:
    """True iff ``member`` is the guild owner."""
    guild = getattr(member, "guild", None)
    if guild is None:
        return False
    return member.id == guild.owner_id


def is_administrator(member: discord.Member) -> bool:
    """True iff ``member`` has the Discord Administrator permission."""
    perms = getattr(member, "guild_permissions", None)
    if perms is None:
        return False
    return bool(getattr(perms, "administrator", False))


def is_setup_admin(
    member: discord.Member,
    session: SetupSession | None = None,
) -> bool:
    """True iff ``member`` is owner, administrator, or delegated admin.

    A ``None`` session means no row exists yet (e.g. the bot was
    only just invited); we still grant access to owners and
    administrators since they would be the ones to start the session.

    The configured **platform owner** (``config.BOT_OWNER_USER_ID``) always
    qualifies, so the bot owner can run setup in any guild even without
    Discord permissions there.
    """
    if is_platform_owner(getattr(member, "id", None)):
        return True
    if is_server_owner(member):
        return True
    if is_administrator(member):
        return True
    return bool(session is not None and member.id in session.delegated_admins)


def can_view_setup(
    member: discord.Member,
    session: SetupSession | None = None,
) -> bool:
    """True iff ``member`` may *see* the setup launcher / readiness."""
    return is_setup_admin(member, session)


def can_run_readiness(
    member: discord.Member,
    session: SetupSession | None = None,
) -> bool:
    """True iff ``member`` may run a readiness scan.

    Same gate as :func:`can_view_setup` for now — split out so future
    flag-based gating (e.g. "trusted contributors can run a scan but
    not see the full report") only touches one helper.
    """
    return is_setup_admin(member, session)


def can_apply_setup(
    member: discord.Member,
    session: SetupSession | None = None,
) -> bool:
    """True iff ``member`` may APPLY setup repairs / wizard steps.

    Tighter than :func:`is_setup_admin`: only owners and
    delegated admins. Administrators with no delegation get read-only
    access — they can still run the readiness scan but the wizard
    refuses to write on their behalf so the owner stays in control
    of capability-significant changes.

    The configured **platform owner** (``config.BOT_OWNER_USER_ID``) always
    qualifies, so the bot owner can apply setup in any guild.
    """
    if is_platform_owner(getattr(member, "id", None)):
        return True
    if is_server_owner(member):
        return True
    return bool(session is not None and member.id in session.delegated_admins)


# ---------------------------------------------------------------------------
# Raw-id variants — for callers that hold an actor_id but not a Member.
# ---------------------------------------------------------------------------


def is_server_owner_by_id(user_id: int, guild_owner_id: int) -> bool:
    return user_id == guild_owner_id


def can_apply_setup_by_id(
    user_id: int,
    guild_owner_id: int,
    delegated_admins: tuple[int, ...] = (),
) -> bool:
    """Variant of :func:`can_apply_setup` that takes raw ids.

    Used by :mod:`services.readiness_repair` (Track 2 PR 6) which
    accepts an ``actor_id`` without resolving the Member object. The
    semantics match :func:`can_apply_setup` exactly: platform owner OR
    server owner OR delegated admin.
    """
    if is_platform_owner(user_id):
        return True
    if user_id == guild_owner_id:
        return True
    return user_id in delegated_admins


__all__ = [
    "can_apply_setup",
    "can_apply_setup_by_id",
    "can_run_readiness",
    "can_view_setup",
    "is_administrator",
    "is_server_owner",
    "is_server_owner_by_id",
    "is_setup_admin",
]
