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
from typing import Any

import discord

from services.audit_events import emit_audit_action
from utils.role_feasibility import (
    ABOVE_BOT,
    BOT_MISSING_MANAGE_ROLES,
    EVERYONE,
    MANAGED,
    evaluate_role,
)

logger = logging.getLogger("bot.services.role_automation")


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoleThreshold:
    """One progression row: ``role_name`` requires ``days_required``.

    ``role_id`` (PR6 id-groundwork, migration 056) lets the engine resolve the
    tier id-first so a role rename never silently orphans it; ``None`` for legacy
    name-only rows, which fall back to normalized-name resolution.
    """

    role_name: str
    days_required: int
    role_id: int | None = None


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


# Reason codes for a classified per-member failure.  The manageability codes
# (BOT_MISSING_MANAGE_ROLES / ABOVE_BOT / MANAGED / EVERYONE) come from
# utils.role_feasibility so the pre-mutation guard, check_preflight, and the
# selector surfaces all classify "can't manage this role" identically; the rest
# are apply-specific outcomes.
MEMBER_NOT_CACHED = "member_not_cached"
FORBIDDEN = "forbidden"
NOT_FOUND = "not_found"
HTTP_ERROR = "http_error"
UNKNOWN = "unknown"

_FAILURE_LABELS: dict[str, str] = {
    BOT_MISSING_MANAGE_ROLES: "missing Manage Roles",
    ABOVE_BOT: "role above my top role",
    MANAGED: "integration-managed role",
    EVERYONE: "the @everyone role",
    MEMBER_NOT_CACHED: "member not in cache",
    FORBIDDEN: "permission denied",
    NOT_FOUND: "member or role not found",
    HTTP_ERROR: "Discord API error",
    UNKNOWN: "unexpected error",
}


@dataclass(frozen=True)
class ApplyError:
    """One classified per-member failure from :func:`apply`.

    ``code`` is a stable reason token (the :mod:`utils.role_feasibility` codes
    for manageability blockers, plus the apply-specific ones above) so operator
    and diagnostics surfaces can group failures by *cause* instead of parsing
    free text.  ``phase`` is where it happened: ``"lookup"`` (member not cached),
    ``"preflight"`` (a role the bot can't manage) or ``"mutate"`` (the Discord
    call raised).
    """

    member_id: int
    phase: str
    code: str
    detail: str


