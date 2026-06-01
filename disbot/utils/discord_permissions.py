"""Synchronous Discord permission predicates (execution authorization).

These are *authorization* helpers — "may this member perform this action" —
and are deliberately kept separate from ``utils/visibility_rules.py``, which
governs UI/help *discoverability* only. Conflating the two is an explicit
anti-pattern called out in that module's docstring.

Promoted from three byte-for-byte-identical ``_is_staff`` copies in
``views/btd6/panel.py``, ``views/btd6/strategy_review.py`` and
``services/btd6_strategy_mutation.py`` (see ``docs/helper-policy.md``: a
predicate needed by both ``services/`` and ``views/`` belongs in ``utils/``).

Pure ``getattr`` checks on ``member.guild_permissions`` — no DB, no async,
no Discord API calls. Accept ``Any`` because callers pass either a
``discord.Member`` or a ``discord.User`` (DMs have no ``guild_permissions``),
and both must degrade to ``False`` rather than raise.
"""

from __future__ import annotations

from typing import Any


def is_staff_member(member: Any) -> bool:
    """Return ``True`` if ``member`` is staff (administrator OR manage_guild).

    Mirrors the ``staff`` visibility tier's Discord permission, but as an
    *authorization* gate. Returns ``False`` for objects without
    ``guild_permissions`` (e.g. a ``discord.User`` in a DM context).
    """
    perms = getattr(member, "guild_permissions", None)
    if perms is None:
        return False
    return bool(
        getattr(perms, "administrator", False) or getattr(perms, "manage_guild", False),
    )


def is_administrator_member(member: Any) -> bool:
    """Return ``True`` only if ``member`` has the administrator permission.

    Stricter than :func:`is_staff_member`. Used to gate live-ingestion
    source mutations, matching ``services.btd6_source_mutation._check_admin``
    so the UI gate and the mutation service agree on who may toggle sources.
    """
    perms = getattr(member, "guild_permissions", None)
    if perms is None:
        return False
    return bool(getattr(perms, "administrator", False))


__all__ = ["is_administrator_member", "is_staff_member"]
