"""Governance scope chain traversal and visibility resolution.

Layer: models → events → cache → dependency → resolver.
Imports from governance.models, governance.cache, governance.dependency,
and external utils (subsystem_registry, visibility_rules, db, settings_keys).
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from config import is_platform_owner
from governance.cache import (
    _CACHE_LOCK,
    _FAILED_SUBSYSTEMS,
    _cache_get,
    _cache_key,
    _cache_set,
)
from governance.dependency import _apply_dependency_rules
from governance.models import (
    SCOPE_PARENT,
    GovernanceContext,
    PolicySource,
    ResolutionTrace,
    SubsystemState,
    VisibilityResult,
)
from utils import db
from utils.subsystem_registry import SUBSYSTEMS
from utils.visibility_rules import (
    VISIBILITY_TIERS,
    get_member_visibility_tier,
    get_subsystems_for_tier,
    is_tier_sufficient,
)

logger = logging.getLogger("bot")

# Import metrics lazily to avoid circular issues at module init
try:
    from services import metrics as _metrics
except Exception:
    _metrics = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Scope chain builder
# ---------------------------------------------------------------------------


def _build_scope_chain(ctx: GovernanceContext) -> list[tuple[str, int]]:
    """Build ordered scope list via SCOPE_PARENT traversal.

    Returns list from most-specific to least-specific, e.g.:
      [("thread", 111), ("channel", 123), ("category", 456), ("guild", 789)]

    This function is the ONLY place that knows the traversal order.
    """
    scope_id_map: dict[str, int | None] = {
        "thread": ctx.thread_id,
        "channel": ctx.channel_id,
        "category": ctx.category_id,
        "guild": ctx.guild_id,
    }
    chain: list[tuple[str, int]] = []
    scope: str | None = "thread"
    while scope is not None:
        sid = scope_id_map.get(scope)
        if sid is not None:
            chain.append((scope, sid))
        scope = SCOPE_PARENT.get(scope)
    return chain


# ---------------------------------------------------------------------------
# DB override resolution
# ---------------------------------------------------------------------------


async def _fetch_all_visibility(
    guild_id: int,
    chain: list[tuple[str, int]],
) -> dict[tuple[str, int], dict[str, bool | None]]:
    """Fetch all visibility rows for the scope chain in a single DB query."""
    if not chain:
        return {}
    scope_types = [s for s, _ in chain]
    scope_ids = [i for _, i in chain]
    rows = await db.get().fetch(
        """SELECT scope_type, scope_id, subsystem, enabled
           FROM subsystem_visibility
           WHERE guild_id=$1
             AND scope_type = ANY($2::text[])
             AND scope_id   = ANY($3::bigint[])""",
        guild_id,
        scope_types,
        scope_ids,
    )
    result: dict[tuple[str, int], dict[str, bool | None]] = {
        (s, i): {} for s, i in chain
    }
    for row in rows:
        key = (row["scope_type"], row["scope_id"])
        if key in result:
            result[key][row["subsystem"]] = row["enabled"]
    return result


def _resolve_single_subsystem(
    subsystem: str,
    chain: list[tuple[str, int]],
    scope_data: dict[tuple[str, int], dict[str, bool | None]],
) -> tuple[bool | None, PolicySource, list[str]]:
    """Walk the scope chain for one subsystem.

    Returns (resolved_bool_or_None, source, checked_scope_labels).
    None means "no override found anywhere" → caller uses registry default.
    """
    checked: list[str] = []
    _SCOPE_TO_SOURCE: dict[str, PolicySource] = {
        "thread": PolicySource.THREAD_OVERRIDE,
        "channel": PolicySource.CHANNEL_OVERRIDE,
        "category": PolicySource.CATEGORY_OVERRIDE,
        "guild": PolicySource.GUILD_OVERRIDE,
        "role": PolicySource.ROLE_OVERRIDE,
    }
    for scope_type, scope_id in chain:
        scope_map = scope_data.get((scope_type, scope_id), {})
        checked.append(scope_type)
        if subsystem in scope_map:
            val = scope_map[subsystem]
            if val is None:
                # Explicit NULL = inherit from next scope
                continue
            return val, _SCOPE_TO_SOURCE[scope_type], checked
    # No override found
    return None, PolicySource.INHERITED_DEFAULT, checked


# ---------------------------------------------------------------------------
# Configured-role tier grants (trusted: ISSUE-015 / moderator: ADR-008)
# ---------------------------------------------------------------------------


async def _role_grants_tier(
    guild_id: int,
    reader: Callable[[int], Awaitable[Any]],
    role_ids: set[int],
) -> bool:
    """True when the guild's configured role (via ``reader``) is one the member holds.

    ``reader`` is a :mod:`core.runtime.config_arbitration` getter returning a
    ``ConfigReadResult`` whose ``.value`` is the configured role id (or ``None``).
    A read failure degrades to ``False`` (no grant): a configured role may only
    ever *add* standing, so a config-store hiccup must fail toward the lower
    tier and can never escalate authority.
    """
    if not role_ids:
        return False
    try:
        result = await reader(guild_id)
    except Exception:  # noqa: BLE001 — a failed read must never grant a tier
        return False
    role_id = result.value
    return role_id is not None and role_id in role_ids


async def _resolve_member_tier(ctx: GovernanceContext) -> str:
    """Resolve the member's effective tier, applying configured-role grants.

    **Declared-tier read path (Q-0045, option b):** when
    ``ctx.member_tier`` is set, it is preferred verbatim — member
    derivation *and* the configured-role grants are skipped, because the
    caller declared the **effective** standing to evaluate (the read-only
    audience-simulation input for Help Preview and the
    ``help_advertises_locked`` drift baseline).  A declared value outside
    :data:`utils.visibility_rules.VISIBILITY_TIERS` is ignored with a
    warning and resolution proceeds as if unset, so a bad input can never
    escalate (nor demote) anyone.

    The base tier comes from Discord permissions
    (:func:`utils.visibility_rules.get_member_visibility_tier`).  Two
    configured-role grants may then *raise* it — never lower it:

    * the **moderator** role (``moderator_tier_role_id``) grants the
      ``moderator`` tier, so its holders may use moderation actions without
      holding the matching Discord permissions (capability-native authority,
      ADR-008);
    * the **trusted** role (``trusted_tier_role_id``) grants the ``trusted``
      tier (ISSUE-015).

    A grant applies only when the base tier is *below* the granted tier, so a
    real administrator/owner is never demoted and the two grants compose (the
    higher one wins).  Reads flow through the Phase 2 arbitration helpers so the
    canary flip of ``bindings.primary`` stays a single change in
    :mod:`core.runtime.config_arbitration`; this function MUST NOT branch on
    ``is_enabled("bindings.primary", ...)`` directly (forbidden by the PR-7
    invariant test).
    """
    if ctx.member_tier is not None:
        if ctx.member_tier in VISIBILITY_TIERS:
            return ctx.member_tier
        logger.warning(
            "governance: ignoring unknown declared member_tier %r (guild %s)",
            ctx.member_tier,
            ctx.guild_id,
        )

    if ctx.member is None:
        return "user"

    # Platform-owner override: the configured bot owner
    # (config.BOT_OWNER_USER_ID / PermissionTier.PLATFORM_OWNER) is treated as
    # the top visibility tier in any guild they are a member of, so they see
    # every subsystem and pass execution gates (resolve_execution / can_execute)
    # — letting them set the bot up correctly even without Discord perms there.
    # "owner" is the maximum tier in VISIBILITY_TIERS; returning it here (after
    # the declared-tier simulation path above) keeps audience-simulation
    # previews honest while elevating the real owner.
    if is_platform_owner(ctx.member.id):
        return "owner"

    tier = get_member_visibility_tier(
        ctx.member,
        ctx.member.guild.owner_id if ctx.member.guild else 0,
    )

    if ctx.role_ids:
        # Local import — keep core.runtime out of governance/__init__'s
        # module-load cycle (PR #74 protection).  resolver.py is a sibling of
        # __init__.py but follows the same discipline.
        from core.runtime.config_arbitration import (
            get_moderator_tier_role,
            get_trusted_tier_role,
        )

        if not is_tier_sufficient(tier, "moderator") and await _role_grants_tier(
            ctx.guild_id,
            get_moderator_tier_role,
            ctx.role_ids,
        ):
            tier = "moderator"
        if not is_tier_sufficient(tier, "trusted") and await _role_grants_tier(
            ctx.guild_id,
            get_trusted_tier_role,
            ctx.role_ids,
        ):
            tier = "trusted"

    return tier


# ---------------------------------------------------------------------------
# Visibility overrides resolution
# ---------------------------------------------------------------------------


async def _resolve_visibility_overrides(
    ctx: GovernanceContext,
    tier_accessible: set[str],
) -> tuple[
    dict[str, SubsystemState],
    dict[str, ResolutionTrace],
    dict[str, PolicySource],
]:
    """Resolve visibility state for all subsystems via scope chain.

    Returns (states, traces, resolved_from).
    """
    chain = _build_scope_chain(ctx)
    scope_data = await _fetch_all_visibility(ctx.guild_id, chain)

    states: dict[str, SubsystemState] = {}
    traces: dict[str, ResolutionTrace] = {}
    resolved_from: dict[str, PolicySource] = {}

    for name, meta in SUBSYSTEMS.items():
        # Tier gate — member doesn't have visibility tier for this subsystem
        if name not in tier_accessible:
            states[name] = SubsystemState.DISABLED
            traces[name] = ResolutionTrace(
                subsystem=name,
                checked_scopes=[],
                matched_scope=PolicySource.REGISTRY_DEFAULT,
                dependency_blocks=[],
                final_state=SubsystemState.DISABLED,
            )
            resolved_from[name] = PolicySource.REGISTRY_DEFAULT
            continue

        # Cog load failure gate — treat as internal so help menus stay clean
        if name in _FAILED_SUBSYSTEMS:
            states[name] = SubsystemState.INTERNAL
            traces[name] = ResolutionTrace(
                subsystem=name,
                checked_scopes=[],
                matched_scope=PolicySource.REGISTRY_DEFAULT,
                dependency_blocks=[],
                final_state=SubsystemState.INTERNAL,
            )
            resolved_from[name] = PolicySource.REGISTRY_DEFAULT
            continue

        # Visibility mode gate
        mode = meta.get("visibility_mode", "normal")
        if mode == "internal":
            states[name] = SubsystemState.INTERNAL
            traces[name] = ResolutionTrace(
                subsystem=name,
                checked_scopes=[],
                matched_scope=PolicySource.REGISTRY_DEFAULT,
                dependency_blocks=[],
                final_state=SubsystemState.INTERNAL,
            )
            resolved_from[name] = PolicySource.REGISTRY_DEFAULT
            continue

        # Scope chain resolution
        override_val, source, checked = _resolve_single_subsystem(
            name,
            chain,
            scope_data,
        )

        if override_val is False:
            final = SubsystemState.DISABLED
        elif override_val is True:
            final = SubsystemState.ENABLED
        else:
            # No override — default to enabled
            final = SubsystemState.ENABLED
            source = PolicySource.REGISTRY_DEFAULT

        states[name] = final
        traces[name] = ResolutionTrace(
            subsystem=name,
            checked_scopes=checked,
            matched_scope=source if override_val is not None else None,
            dependency_blocks=[],
            final_state=final,
        )
        resolved_from[name] = source

    return states, traces, resolved_from


# ---------------------------------------------------------------------------
# Public resolve_visibility
# ---------------------------------------------------------------------------


async def resolve_visibility(ctx: GovernanceContext) -> VisibilityResult:
    """Resolve which subsystems are visible to this member in this context.

    Scope resolution: thread > channel > category > guild > registry default.
    Dependency rules applied after scope resolution (topological order).
    Results are cached by (guild_id, version, channel_id, thread_id, member_tier)
    so a thread context never collides with a sibling thread or the parent
    channel (RC-2 / ISSUE-016).
    """
    tier = await _resolve_member_tier(ctx)

    role_ids = frozenset(ctx.role_ids) if ctx.role_ids else frozenset()
    cache_key = _cache_key(
        ctx.guild_id,
        ctx.channel_id,
        tier,
        role_ids,
        thread_id=ctx.thread_id,
    )
    _guild_label = str(ctx.guild_id)

    async with _CACHE_LOCK:
        cached = _cache_get(cache_key)
        if cached is not None:
            if _metrics:
                _metrics.governance_cache_hits.labels(guild_id=_guild_label).inc()
            return cached

    if _metrics:
        _metrics.governance_cache_misses.labels(guild_id=_guild_label).inc()

    tier_accessible = set(get_subsystems_for_tier(tier))

    states, traces, resolved_from = await _resolve_visibility_overrides(
        ctx,
        tier_accessible,
    )
    _apply_dependency_rules(states, traces, resolved_from)

    visible = {
        name for name, state in states.items() if state == SubsystemState.ENABLED
    }

    result = VisibilityResult(
        visible_subsystems=visible,
        member_tier=tier,
        resolved_from=resolved_from,
        traces=traces,
    )

    async with _CACHE_LOCK:
        _cache_set(cache_key, result)

    return result


async def get_visible_subsystems(ctx: GovernanceContext) -> set[str]:
    """Convenience wrapper — returns only the visible subsystem name set."""
    result = await resolve_visibility(ctx)
    return result.visible_subsystems
