"""Role-automation exemptions + stacking-toggle access (read + write).

The read side composes the cached exemption rows
(:func:`utils.guild_config_accessors.get_role_exemptions`) into role-id
sets and resolves the two stacking toggles, so the XP listener and the
time-based engine share a single interpretation. The write side is the
only sanctioned path for mutating exemptions: it persists, invalidates
the cache, and emits an ``audit.action_recorded`` event.

Cycle discipline: cross-package imports of ``services.*`` are
function-local (mirrors the rest of ``services``); top-level imports are
limited to stdlib + ``utils`` (which this layer may depend on).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from utils import db
from utils import guild_config_accessors as gca


@dataclass(frozen=True)
class ExemptRoleIds:
    """Role ids exempted from each automation engine for one guild."""

    xp: frozenset[int]
    time: frozenset[int]


async def get_exempt_role_ids(guild_id: int) -> ExemptRoleIds:
    """Return the ``(xp, time)`` exempt role-id sets for ``guild_id`` (cached)."""
    rows = await gca.get_role_exemptions(guild_id)
    return ExemptRoleIds(
        xp=frozenset(int(r["role_id"]) for r in rows if r["exempt_xp"]),
        time=frozenset(int(r["role_id"]) for r in rows if r["exempt_time"]),
    )


async def time_roles_stack(guild_id: int) -> bool:
    """Whether tenure roles stack (keep the previous tier) for ``guild_id``."""
    from services.settings_resolution import resolve_value

    return bool(await resolve_value(guild_id, "role", "time_roles_stack", False))


async def xp_roles_stack(guild_id: int) -> bool:
    """Whether XP/level roles stack (keep lower roles) for ``guild_id``."""
    from services.settings_resolution import resolve_value

    return bool(await resolve_value(guild_id, "role", "xp_roles_stack", True))


def _flags_for(rows: list[dict], role_id: int) -> tuple[bool, bool]:
    for row in rows:
        if int(row["role_id"]) == role_id:
            return bool(row["exempt_xp"]), bool(row["exempt_time"])
    return False, False


async def set_exemption(
    guild_id: int,
    role_id: int,
    *,
    exempt_xp: bool,
    exempt_time: bool,
    actor_id: int | None,
) -> None:
    """Persist a role's exemption flags (audited + cache-invalidated).

    A row with neither flag set is deleted rather than stored, so the
    table only ever lists roles that are exempt from something.
    """
    rows = await db.get_role_exemptions(guild_id)
    prev_xp, prev_time = _flags_for(rows, role_id)

    if not exempt_xp and not exempt_time:
        await db.clear_role_exemption(guild_id, role_id)
    else:
        await db.set_role_exemption(
            guild_id,
            role_id,
            exempt_xp=exempt_xp,
            exempt_time=exempt_time,
        )

    gca.invalidate_role_exemptions(guild_id)

    from services.audit_events import emit_audit_action

    await emit_audit_action(
        mutation_id=str(uuid.uuid4()),
        subsystem="role",
        mutation_type="set_role_exemption",
        target=f"role:{role_id}",
        scope="guild",
        guild_id=guild_id,
        prev_value=f"xp={prev_xp},time={prev_time}",
        new_value=f"xp={exempt_xp},time={exempt_time}",
        actor_id=actor_id,
        actor_type="admin",
        occurred_at=datetime.now(tz=timezone.utc),
    )


__all__ = [
    "ExemptRoleIds",
    "get_exempt_role_ids",
    "set_exemption",
    "time_roles_stack",
    "xp_roles_stack",
]