@dataclass(frozen=True)
class ApplyResult:
    """Outcome of :func:`apply`."""

    attempted: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    failures: tuple[ApplyError, ...] = ()

    @property
    def errors(self) -> tuple[str, ...]:
        """Back-compat human-readable failure strings (``failures`` is the
        structured form).
        """
        return tuple(f"member {f.member_id}: {f.detail}" for f in self.failures)

    def failure_counts(self) -> dict[str, int]:
        """``{reason_code: count}`` over :attr:`failures`, busiest cause first."""
        counts: dict[str, int] = {}
        for f in self.failures:
            counts[f.code] = counts.get(f.code, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def summarize_failures(result: ApplyResult) -> str:
    """Compact ``"missing Manage Roles: 26, role above my top role: 2"`` summary
    of a result's failures (busiest first), or ``""`` when there were none.
    """
    return ", ".join(
        f"{_FAILURE_LABELS.get(code, code)}: {n}"
        for code, n in result.failure_counts().items()
    )


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


def _resolve_threshold_role(guild: Any, threshold: RoleThreshold) -> Any | None:
    """Resolve a threshold to its current role — id-first, then normalized name.

    Iterating ``guild.roles`` (never ``guild.get_role``) keeps the cache-only
    contract and the no-raw-lookup invariant.  Id-first means a renamed role
    still resolves to the same tier; ``role_id=None`` (legacy rows) falls back to
    the name lookup, preserving the pre-PR6 behavior exactly.
    """
    rid = getattr(threshold, "role_id", None)
    if rid is not None:
        for role in getattr(guild, "roles", ()) or ():
            if getattr(role, "id", None) == rid:
                return role
    return _resolve_role(guild, threshold.role_name)


def compute_assignments(
    guild: Any,
    thresholds: list[RoleThreshold] | tuple[RoleThreshold, ...],
    *,
    exempt_role_ids: frozenset[int] = frozenset(),
    keep_previous_tier: bool = False,
    now: datetime | None = None,
) -> tuple[Assignment, ...]:
    """Walk ``guild.members`` and produce planned operations.

    Pure: no Discord API mutation, no DB writes. The result is what
    :func:`apply` would do if invoked with ``dry_run=False``.

    ``exempt_role_ids`` — members holding any of these roles are skipped
    entirely (the time-exempt set from ``role_automation_exemptions``).
    ``keep_previous_tier`` — when ``True`` the previously-earned tier
    roles are kept instead of being removed on promotion (the
    ``time_roles_stack`` toggle).
    """
    if now is None:
        now = datetime.now(tz=timezone.utc)
    if not thresholds:
        return ()

    # Resolve each tier to its CURRENT role id-first (name fallback), then key
    # the progression by the resolved current name.  This makes a renamed role
    # keep its tier (the id resolves, and member roles match on the current
    # name), while legacy name-only rows behave exactly as before.  Tiers whose
    # role no longer exists are dropped — they could never assign anything.
    resolved = [
        (role, t.days_required)
        for t in thresholds
        if (role := _resolve_threshold_role(guild, t)) is not None
    ]
    if not resolved:
        return ()
    role_map = {role.name: days for role, days in resolved}
    role_by_name = {role.name: role for role, _ in resolved}
    progression = sorted(role_map, key=lambda r: role_map[r])

    out: list[Assignment] = []
    for member in getattr(guild, "members", ()) or ():
        if getattr(member, "bot", False):
            continue
        if any(
            getattr(r, "id", None) in exempt_role_ids
            for r in getattr(member, "roles", ())
        ):
            continue
        joined_at = getattr(member, "joined_at", None)
        if joined_at is None:
            continue

        days = (now - joined_at).days

        target_name: str | None = None
        for name in progression:
            if days >= role_map[name]:
                target_name = name

        target_role = role_by_name.get(target_name) if target_name else None
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

        to_remove = (
            []
            if keep_previous_tier
            else [
                r
                for r in member_roles
                if any(_normalize(r.name) == _normalize(n) for n in role_map)
                and r != target_role
            ]
        )

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
    exempt_role_ids: frozenset[int] = frozenset(),
    keep_previous_tier: bool = False,
    now: datetime | None = None,
) -> Assignment | None:
    """Return the planned operation for one member, or ``None`` if
    no change is needed.
    """
    fake_guild = _SingleMemberGuild(guild, member)
    plans = compute_assignments(
        fake_guild,
        thresholds,
        exempt_role_ids=exempt_role_ids,
        keep_previous_tier=keep_previous_tier,
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


def _bot_has_manage_roles(me: Any) -> bool:
    """Whether ``guild.me`` carries the ``manage_roles`` permission.

    Shared by :func:`check_preflight` and :func:`apply` so the owner-facing
    report and the mutation guard can never disagree on the permission state.
    """
    return bool(
        getattr(getattr(me, "guild_permissions", None), "manage_roles", False),
    )


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
    bot_has_manage = _bot_has_manage_roles(me)
    bot_top_position = getattr(getattr(me, "top_role", None), "position", 0)

    missing: list[str] = []
    blockers: list[str] = []
    for t in thresholds:
        # Resolve id-first (mirrors compute_assignments / apply) so a renamed
        # role with a persisted role_id is NOT reported "missing" — the parity
        # the old name-only lookup silently broke.
        role = _resolve_threshold_role(guild, t)
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


def _classify_exception(exc: Exception) -> tuple[str, bool]:
    """Map a mutation exception to ``(reason_code, is_unexpected)``.

    Predictable Discord conditions — permission denied, gone member/role, a
    transient HTTP error — are *expected operational states*, not bot faults,
    so they return ``is_unexpected=False``: the caller logs them at WARNING and
    they stay out of the ERROR-only health surface.  Anything else is genuinely
    unexpected and is logged with a traceback at ERROR.
    """
    if isinstance(exc, discord.Forbidden):
        return FORBIDDEN, False
    if isinstance(exc, discord.NotFound):
        return NOT_FOUND, False
    if isinstance(exc, discord.HTTPException):
        return HTTP_ERROR, False
    return UNKNOWN, True


def _blocking_verdict(guild: Any, me: Any, plan: Assignment) -> ApplyError | None:
    """Classified :class:`ApplyError` if any role this plan touches is
    unmanageable by the bot, else ``None``.

    Delegates the per-role verdict to
    :func:`utils.role_feasibility.evaluate_role` — the single source of truth
    for "can the bot manage this role?" — so the pre-mutation guard,
    :func:`check_preflight`, and the selector surfaces can never drift.  With
    ``me`` unresolved (``guild.me is None``) the bot hierarchy / permission
    checks are skipped, so the mutation is attempted and any raise classified;
    we never assume a failure we cannot prove.
    """
    roles_by_id = {
        r.id: r for r in (getattr(guild, "roles", ()) or ()) if getattr(r, "id", None)
    }
    touched: list[Any] = []
    if plan.add_role_id is not None and plan.add_role_id in roles_by_id:
        touched.append(roles_by_id[plan.add_role_id])
    touched.extend(
        roles_by_id[rid] for rid in plan.remove_role_ids if rid in roles_by_id
    )
    for role in touched:
        verdict = evaluate_role(role, bot_member=me)
        if not verdict.ok:
            return ApplyError(
                member_id=plan.member_id,
                phase="preflight",
                code=verdict.code,
                detail=f"role '{verdict.role_name}': {verdict.reason}",
            )
    return None


async def apply(
    guild: Any,
    assignments: tuple[Assignment, ...] | list[Assignment],
    *,
    dry_run: bool = False,
    actor_id: int | None = None,
    actor_type: str = "system",
) -> ApplyResult:
    """Apply ``assignments`` to the live guild.

    Preflight-guarded at the mutation point: before any API call the bot's
    ability to manage each touched role is checked via
    :func:`utils.role_feasibility.evaluate_role`.  Predictable blockers — the
    bot missing ``manage_roles`` or a progression role sitting at/above the
    bot's top role — are recorded as classified :class:`ApplyError` failures and
    logged once for the batch, instead of letting every member raise a 403 and
    flood the ERROR log / health surface (the "26 role automation errors" shape).
    Each remaining member is still handled in isolation: an unexpected exception
    increments the failure counter but does NOT abort the batch and is logged
    with a traceback. Every successful change emits ``audit.action_recorded``
    via the Track 1 shared helper.
    """
    if dry_run:
        return ApplyResult(
            attempted=len(assignments),
            skipped=len(assignments),
        )

    me = getattr(guild, "me", None)
    guild_id = getattr(guild, "id", "?")

    # Systemic guard: if the bot demonstrably lacks Manage Roles, every
    # add/remove would 403 once per member.  Catch it once, skip the batch, and
    # return classified failures — no per-member ERROR tracebacks.
    if me is not None and not _bot_has_manage_roles(me):
        logger.warning(
            "role_automation.apply: skipping %d assignment(s) in guild=%s — "
            "bot lacks the Manage Roles permission.",
            len(assignments),
            guild_id,
        )
        return ApplyResult(
            attempted=len(assignments),
            failed=len(assignments),
            failures=tuple(
                ApplyError(
                    member_id=p.member_id,
                    phase="preflight",
                    code=BOT_MISSING_MANAGE_ROLES,
                    detail="bot lacks the Manage Roles permission",
                )
                for p in assignments
            ),
        )

    attempted = 0
    succeeded = 0
    preflight_blocked = 0
    failures: list[ApplyError] = []

    members_by_id = {m.id: m for m in (getattr(guild, "members", ()) or ())}

    for plan in assignments:
        attempted += 1
        member = members_by_id.get(plan.member_id)
        if member is None:
            failures.append(
                ApplyError(
                    member_id=plan.member_id,
                    phase="lookup",
                    code=MEMBER_NOT_CACHED,
                    detail="member not in guild cache",
                ),
            )
            continue

        blocked = _blocking_verdict(guild, me, plan)
        if blocked is not None:
            preflight_blocked += 1
            failures.append(blocked)
            continue

        try:
            await _apply_single(guild, member, plan, actor_id, actor_type)
            succeeded += 1
        except Exception as exc:  # noqa: BLE001 — per-member boundary
            code, unexpected = _classify_exception(exc)
            failures.append(
                ApplyError(
                    member_id=plan.member_id,
                    phase="mutate",
                    code=code,
                    detail=f"{type(exc).__name__}: {exc}",
                ),
            )
            if unexpected:
                logger.exception(
                    "role_automation.apply: failed for member=%d",
                    plan.member_id,
                )
            else:
                logger.warning(
                    "role_automation.apply: %s for member=%d: %s",
                    code,
                    plan.member_id,
                    exc,
                )

    # One WARNING for the whole batch of predictable, pre-empted blockers — keeps
    # a roster-wide misconfiguration out of the ERROR-only health surface while
    # still recording it (and the structured result drives the operator surface).
    if preflight_blocked:
        logger.warning(
            "role_automation.apply: skipped %d assignment(s) in guild=%s — "
            "unmanageable roles (%s).",
            preflight_blocked,
            guild_id,
            summarize_failures(ApplyResult(failures=tuple(failures))),
        )

    return ApplyResult(
        attempted=attempted,
        succeeded=succeeded,
        failed=len(failures),
        failures=tuple(failures),
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
    "ApplyError",
    "ApplyResult",
    "Assignment",
    "PreflightResult",
    "RoleThreshold",
    "apply",
    "check_preflight",
    "compute_assignments",
    "explain_assignment_for",
    "summarize_failures",
]
