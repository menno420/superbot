"""Governance scope chain traversal and visibility resolution.

Layer: models → events → cache → dependency → resolver.
Imports from governance.models, governance.cache, governance.dependency,
and external utils (subsystem_registry, visibility_rules, db, settings_keys).
"""

from __future__ import annotations

import logging

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
from utils import db, settings_keys
from utils.subsystem_registry import SUBSYSTEMS
from utils.visibility_rules import get_member_visibility_tier, get_subsystems_for_tier

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
        "thread": ctx.thread_id,  # ISSUE-016
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
# Trusted tier resolution (ISSUE-015)
# ---------------------------------------------------------------------------


async def _resolve_member_tier(ctx: GovernanceContext) -> str:
    """Resolve the member's visibility tier, applying trusted role check (ISSUE-015)."""
    if ctx.member is None:
        return "user"

    tier = get_member_visibility_tier(
        ctx.member,
        ctx.member.guild.owner_id if ctx.member.guild else 0,
    )

    # Trusted tier: if the guild has a TRUSTED_TIER_ROLE_ID setting and the
    # member has that role, promote them to "trusted" (but only if they're
    # currently "user" — higher tiers like staff/mod/admin take precedence).
    if tier == "user":
        try:
            trusted_role_id = await db.get_setting(
                ctx.guild_id,
                settings_keys.TRUSTED_TIER_ROLE_ID,
                default="",
            )
            if (
                trusted_role_id
                and ctx.role_ids
                and int(trusted_role_id) in ctx.role_ids
            ):
                tier = "trusted"
        except Exception:
            # Fail gracefully: if the setting lookup fails, stay at "user"
            pass

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
    Results are cached by (guild_id, version, channel_id, member_tier).
    """
    tier = await _resolve_member_tier(ctx)

    role_ids = frozenset(ctx.role_ids) if ctx.role_ids else frozenset()
    cache_key = _cache_key(ctx.guild_id, ctx.channel_id, tier, role_ids)
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
