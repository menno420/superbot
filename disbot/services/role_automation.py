"""Role-automation decision logic — Phase 9h / Track 7 PR 20.

Pure-read decision module extracted from :mod:`disbot.cogs.role_cog`.
Owns the time-based / threshold-based role progression logic:

* :func:`compute_assignments` — pure: given the guild's threshold
  table + the live member roster, return the planned add / remove
  operations.
* :func:`explain_assignment_for` — single-member reasoning for the
  ``!roles explain`` operator surface and the wizard's
  drill-down view.
* :func:`check_preflight` — owner-facing safety check: confirms the
  bot has ``manage_roles`` and that the configured progression
  roles are below the bot's top role.
* :func:`apply` — perform the actual ``add_roles`` /
  ``remove_roles`` calls. Wrapped per-member in try/except so one
  hierarchy-blocked role does not abort the whole batch. Emits
  ``audit.action_recorded`` via the Track 1 shared helper for
  every successful change.

Tests pin:

* Dry-run produces no mutations.
* ``explain_assignment_for`` returns deterministic reasoning.
* Hierarchy preflight catches a progression role above the bot's
  top role.
* Permission preflight catches a missing ``manage_roles``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from services.audit_events import emit_audit_action

if TYPE_CHECKING:
    pass

logger = logging.getLogger("bot.services.role_automation")


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoleThreshold:
    """One progression row: ``role_name`` requires ``days_required``."""

    role_name: str
    days_required: int


@dataclass(frozen=True)
class Assignment:
    """One planned (member, add/remove) operation."""

    member_id: int
    member_display: str
    add_role_id: int | None
    add_role_name: str | None
    remove_role_ids: tuple[int, ...]
    remove_role_names: tuple[str, ...]
    reason: str  # human-readable explanation
    days_in_guild: int


@dataclass(frozen=True)
class PreflightResult:
    """Outcome of :func:`check_preflight`."""

    bot_has_manage_roles: bool
    hierarchy_blockers: tuple[str, ...] = ()
    missing_roles: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return (
            self.bot_has_manage_roles
            and not self.hierarchy_blockers
            and not self.missing_roles
        )


@dataclass(frozen=True)
class ApplyResult:
    """Outcome of :func:`apply`."""

    attempted: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    errors: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Pure decision logic
# ---------------------------------------------------------------------------


def _normalize(name: str | None) -> str:
    return (name or "").strip().lower()


def _resolve_role(guild: Any, name: str) -> Any | None:
    """Cache-only normalised role lookup."""
    norm = _normalize(name)
    for role in getattr(guild, "roles", ()) or ():
        if _normalize(role.name) == norm:
            return role
    return None


def compute_assignments(
    guild: Any,
    thresholds: list[RoleThreshold] | tuple[RoleThreshold, ...],
    *,
    skip_role_names: tuple[str, ...] = (),
    now: datetime | None = None,
) -> tuple[Assignment, ...]:
    """Walk ``guild.members`` and produce planned operations.

    Pure: no Discord API mutation, no DB writes. The result is what
    :func:`apply` would do if invoked with ``dry_run=False``.
    """
    if now is None:
        now = datetime.now(tz=timezone.utc)
    if not thresholds:
        return ()

    role_map = {t.role_name: t.days_required for t in thresholds}
    progression = sorted(role_map, key=lambda r: role_map[r])

    skip_roles = tuple(
        r for n in skip_role_names if (r := _resolve_role(guild, n)) is not None
    )

    out: list[Assignment] = []
    for member in getattr(guild, "members", ()) or ():
        if getattr(member, "bot", False):
            continue
        if any(role in getattr(member, "roles", ()) for role in skip_roles):
            continue
        joined_at = getattr(member, "joined_at", None)
        if joined_at is None:
            continue

        days = (now - joined_at).days

        target_name: str | None = None
        for name in progression:
            if days >= role_map[name]:
                target_name = name

        target_role = _resolve_role(guild, target_name) if target_name else None
        member_roles = list(getattr(member, "roles", ()) or ())

        # Walk through member's existing roles, find any that belong
        # to the progression — to figure out the operator's "current
        # tier" and avoid demotions.
        current_highest: str | None = None
        for role in member_roles:
            matched = next(
                (n for n in role_map if _normalize(n) == _normalize(role.name)),
                None,
            )
            if matched is not None:
                if current_highest is None or progression.index(
                    matched,
                ) > progression.index(current_highest):
                    current_highest = matched

        if (
            current_highest
            and target_name
            and progression.index(current_highest) > progression.index(target_name)
        ):
            continue  # never demote

        to_remove = [
            r
            for r in member_roles
            if any(_normalize(r.name) == _normalize(n) for n in role_map)
            and r != target_role
        ]

        add_role_id = target_role.id if target_role else None
        add_role_name = target_role.name if target_role else None
        already_assigned = target_role in member_roles if target_role else False

        if not to_remove and already_assigned:
            continue  # no-op

        if target_role and not already_assigned and not to_remove:
            reason = (
                f"{member.display_name} has {days} day(s) in guild; "
                f"earns role '{target_role.name}'."
            )
        elif to_remove and target_role and not already_assigned:
            reason = (
                f"{member.display_name} has {days} day(s); promote to "
                f"'{target_role.name}', remove "
                f"{[r.name for r in to_remove]}."
            )
        elif to_remove and not target_role:
            reason = (
                f"{member.display_name} no longer earns any progression "
                f"role at {days} day(s); remove "
                f"{[r.name for r in to_remove]}."
            )
        else:
            reason = "no-op"

        out.append(
            Assignment(
                member_id=member.id,
                member_display=getattr(
                    member,
                    "display_name",
                    str(member.id),
                ),
                add_role_id=add_role_id if not already_assigned else None,
                add_role_name=add_role_name if not already_assigned else None,
                remove_role_ids=tuple(r.id for r in to_remove),
                remove_role_names=tuple(r.name for r in to_remove),
                reason=reason,
                days_in_guild=days,
            ),
        )

    return tuple(out)


def explain_assignment_for(
    guild: Any,
    member: Any,
    thresholds: list[RoleThreshold] | tuple[RoleThreshold, ...],
    *,
    skip_role_names: tuple[str, ...] = (),
    now: datetime | None = None,
) -> Assignment | None:
    """Return the planned operation for one member, or ``None`` if
    no change is needed.
    """
    fake_guild = _SingleMemberGuild(guild, member)
    plans = compute_assignments(
        fake_guild,
        thresholds,
        skip_role_names=skip_role_names,
        now=now,
    )
    return plans[0] if plans else None


class _SingleMemberGuild:
    """Tiny adapter that exposes one member as ``guild.members``."""

    def __init__(self, guild: Any, member: Any) -> None:
        self._guild = guild
        self._member = member

    @property
    def roles(self):
        return getattr(self._guild, "roles", ()) or ()

    @property
    def members(self):
        return (self._member,)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._guild, name)


# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------


def check_preflight(
    guild: Any,
    thresholds: list[RoleThreshold] | tuple[RoleThreshold, ...],
) -> PreflightResult:
    """Permission + hierarchy + missing-role check.

    Returns a :class:`PreflightResult` whose ``ok`` is True iff:

    * The bot has ``manage_roles``.
    * Every progression role exists in the guild.
    * Every progression role's position is below the bot's top role.
    """
    me = getattr(guild, "me", None)
    if me is None:
        return PreflightResult(
            bot_has_manage_roles=False,
            missing_roles=tuple(t.role_name for t in thresholds),
        )
    bot_has_manage = bool(
        getattr(
            getattr(me, "guild_permissions", None),
            "manage_roles",
            False,
        ),
    )
    bot_top_position = getattr(
        getattr(me, "top_role", None),
        "position",
        0,
    )

    missing: list[str] = []
    blockers: list[str] = []
    for t in thresholds:
        role = _resolve_role(guild, t.role_name)
        if role is None:
            missing.append(t.role_name)
            continue
        if getattr(role, "position", 0) >= bot_top_position:
            blockers.append(t.role_name)

    return PreflightResult(
        bot_has_manage_roles=bot_has_manage,
        hierarchy_blockers=tuple(blockers),
        missing_roles=tuple(missing),
    )


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


async def apply(
    guild: Any,
    assignments: tuple[Assignment, ...] | list[Assignment],
    *,
    dry_run: bool = False,
    actor_id: int | None = None,
    actor_type: str = "system",
) -> ApplyResult:
    """Apply ``assignments`` to the live guild.

    Each member is handled in isolation: an exception on one
    ``add_roles`` / ``remove_roles`` call increments the failure
    counter but does NOT abort subsequent members. Every successful
    change emits a ``audit.action_recorded`` event via the Track 1
    shared helper.
    """
    if dry_run:
        return ApplyResult(
            attempted=len(assignments),
            skipped=len(assignments),
        )

    attempted = 0
    succeeded = 0
    failed = 0
    errors: list[str] = []

    members_by_id = {m.id: m for m in (getattr(guild, "members", ()) or ())}

    for plan in assignments:
        attempted += 1
        member = members_by_id.get(plan.member_id)
        if member is None:
            failed += 1
            errors.append(f"member {plan.member_id} not in cache")
            continue
        try:
            await _apply_single(guild, member, plan, actor_id, actor_type)
            succeeded += 1
        except Exception as exc:  # noqa: BLE001 — per-member boundary
            logger.exception(
                "role_automation.apply: failed for member=%d",
                plan.member_id,
            )
            failed += 1
            errors.append(
                f"member {plan.member_id}: {type(exc).__name__}: {exc}",
            )

    return ApplyResult(
        attempted=attempted,
        succeeded=succeeded,
        failed=failed,
        errors=tuple(errors),
    )


async def _apply_single(
    guild: Any,
    member: Any,
    plan: Assignment,
    actor_id: int | None,
    actor_type: str,
) -> None:
    """Per-member work. Wrapped in try/except by :func:`apply`."""
    occurred_at = datetime.now(tz=timezone.utc)

    if plan.remove_role_ids:
        roles_to_remove = [
            r for r in getattr(guild, "roles", ()) or () if r.id in plan.remove_role_ids
        ]
        if roles_to_remove:
            await member.remove_roles(
                *roles_to_remove,
                reason="role_automation:demote",
            )
            await emit_audit_action(
                mutation_id=f"role_automation:{member.id}:{occurred_at.timestamp()}",
                subsystem="role_automation",
                mutation_type="remove_role",
                target=f"member:{member.id}",
                scope="guild",
                guild_id=guild.id,
                prev_value=",".join(plan.remove_role_names),
                new_value=None,
                actor_id=actor_id,
                actor_type=actor_type,
                occurred_at=occurred_at,
            )

    if plan.add_role_id is not None:
        target = next(
            (r for r in getattr(guild, "roles", ()) or () if r.id == plan.add_role_id),
            None,
        )
        if target is not None:
            await member.add_roles(
                target,
                reason="role_automation:promote",
            )
            await emit_audit_action(
                mutation_id=f"role_automation:{member.id}:{occurred_at.timestamp()}",
                subsystem="role_automation",
                mutation_type="assign_role",
                target=f"member:{member.id}",
                scope="guild",
                guild_id=guild.id,
                prev_value=None,
                new_value=plan.add_role_name,
                actor_id=actor_id,
                actor_type=actor_type,
                occurred_at=occurred_at,
            )


__all__ = [
    "ApplyResult",
    "Assignment",
    "PreflightResult",
    "RoleThreshold",
    "apply",
    "check_preflight",
    "compute_assignments",
    "explain_assignment_for",
]
