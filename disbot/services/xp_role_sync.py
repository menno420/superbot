"""Shared XP level-role planning.

The rule that turns "member is now level N" into a concrete role add/remove
set — the configured threshold list, stacking vs. single-role mode, and the
XP-exempt roles — lived inline in ``cogs/xp/listener``.  It is now one pure
planner shared by:

* the **live** level-up path (``cogs.xp.listener._apply_xp_threshold_roles``),
* the **bot-to-bot migration** (``services.xp_migration``), so an imported
  member is granted exactly the level roles they would have earned live.

Keeping one planner is the point: two copies of the stack/exempt logic would
drift.  The planner is pure (no DB, no ``await``) — the caller fetches the
guild's threshold list / stack flag / exempt set once and passes them in, so a
batch import can plan every member off a single set of reads and apply them in
one :func:`services.role_automation.apply` call.
"""

from __future__ import annotations

from typing import Any

from core.runtime import resources
from services.role_automation import Assignment


def plan_level_role_assignments(
    guild: Any,
    member: Any,
    new_level: int,
    *,
    stack: bool,
    exempt_xp_ids: frozenset[int],
    xp_roles: list[dict],
    reason: str,
) -> list[Assignment]:
    """Return the role assignments that bring *member* to *new_level*.

    Returns ``[]`` when the member holds an XP-exempt role, when nothing is
    configured/resolvable, or when the member already holds the correct roles.

    * **Stacking mode** — one promote assignment per newly-earned role
      (``level_required <= new_level``) the member does not already hold.
    * **Single-role mode** — keep only the highest earned tier: one assignment
      carrying the promote to the top qualifying role plus demotions of every
      other configured tier the member currently holds.

    Role resolution is id-first with a normalized-name fallback (migration
    056), so a renamed role keeps its tier.
    """
    member_role_ids = {r.id for r in getattr(member, "roles", ())}
    if member_role_ids & exempt_xp_ids:
        return []

    qualifying: list = []  # earned roles (level_required <= new_level)
    configured: list = []  # every configured XP role that resolves
    for role_cfg in xp_roles:
        discord_role = resources.resolve_role(
            guild,
            role_id=role_cfg.get("role_id"),
            name=role_cfg["role_name"],
        )
        if discord_role is None:
            continue
        configured.append(discord_role)
        if role_cfg["level_required"] <= new_level:
            qualifying.append(discord_role)
    if not qualifying:
        return []

    member_roles = member.roles
    member_display = getattr(member, "display_name", str(getattr(member, "id", "?")))
    assignments: list[Assignment] = []

    if stack:
        for r in (role for role in qualifying if role not in member_roles):
            assignments.append(
                Assignment(
                    member_id=member.id,
                    member_display=member_display,
                    add_role_id=r.id,
                    add_role_name=r.name,
                    remove_role_ids=(),
                    remove_role_names=(),
                    reason=reason,
                    days_in_guild=0,
                ),
            )
    else:
        # Single-role mode: keep only the highest earned level role
        # (xp_roles is ordered by level_required ascending).
        target = qualifying[-1]
        add = None if target in member_roles else target
        to_remove = [r for r in configured if r != target and r in member_roles]
        if add is not None or to_remove:
            assignments.append(
                Assignment(
                    member_id=member.id,
                    member_display=member_display,
                    add_role_id=add.id if add is not None else None,
                    add_role_name=add.name if add is not None else None,
                    remove_role_ids=tuple(r.id for r in to_remove),
                    remove_role_names=tuple(r.name for r in to_remove),
                    reason=reason,
                    days_in_guild=0,
                ),
            )

    return assignments
