"""Access Map projection — side-effect-free composed read model (P1A).

Phase 1 of the Adaptive Setup/Access platform
(`docs/planning/adaptive-setup-access-routine-platform-2026-06-08.md` §16). For a
``(feature, context)`` pair this answers **"is this allowed here, and if not,
why?"** by *composing the existing policy owners in a fixed precedence*. It owns
**no policy of its own** — there is no second permission system; every
``allow``/``deny`` traces to an existing owner, recorded in ``source_chain``.

**Read-only.** The projection calls async resolvers that *read* DB policy, but it
performs **no writes** and imports **no** mutation service or Discord resource
API. It computes on demand and does **not** persist (§16.6); a cache may be added
later only with an explicit invalidation owner.

**Axes (precedence order; short-circuits on the first ``deny``):**

======  =================  ===============================================
 axis    name               existing owner it delegates to
======  =================  ===============================================
 1+2     command access     ``core.runtime.command_access.resolve_command_access``
                            (lifecycle drain · DM · bootstrap bypass · channel
                            admission — the ``DecisionSource`` distinguishes them)
 3       cog routing        ``services.command_routing.is_cog_enabled``
 4       governance         ``governance.get_visible_subsystems`` (visibility +
                            member tier — the same read the access explorer uses)
 5       availability       FUTURE central resolver (§6.6) — not built; ``skipped``
 6       help visibility    ``core.runtime.command_surface_ledger`` — *informational
                            only*; never flips an execution ``allow`` to ``deny``
 7       user preference    FUTURE (Phase 5) — can hide/sort, never grants
======  =================  ===============================================

The reason vocabulary **reuses** ``command_access.DecisionReason`` /
``DecisionSource`` for the command-access axis rather than forking a parallel
enum; the routing/governance/availability axes add the small stable set in
:data:`_SAFE_TEXT`.

Cycle discipline (mirrors :mod:`services.customization_catalogue`): every
cross-package import is **function-local**; top-level imports are stdlib only.
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass
from typing import Any, Literal

logger = logging.getLogger("bot.services.access_projection")

_PROJECTION_VERSION = 1


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class AccessAxis(enum.Enum):
    """The composed policy axes, in evaluation order."""

    COMMAND_ACCESS = "command_access"  # axes 1+2 (lifecycle/DM/bootstrap/channel)
    ROUTING = "routing"  # axis 3
    GOVERNANCE = "governance"  # axis 4 (visibility + tier)
    AVAILABILITY = "availability"  # axis 5 (future — stubbed)
    HELP = "help"  # axis 6 (informational, non-gating)
    PREFERENCE = "preference"  # axis 7 (future — never grants)


# An axis result. ``allow``/``deny`` gate the effective decision (for axes 1-5);
# ``unknown`` means the owner could not resolve (does not gate, but blocks a
# confident ``allow``); ``skipped`` is a deliberately-not-evaluated axis (future
# axis, or no representative command) and never affects the result; ``shown`` /
# ``hidden`` are the help axis's non-gating states.
AxisState = Literal["allow", "deny", "unknown", "skipped", "shown", "hidden"]

# The effective access result for a feature.
Effective = Literal["allow", "deny", "unknown"]


@dataclass(frozen=True)
class LockedReason:
    """A structured, *user-safe* explanation of a denial (§6.3 / §16.3).

    ``safe_text`` is renderable to any audience and **never** leaks a role
    name, channel id, or policy internal — it is drawn from the static
    :data:`_SAFE_TEXT` table, not interpolated from context.
    """

    code: str
    safe_text: str
    source: str
    unlock_hint: str | None = None


@dataclass(frozen=True)
class AxisOutcome:
    """One axis's contribution to the decision chain.

    ``detail`` is an *internal* diagnostic string (it may name the source/mode)
    and is **not** rendered to users — only :attr:`LockedReason.safe_text` is.
    """

    axis: AccessAxis
    state: AxisState
    reason_code: str | None = None
    detail: str | None = None


@dataclass(frozen=True)
class AccessDecision:
    """The composed effective access for one feature in one context."""

    feature: str  # subsystem key (snake_case) — the unit of the read model
    command_name: str | None  # the representative entry_point evaluated, if any
    effective: Effective
    deciding_axis: AccessAxis | None  # axis that produced a deny, else None
    reason: LockedReason | None  # populated on deny
    source_chain: tuple[AxisOutcome, ...]  # every axis evaluated, in order
    remediation: str | None = None  # safe pointer to the owning surface


@dataclass(frozen=True)
class FeatureEntry:
    """One row of the feature inventory (registry + ledger)."""

    subsystem: str
    command_name: str | None  # representative entry_point (first declared)
    visibility_tier: str | None


@dataclass(frozen=True)
class AccessContext:
    """Explicit, fully-specified input to the projection (no implicit globals).

    Superset of ``command_access.CommandAccessContext`` plus the governance
    inputs (``member`` / ``member_role_ids``) and the channel/category scope the
    routing axis needs. Building one performs no I/O; the resolvers it is passed
    to do their own (read-only) lookups.

    ``member_tier`` is the **audience-simulation input** (Q-0045, option b):
    when set, the governance axis evaluates as that declared tier — with or
    without a real ``member`` — because governance's own tier resolution
    prefers a declared tier verbatim. Simulated contexts must label their
    limits (§16.4): a declared tier cannot model live Discord
    channel-permission overrides the simulation was not given.
    """

    guild_id: int | None
    channel_id: int | None = None
    category_id: int | None = None
    user_id: int | None = None
    member: Any | None = None  # discord.Member — governance/capability axis
    member_role_ids: tuple[int, ...] = ()
    member_tier: str | None = None
    is_guild_operator: bool = False
    is_bot_owner: bool = False
    is_dm: bool = False
    invocation_type: str = "prefix"  # "prefix" | "slash"
    # Reserved for the future availability axis (§6.6); unused today.
    now: Any | None = None


# ---------------------------------------------------------------------------
# User-safe reason text. Static strings only — never interpolate context
# (this is what keeps `safe_text` leak-free; §16.7 redaction guard).
#
# This is the FULL drafted denial-copy set for the §16.3 reason-code union
# (owner decision Q-0036: Claude drafts, maintainer reviews in the PR).
# DRAFT STATUS: these strings are NOT wired into any live denial path yet —
# the live command-access feedback strings in core/runtime/command_access.py
# are unchanged. Wiring is a follow-up commit after the maintainer's
# read-through of the table in the P1B PR.
# ---------------------------------------------------------------------------

# code -> (safe_text, source, unlock_hint, remediation)
_SAFE_TEXT: dict[str, tuple[str, str, str | None, str | None]] = {
    # axis 1+2 — command_access (codes are DecisionReason.value verbatim)
    "lifecycle_draining": (
        "The bot is restarting — try again in a moment.",
        "command_access",
        "retry shortly",
        None,
    ),
    "dm_not_supported": (
        "This command isn't available in direct messages.",
        "command_access",
        "use it inside the server",
        None,
    ),
    "commands_disabled": (
        "Commands are currently disabled in this server.",
        "command_access",
        None,
        "Enable commands in the Command Access settings.",
    ),
    "channel_not_allowed": (
        "This command isn't enabled in this channel.",
        "command_access",
        "try one of the server's command channels",
        "Add this channel in the Command Access settings.",
    ),
    # axis 3 — routing
    "routing_disabled": (
        "This feature is turned off here.",
        "routing",
        None,
        "Re-enable the feature in the Cog Routing setup section.",
    ),
    # axis 4 — governance
    "subsystem_hidden": (
        "You don't have access to this feature here.",
        "governance",
        None,
        None,
    ),
    "capability_insufficient": (
        "You don't have permission to do that here.",
        "governance",
        None,
        None,
    ),
    # axis 5 — availability (future; availability owns quiet mode — Q-0029)
    "availability_window": (
        "This feature isn't available right now.",
        "availability",
        "try again later",
        None,
    ),
    "quiet_mode": (
        "The server is in quiet hours — this feature is paused.",
        "availability",
        "try again after quiet hours",
        "Adjust quiet hours in the Availability settings.",
    ),
    # bootstrap — setup staging
    "setup_stage_required": (
        "This feature isn't set up yet.",
        "bootstrap",
        None,
        "Finish this feature's setup in the setup wizard.",
    ),
}

_GENERIC_DENIAL = LockedReason(
    code="access_denied",
    safe_text="You can't use this feature here right now.",
    source="unknown",
)


def _locked_reason(reason_code: str | None) -> tuple[LockedReason, str | None]:
    """Map a stable reason code to a user-safe ``LockedReason`` + remediation.

    Falls back to a generic denial for an unmapped code so the renderer can
    never crash on a new code and never leaks an internal string.
    """
    if reason_code and reason_code in _SAFE_TEXT:
        text, source, hint, remediation = _SAFE_TEXT[reason_code]
        return (
            LockedReason(
                code=reason_code,
                safe_text=text,
                source=source,
                unlock_hint=hint,
            ),
            remediation,
        )
    return _GENERIC_DENIAL, None


def safe_locked_reason(reason_code: str | None) -> LockedReason:
    """Public read-only lookup: stable reason code → user-safe copy.

    For surfaces that carry only the code (e.g. a ``HelpDecision`` from
    :func:`services.help_projection.project_help_with_execution`) and need
    the renderable ``safe_text``. Same fallback contract as the internal
    resolver: an unmapped code yields the generic denial, never a crash or
    an internal string.
    """
    return _locked_reason(reason_code)[0]


# ---------------------------------------------------------------------------
# Feature inventory adapter
# ---------------------------------------------------------------------------


def feature_inventory() -> tuple[FeatureEntry, ...]:
    """Enumerate every subsystem as a feature row (registry-driven).

    The representative ``command_name`` is the subsystem's first declared
    ``entry_point`` (the command the command-access/bootstrap axes evaluate).
    Subsystem keys are the snake_case keys guaranteed by Q-0026.
    """
    from utils.subsystem_registry import SUBSYSTEMS

    out: list[FeatureEntry] = []
    for key, meta in SUBSYSTEMS.items():
        eps = tuple(meta.get("entry_points") or ())
        out.append(
            FeatureEntry(
                subsystem=key,
                command_name=eps[0] if eps else None,
                visibility_tier=meta.get("visibility_tier"),
            ),
        )
    return tuple(out)


# ---------------------------------------------------------------------------
# Axis evaluators — each delegates to an existing owner, never decides policy
# ---------------------------------------------------------------------------


async def _axis_command_access(
    feature: FeatureEntry,
    ctx: AccessContext,
) -> AxisOutcome:
    """Axes 1+2 — admission via ``command_access.resolve_command_access``."""
    if feature.command_name is None:
        return AxisOutcome(
            AccessAxis.COMMAND_ACCESS,
            "skipped",
            detail="no representative command",
        )
    from core.runtime.command_access import (
        CommandAccessContext,
        resolve_command_access,
    )

    cactx = CommandAccessContext(
        guild_id=ctx.guild_id,
        channel_id=ctx.channel_id,
        user_id=ctx.user_id,
        command_name=feature.command_name,
        invocation_type=ctx.invocation_type,
        is_guild_operator=ctx.is_guild_operator,
        is_bot_owner=ctx.is_bot_owner,
        is_dm=ctx.is_dm,
    )
    try:
        decision = await resolve_command_access(cactx)
    except Exception as exc:  # noqa: BLE001 — a read model must never crash
        logger.warning("access_projection: command_access axis raised: %s", exc)
        return AxisOutcome(
            AccessAxis.COMMAND_ACCESS,
            "unknown",
            detail="resolver error",
        )
    state: AxisState = "allow" if decision.allowed else "deny"
    return AxisOutcome(
        AccessAxis.COMMAND_ACCESS,
        state,
        reason_code=decision.reason.value,
        detail=decision.source.value,
    )


async def _axis_routing(feature: FeatureEntry, ctx: AccessContext) -> AxisOutcome:
    """Axis 3 — per-channel cog routing via ``command_routing.is_cog_enabled``.

    Routing keys on the **subsystem key** (verified: ``cog_routing_profiles``
    writes ``cog_name="games"``/``"economy"``/...), so the snake_case feature
    key is passed straight through.
    """
    if ctx.guild_id is None:
        return AxisOutcome(AccessAxis.ROUTING, "skipped", detail="no guild")
    from services.command_routing import is_cog_enabled

    try:
        enabled = await is_cog_enabled(
            guild_id=ctx.guild_id,
            cog_name=feature.subsystem,
            channel_id=ctx.channel_id,
            category_id=ctx.category_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("access_projection: routing axis raised: %s", exc)
        return AxisOutcome(AccessAxis.ROUTING, "unknown", detail="resolver error")
    if enabled:
        return AxisOutcome(AccessAxis.ROUTING, "allow")
    return AxisOutcome(AccessAxis.ROUTING, "deny", reason_code="routing_disabled")


async def _axis_governance(feature: FeatureEntry, ctx: AccessContext) -> AxisOutcome:
    """Axis 4 — subsystem visibility + member tier via governance.

    Reuses ``governance.get_visible_subsystems`` — the exact read the
    AccessExplorer view uses — so there is no duplicate visibility logic.

    **Audience simulation (Q-0045, option b):** when ``ctx.member_tier``
    is set it is passed through to governance, whose tier resolution
    prefers a declared tier verbatim.  A context with *no* member but a
    declared tier therefore evaluates instead of degrading to ``unknown``
    — that is the read path Help Preview and the drift baseline use.  The
    outcome ``detail`` labels the simulation and its limit (a declared
    tier cannot model live Discord channel-permission overrides — §16.4).
    """
    if ctx.member is None and ctx.member_tier is None:
        # Without a resolved member or a declared tier we cannot evaluate
        # tier/visibility; report unknown rather than guess (a guess could
        # falsely claim allow).
        return AxisOutcome(AccessAxis.GOVERNANCE, "unknown", detail="no member")
    from governance import get_visible_subsystems
    from governance.models import GovernanceContext

    simulated = (
        f"simulated tier={ctx.member_tier} "
        "(live channel-permission overrides not modeled)"
        if ctx.member_tier is not None
        else None
    )
    gctx = GovernanceContext(
        guild_id=ctx.guild_id or 0,
        channel_id=ctx.channel_id,
        category_id=ctx.category_id,
        member=ctx.member,
        role_ids=set(ctx.member_role_ids),
        member_tier=ctx.member_tier,
    )
    try:
        visible = await get_visible_subsystems(gctx)
    except Exception as exc:  # noqa: BLE001
        logger.warning("access_projection: governance axis raised: %s", exc)
        return AxisOutcome(AccessAxis.GOVERNANCE, "unknown", detail="resolver error")
    if feature.subsystem in visible:
        return AxisOutcome(AccessAxis.GOVERNANCE, "allow", detail=simulated)
    deny_detail = f"required_tier={feature.visibility_tier}"
    if simulated is not None:
        deny_detail = f"{deny_detail}; {simulated}"
    return AxisOutcome(
        AccessAxis.GOVERNANCE,
        "deny",
        reason_code="subsystem_hidden",
        detail=deny_detail,
    )


def _axis_availability(feature: FeatureEntry, ctx: AccessContext) -> AxisOutcome:
    """Axis 5 — central availability policy (§6.6). Not built yet → skipped.

    A ``skipped`` axis never affects the effective result; it is recorded so the
    chain documents that the axis exists and is intentionally inert today.
    """
    return AxisOutcome(
        AccessAxis.AVAILABILITY,
        "skipped",
        detail="availability policy not implemented",
    )


def _axis_help_visibility(feature: FeatureEntry, ctx: AccessContext) -> AxisOutcome:
    """Axis 6 — help visibility (informational ONLY; never gates execution).

    Looks the representative command up in the cached command-surface ledger and
    reports whether help would hide it. Degrades to ``unknown`` when the ledger
    isn't built or the command isn't found.
    """
    if feature.command_name is None:
        return AxisOutcome(
            AccessAxis.HELP,
            "skipped",
            detail="no representative command",
        )
    from core.runtime.command_surface_ledger import (
        get_cached_ledger,
        is_hidden_from_help,
    )

    ledger = get_cached_ledger()
    if ledger is None:
        return AxisOutcome(AccessAxis.HELP, "unknown", detail="ledger not built")
    entry = ledger.find(feature.command_name)
    if entry is None:
        return AxisOutcome(AccessAxis.HELP, "unknown", detail="command not in ledger")
    return AxisOutcome(
        AccessAxis.HELP,
        "hidden" if is_hidden_from_help(entry) else "shown",
    )


# ---------------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------------

# Axes 1-5 gate the effective result, evaluated in this order; the first ``deny``
# short-circuits. Axes 6-7 are appended as non-gating context.
_GATING_DENY_ORDER = (
    AccessAxis.COMMAND_ACCESS,
    AccessAxis.ROUTING,
    AccessAxis.GOVERNANCE,
    AccessAxis.AVAILABILITY,
)


async def resolve_feature_access(
    feature: FeatureEntry,
    ctx: AccessContext,
) -> AccessDecision:
    """Compose every axis into one :class:`AccessDecision` (read-only).

    Short-circuits on the first ``deny`` among the gating axes (1-5). If no axis
    denies but one returned ``unknown``, the effective result is ``unknown``
    (the model never claims ``allow`` it could not verify). The help axis (6) is
    always recorded but can never change ``effective``.
    """
    chain: list[AxisOutcome] = []

    # Gating axes 1-5, in precedence order.
    ca = await _axis_command_access(feature, ctx)
    chain.append(ca)
    if ca.state == "deny":
        return _denied(feature, ca, chain)

    rt = await _axis_routing(feature, ctx)
    chain.append(rt)
    if rt.state == "deny":
        return _denied(feature, rt, chain)

    gv = await _axis_governance(feature, ctx)
    chain.append(gv)
    if gv.state == "deny":
        return _denied(feature, gv, chain)

    av = _axis_availability(feature, ctx)
    chain.append(av)
    if av.state == "deny":
        return _denied(feature, av, chain)

    # Axis 6 — help visibility (informational; never gates).
    chain.append(_axis_help_visibility(feature, ctx))

    # No deny. If any gating axis was unknown, we cannot confidently allow.
    gating = {AccessAxis.COMMAND_ACCESS, AccessAxis.ROUTING, AccessAxis.GOVERNANCE}
    effective: Effective = (
        "unknown"
        if any(o.axis in gating and o.state == "unknown" for o in chain)
        else "allow"
    )
    return AccessDecision(
        feature=feature.subsystem,
        command_name=feature.command_name,
        effective=effective,
        deciding_axis=None,
        reason=None,
        source_chain=tuple(chain),
    )


def _denied(
    feature: FeatureEntry,
    outcome: AxisOutcome,
    chain: list[AxisOutcome],
) -> AccessDecision:
    reason, remediation = _locked_reason(outcome.reason_code)
    return AccessDecision(
        feature=feature.subsystem,
        command_name=feature.command_name,
        effective="deny",
        deciding_axis=outcome.axis,
        reason=reason,
        source_chain=tuple(chain),
        remediation=remediation,
    )


async def project_access_map(ctx: AccessContext) -> tuple[AccessDecision, ...]:
    """Project the access decision for **every** feature in one context.

    The batch surface a future read-only Access Map panel (P1C) renders. Pure
    composition over :func:`feature_inventory`; no persistence.
    """
    return tuple(
        [await resolve_feature_access(feature, ctx) for feature in feature_inventory()],
    )


__all__ = [
    "AccessAxis",
    "AccessContext",
    "AccessDecision",
    "AxisOutcome",
    "FeatureEntry",
    "LockedReason",
    "feature_inventory",
    "project_access_map",
    "resolve_feature_access",
    "safe_locked_reason",
]
