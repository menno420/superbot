"""Central governance orchestration service.

Plugin Isolation Contract
-------------------------
Plugins MAY:
  - call any public async function defined here
  - register subsystems in subsystem_registry (before validate_registry())
  - register capabilities following {subsystem}.{resource}.{action} namespace

Plugins MAY NOT:
  - mutate the registry after validate_registry() has been called (TypeError enforced)
  - bypass this service and write governance DB tables (subsystem_visibility,
    cleanup_policies) directly
  - call db.set_subsystem_visibility / db.set_cleanup_policy directly
  - emit governance.* events directly
  - hold references to _CACHE, _CACHE_VERSION, or _CACHE_LOCK

Architectural layer terminology:
  registry   — immutable subsystem metadata (subsystem_registry.py)
  visibility — UI/help discoverability (what appears in menus)
  execution  — capability authorization (what can actually run)
  cleanup    — moderation behavior (delete/feedback policies)
  governance — orchestration: this file combines all layers into resolved policies

Internal pipeline isolation: each concern lives in its own private function.
No public function may inline more than one concern.
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import config as _config
import discord
from utils import db, settings_keys
from utils.subsystem_registry import (
    _COMPILED_DEPENDENCY_ORDER,
    _COMPILED_DEPENDENTS,
    COMMAND_TO_SUBSYSTEM,
    REGISTRY_SCHEMA_VERSION,
    REGISTRY_VERSION,
    SUBSYSTEMS,
    capability_matches,
    get_subsystem_for_command,
)
from utils.visibility_rules import (
    get_member_visibility_tier,
    get_subsystems_for_tier,
    is_tier_sufficient,
)

logger = logging.getLogger("bot")

# ---------------------------------------------------------------------------
# Canonical governance event names
# Do NOT rename after v1 — external consumers may depend on these strings.
# ---------------------------------------------------------------------------

EVT_VISIBILITY_CHANGED = "governance.visibility.changed"
EVT_CLEANUP_CHANGED = "governance.cleanup.changed"
EVT_EXECUTION_DENIED = "governance.execution.denied"
EVT_EXECUTION_ALLOWED = "governance.execution.allowed"
EVT_CACHE_INVALIDATED = "governance.cache.invalidated"

# ---------------------------------------------------------------------------
# Scope resolution constants
# ---------------------------------------------------------------------------

SCOPE_PRIORITY: list[str] = ["channel", "category", "guild"]
SCOPE_PARENT: dict[str, str | None] = {
    "channel": "category",
    "category": "guild",
    "guild": None,
    # Future: prepend "thread" → "channel"
}

# ---------------------------------------------------------------------------
# Internal enums
# ---------------------------------------------------------------------------


class SubsystemState(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    INHERITED = "inherited"  # no override at this scope
    BLOCKED_DEPENDENCY = "blocked_dep"  # a hard dependency is disabled
    INTERNAL = "internal"  # visibility_mode == "internal"
    EXPERIMENTAL_DISABLED = "exp_disabled"  # experimental, not opted in


class PolicySource(Enum):
    """Typed provenance for governance decisions.
    Serialized to .value strings only in to_dict().
    """

    REGISTRY_DEFAULT = "registry_default"  # derived from registry; no DB override
    INHERITED_DEFAULT = "inherited_default"  # walked entire scope chain; no override
    FALLBACK_DEFAULT = "fallback_default"  # hardcoded compat (e.g. config whitelist)
    DEPENDENCY_BLOCK = "dependency_block"  # blocked by a disabled dependency
    CHANNEL_OVERRIDE = "channel"
    CATEGORY_OVERRIDE = "category"
    GUILD_OVERRIDE = "guild"
    ROLE_OVERRIDE = "role"


# ---------------------------------------------------------------------------
# Public context + result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class GovernanceContext:
    """Carries all context needed for governance resolution.

    Use from_ctx() / from_interaction() rather than constructing directly.
    Future-proofs for threads, DMs, dashboards, AI agents, scheduled jobs.
    """

    guild_id: int
    channel_id: int | None = None
    category_id: int | None = None
    thread_id: int | None = None
    member: discord.Member | None = None
    role_ids: set[int] = field(default_factory=set)

    @classmethod
    def from_ctx(cls, ctx) -> "GovernanceContext":
        channel = ctx.channel
        category_id = getattr(channel, "category_id", None)
        member = ctx.author
        return cls(
            guild_id=ctx.guild.id,
            channel_id=getattr(channel, "id", None),
            category_id=category_id,
            member=member,
            role_ids={r.id for r in getattr(member, "roles", [])},
        )

    @classmethod
    def from_interaction(cls, interaction: discord.Interaction) -> "GovernanceContext":
        channel = interaction.channel
        category_id = getattr(channel, "category_id", None)
        member = interaction.user
        return cls(
            guild_id=interaction.guild_id,
            channel_id=getattr(channel, "id", None),
            category_id=category_id,
            member=member,
            role_ids={r.id for r in getattr(member, "roles", [])},
        )

    @classmethod
    def from_message(cls, message: discord.Message) -> "GovernanceContext":
        channel = message.channel
        category_id = getattr(channel, "category_id", None)
        member = message.author
        return cls(
            guild_id=message.guild.id if message.guild else 0,
            channel_id=getattr(channel, "id", None),
            category_id=category_id,
            member=member,
            role_ids={r.id for r in getattr(member, "roles", [])},
        )


@dataclass
class ResolutionTrace:
    subsystem: str
    checked_scopes: list[str]
    matched_scope: PolicySource | None
    dependency_blocks: list[str]
    final_state: SubsystemState

    def to_dict(self) -> dict:
        return {
            "subsystem": self.subsystem,
            "checked_scopes": sorted(self.checked_scopes),
            "matched_scope": self.matched_scope.value if self.matched_scope else None,
            "dependency_blocks": sorted(self.dependency_blocks),
            "final_state": self.final_state.value,
        }


@dataclass
class VisibilityResult:
    visible_subsystems: set[str]
    member_tier: str
    resolved_from: dict[str, PolicySource]
    traces: dict[str, ResolutionTrace]

    def to_dict(self) -> dict:
        return {
            "visible_subsystems": sorted(self.visible_subsystems),
            "member_tier": self.member_tier,
            "resolved_from": {
                k: v.value for k, v in sorted(self.resolved_from.items())
            },
            "traces": {k: v.to_dict() for k, v in sorted(self.traces.items())},
        }


@dataclass
class ExecutionTrace:
    capability: str
    checked_scopes: list[str]
    matched_scope: str | None
    denied_by: str | None
    final_result: bool

    def to_dict(self) -> dict:
        return {
            "capability": self.capability,
            "checked_scopes": sorted(self.checked_scopes),
            "matched_scope": self.matched_scope,
            "denied_by": self.denied_by,
            "final_result": self.final_result,
        }


@dataclass
class ExecutionResult:
    allowed: bool
    reason: str | None = None
    resolved_scope: str | None = None
    matched_capability: str | None = None
    trace: ExecutionTrace | None = None


@dataclass
class CleanupPolicy:
    delete_message: bool
    delete_after_seconds: int
    send_feedback: bool
    resolved_from: PolicySource

    def to_dict(self) -> dict:
        return {
            "delete_message": self.delete_message,
            "delete_after_seconds": self.delete_after_seconds,
            "send_feedback": self.send_feedback,
            "resolved_from": self.resolved_from.value,
        }


@dataclass
class CommandPolicy:
    allowed: bool
    cleanup: CleanupPolicy
    feedback: str | None
    redirect_channel_mention: str | None


@dataclass
class SubsystemEffectiveState:
    """Complete resolved state for one subsystem in one context.
    Powers /why, per-subsystem diagnostics, AI explanations.
    """

    name: str
    state: SubsystemState
    visibility_source: PolicySource
    execution_allowed: bool
    execution_source: PolicySource
    dependency_blocks: list[str]
    cleanup_policy: CleanupPolicy
    trace: ResolutionTrace

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "visibility_source": self.visibility_source.value,
            "execution_allowed": self.execution_allowed,
            "execution_source": self.execution_source.value,
            "dependency_blocks": sorted(self.dependency_blocks),
            "cleanup_policy": self.cleanup_policy.to_dict(),
            "trace": self.trace.to_dict(),
        }


@dataclass
class GovernanceHealthReport:
    orphan_overrides: list[dict]
    stale_version_guilds: list[int]
    invalid_cleanup_configs: list[dict]
    summary: str


@dataclass
class GovernanceSnapshot:
    """Complete governance state for a context.
    Powers dashboards, /why, AI reasoning, export/import.
    All fields JSON-safe. Use to_dict() for serialization.
    """

    visible_subsystems: set[str]
    denied_subsystems: set[str]
    dependency_blocks: dict[str, list[str]]
    cleanup_policy: CleanupPolicy
    member_tier: str
    scope_provenance: dict[str, PolicySource]
    capability_map: dict[str, bool]
    registry_version: int
    registry_schema_version: int

    def to_dict(self) -> dict:
        return {
            "visible_subsystems": sorted(self.visible_subsystems),
            "denied_subsystems": sorted(self.denied_subsystems),
            "dependency_blocks": {
                k: sorted(v) for k, v in sorted(self.dependency_blocks.items())
            },
            "cleanup_policy": self.cleanup_policy.to_dict(),
            "member_tier": self.member_tier,
            "scope_provenance": {
                k: v.value for k, v in sorted(self.scope_provenance.items())
            },
            "capability_map": {k: v for k, v in sorted(self.capability_map.items())},
            "registry_version": self.registry_version,
            "registry_schema_version": self.registry_schema_version,
        }


# ---------------------------------------------------------------------------
# Cache — version-stamped, tier-keyed (not member-keyed)
# ---------------------------------------------------------------------------

_CACHE: dict[tuple, tuple[float, Any]] = {}
_CACHE_VERSION: dict[int, int] = {}  # guild_id → version counter
_CACHE_LOCK = asyncio.Lock()
_CACHE_TTL = 60.0
_NO_OVERRIDE = object()  # sentinel for negative cache entries


def _cache_ver(guild_id: int) -> int:
    return _CACHE_VERSION.get(guild_id, 0)


def _cache_key(guild_id: int, channel_id: int | None, tier: str) -> tuple:
    return (guild_id, _cache_ver(guild_id), channel_id, tier)


def _cache_get(key: tuple) -> Any:
    entry = _CACHE.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.monotonic() - ts > _CACHE_TTL:
        return None
    return value


def _cache_set(key: tuple, value: Any) -> None:
    _CACHE[key] = (time.monotonic(), value)
    # Lazy cleanup: remove entries from previous versions (unreachable anyway)
    if len(_CACHE) > 2000:
        cutoff = time.monotonic() - _CACHE_TTL
        stale = [k for k, (ts, _) in _CACHE.items() if ts < cutoff]
        for k in stale:
            _CACHE.pop(k, None)


def invalidate_guild_cache(guild_id: int) -> None:
    """Increment version counter — old keys become unreachable (O(1))."""
    _CACHE_VERSION[guild_id] = _cache_ver(guild_id) + 1


# ---------------------------------------------------------------------------
# Profiling hooks (no-op; wired for future metrics)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def _profile(operation: str):
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed = time.monotonic() - start
        logger.debug("governance_profile op=%s elapsed=%.4f", operation, elapsed)


# ---------------------------------------------------------------------------
# Feedback debouncing
# ---------------------------------------------------------------------------

_FEEDBACK_COOLDOWN: dict[tuple[int, str], float] = {}
_FEEDBACK_COOLDOWN_SECS = 10


def _should_send_feedback(channel_id: int, subsystem: str) -> bool:
    key = (channel_id, subsystem)
    if time.monotonic() - _FEEDBACK_COOLDOWN.get(key, 0.0) > _FEEDBACK_COOLDOWN_SECS:
        _FEEDBACK_COOLDOWN[key] = time.monotonic()
        return True
    return False


# ---------------------------------------------------------------------------
# Internal pipeline — scope chain traversal
# ---------------------------------------------------------------------------


def _build_scope_chain(ctx: GovernanceContext) -> list[tuple[str, int]]:
    """Build ordered scope list via SCOPE_PARENT traversal.

    Returns list from most-specific to least-specific, e.g.:
      [("channel", 123), ("category", 456), ("guild", 789)]

    Future: prepend ("thread", thread_id) before ("channel", channel_id).
    This function is the ONLY place that knows the traversal order.
    """
    scope_id_map: dict[str, int | None] = {
        "channel": ctx.channel_id,
        "category": ctx.category_id,
        "guild": ctx.guild_id,
    }
    chain: list[tuple[str, int]] = []
    scope: str | None = "channel"
    while scope is not None:
        sid = scope_id_map.get(scope)
        if sid is not None:
            chain.append((scope, sid))
        scope = SCOPE_PARENT.get(scope)
    return chain


# ---------------------------------------------------------------------------
# Internal pipeline — DB override resolution
# ---------------------------------------------------------------------------


async def _fetch_all_visibility(
    guild_id: int, chain: list[tuple[str, int]]
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
# Internal pipeline — dependency propagation
# ---------------------------------------------------------------------------


def _apply_dependency_rules(
    states: dict[str, SubsystemState],
    traces: dict[str, ResolutionTrace],
    resolved_from: dict[str, PolicySource],
) -> None:
    """Propagate hard dependency blocking using topological order.

    Modifies states, traces, and resolved_from in-place.
    Uses _COMPILED_DEPENDENCY_ORDER so deps are always processed before dependents.
    Soft dependencies are not propagated (future: UI hint only).
    """
    for subsystem in _COMPILED_DEPENDENCY_ORDER:
        if subsystem not in states:
            continue
        meta = SUBSYSTEMS.get(subsystem)
        if not meta:
            continue
        blocking_deps = [
            dep
            for dep in meta.get("dependencies", [])
            if states.get(dep)
            in (SubsystemState.DISABLED, SubsystemState.BLOCKED_DEPENDENCY)
        ]
        if blocking_deps and states[subsystem] == SubsystemState.ENABLED:
            states[subsystem] = SubsystemState.BLOCKED_DEPENDENCY
            resolved_from[subsystem] = PolicySource.DEPENDENCY_BLOCK
            if subsystem in traces:
                traces[subsystem].dependency_blocks.extend(blocking_deps)
                traces[subsystem].final_state = SubsystemState.BLOCKED_DEPENDENCY
                traces[subsystem].matched_scope = PolicySource.DEPENDENCY_BLOCK


# ---------------------------------------------------------------------------
# Internal pipeline — visibility resolution
# ---------------------------------------------------------------------------


async def _resolve_visibility_overrides(
    ctx: GovernanceContext,
    tier_accessible: set[str],
) -> tuple[
    dict[str, SubsystemState], dict[str, ResolutionTrace], dict[str, PolicySource]
]:
    """Resolve visibility state for all subsystems via scope chain.

    Returns (states, traces, resolved_from).
    """
    async with _profile("db.get_visibility"):
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
            name, chain, scope_data
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
# Internal pipeline — cleanup policy resolution
# ---------------------------------------------------------------------------


async def _resolve_cleanup_overrides(ctx: GovernanceContext) -> CleanupPolicy:
    """Resolve cleanup policy with scope fallback: channel > guild > default.

    Default preserves backwards-compatible behavior (config whitelist logic).
    """
    chain = _build_scope_chain(ctx)
    for scope_type, scope_id in chain:
        if scope_type == "role":
            continue  # cleanup_policies doesn't support role scope
        async with _profile("db.get_cleanup_policy"):
            row = await db.get_cleanup_policy(ctx.guild_id, scope_type, scope_id)
        if row is not None:
            source_map = {
                "channel": PolicySource.CHANNEL_OVERRIDE,
                "category": PolicySource.CATEGORY_OVERRIDE,
                "guild": PolicySource.GUILD_OVERRIDE,
            }
            return CleanupPolicy(
                delete_message=row["delete_invalid_commands"],
                delete_after_seconds=row["delete_after_seconds"],
                send_feedback=True,
                resolved_from=source_map.get(scope_type, PolicySource.GUILD_OVERRIDE),
            )

    # Backwards-compatible default: behave like config.CLEANUP_WHITELIST_CHANNELS
    if ctx.channel_id and ctx.channel_id in _config.CLEANUP_WHITELIST_CHANNELS:
        return CleanupPolicy(
            delete_message=False,
            delete_after_seconds=0,
            send_feedback=False,
            resolved_from=PolicySource.FALLBACK_DEFAULT,
        )
    return CleanupPolicy(
        delete_message=True,
        delete_after_seconds=5,
        send_feedback=True,
        resolved_from=PolicySource.FALLBACK_DEFAULT,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_redirect_channel(
    guild: discord.Guild | None, subsystem_meta: dict
) -> str | None:
    if guild is None:
        return None
    for ch_name in subsystem_meta.get("default_channels", []):
        ch = discord.utils.get(guild.text_channels, name=ch_name)
        if ch:
            return ch.mention
    return None


def _build_feedback(subsystem_meta: dict, redirect: str | None) -> str:
    name = subsystem_meta.get("display_name", "This")
    emoji = subsystem_meta.get("emoji", "❌")
    if redirect:
        return f"{emoji} **{name}** commands are disabled here. Use {redirect} instead."
    return f"{emoji} **{name}** commands are disabled in this channel."


# ---------------------------------------------------------------------------
# Public API — visibility
# ---------------------------------------------------------------------------


async def resolve_visibility(ctx: GovernanceContext) -> VisibilityResult:
    """Resolve which subsystems are visible to this member in this context.

    Scope resolution: channel > category > guild > registry default.
    Dependency rules applied after scope resolution (topological order).
    Results are cached by (guild_id, version, channel_id, member_tier).
    """
    if ctx.member is None:
        tier = "user"
    else:
        tier = get_member_visibility_tier(
            ctx.member,
            ctx.member.guild.owner_id if ctx.member.guild else 0,
        )

    cache_key = _cache_key(ctx.guild_id, ctx.channel_id, tier)
    async with _CACHE_LOCK:
        cached = _cache_get(cache_key)
        if cached is not None and cached is not _NO_OVERRIDE:
            return cached

    tier_accessible = set(get_subsystems_for_tier(tier))

    async with _profile("resolve_visibility"):
        states, traces, resolved_from = await _resolve_visibility_overrides(
            ctx, tier_accessible
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


# ---------------------------------------------------------------------------
# Public API — execution
# ---------------------------------------------------------------------------


async def resolve_execution(ctx: GovernanceContext, capability: str) -> ExecutionResult:
    """Determine if a capability is executable in this context.

    Separate from visibility — a subsystem can be hidden but still executable
    (e.g. internal commands, AI-triggered actions, API calls).
    Currently: delegates to visibility resolution for the capability's subsystem.
    Future: independent execution policy layer.
    """
    async with _profile("resolve_execution"):
        vis = await resolve_visibility(ctx)
        from utils.subsystem_registry import CAPABILITY_TO_SUBSYSTEM

        subsystem_name = CAPABILITY_TO_SUBSYSTEM.get(capability)

        if not subsystem_name:
            return ExecutionResult(
                allowed=True,
                reason="Unknown capability — no governance restriction",
                trace=ExecutionTrace(
                    capability=capability,
                    checked_scopes=[],
                    matched_scope=None,
                    denied_by=None,
                    final_result=True,
                ),
            )

        allowed = subsystem_name in vis.visible_subsystems
        trace_obj = vis.traces.get(subsystem_name)
        denied_by = trace_obj.final_state.value if trace_obj and not allowed else None

        if not allowed:
            await _emit_governance_event(
                EVT_EXECUTION_DENIED,
                {
                    "guild_id": ctx.guild_id,
                    "capability": capability,
                    "subsystem": subsystem_name,
                    "denied_by": denied_by,
                },
            )
        else:
            await _emit_governance_event(
                EVT_EXECUTION_ALLOWED,
                {
                    "guild_id": ctx.guild_id,
                    "capability": capability,
                    "subsystem": subsystem_name,
                },
            )

        return ExecutionResult(
            allowed=allowed,
            reason=denied_by,
            resolved_scope=(
                trace_obj.matched_scope.value
                if trace_obj and trace_obj.matched_scope
                else None
            ),
            matched_capability=capability if allowed else None,
            trace=ExecutionTrace(
                capability=capability,
                checked_scopes=trace_obj.checked_scopes if trace_obj else [],
                matched_scope=(
                    trace_obj.matched_scope.value
                    if trace_obj and trace_obj.matched_scope
                    else None
                ),
                denied_by=denied_by,
                final_result=allowed,
            ),
        )


# ---------------------------------------------------------------------------
# Public API — cleanup policy
# ---------------------------------------------------------------------------


async def resolve_cleanup_policy(ctx: GovernanceContext) -> CleanupPolicy:
    """Resolve cleanup behavior for this context."""
    async with _profile("resolve_cleanup_policy"):
        return await _resolve_cleanup_overrides(ctx)


# ---------------------------------------------------------------------------
# Public API — command policy (combines visibility + cleanup)
# ---------------------------------------------------------------------------


async def resolve_command_policy(
    ctx: GovernanceContext, command_name: str
) -> CommandPolicy:
    """Full policy resolution for a message command invocation attempt.

    Returns allowed=True for unknown commands (not a governance concern).
    """
    async with _profile("resolve_command_policy"):
        found = get_subsystem_for_command(command_name)
        if found is None:
            # Unknown command — not a governance concern
            return CommandPolicy(
                allowed=True,
                cleanup=CleanupPolicy(
                    delete_message=False,
                    delete_after_seconds=0,
                    send_feedback=False,
                    resolved_from=PolicySource.REGISTRY_DEFAULT,
                ),
                feedback=None,
                redirect_channel_mention=None,
            )

        subsystem_name, subsystem_meta = found
        visible = await get_visible_subsystems(ctx)

        if subsystem_name in visible:
            return CommandPolicy(
                allowed=True,
                cleanup=CleanupPolicy(
                    delete_message=False,
                    delete_after_seconds=0,
                    send_feedback=False,
                    resolved_from=PolicySource.REGISTRY_DEFAULT,
                ),
                feedback=None,
                redirect_channel_mention=None,
            )

        # Blocked — build cleanup + feedback
        cleanup = await _resolve_cleanup_overrides(ctx)
        guild = ctx.member.guild if ctx.member else None
        redirect = _find_redirect_channel(guild, subsystem_meta)

        send_fb = cleanup.send_feedback and _should_send_feedback(
            ctx.channel_id or 0, subsystem_name
        )
        feedback = _build_feedback(subsystem_meta, redirect) if send_fb else None

        return CommandPolicy(
            allowed=False,
            cleanup=cleanup,
            feedback=feedback,
            redirect_channel_mention=redirect,
        )


# ---------------------------------------------------------------------------
# Public API — bulk resolution
# ---------------------------------------------------------------------------


async def resolve_all_subsystem_visibility(
    ctx: GovernanceContext,
) -> dict[str, bool]:
    """All subsystems with resolved enabled state. Single-trip through resolve_visibility."""
    result = await resolve_visibility(ctx)
    return {name: (name in result.visible_subsystems) for name in SUBSYSTEMS}


async def resolve_all_capabilities(ctx: GovernanceContext) -> dict[str, bool]:
    """All capabilities with resolved allowed state."""
    from utils.subsystem_registry import CAPABILITY_TO_SUBSYSTEM

    visible = await get_visible_subsystems(ctx)
    return {
        cap: (subsystem in visible)
        for cap, subsystem in CAPABILITY_TO_SUBSYSTEM.items()
    }


# ---------------------------------------------------------------------------
# Public API — effective state (single subsystem)
# ---------------------------------------------------------------------------


async def resolve_subsystem_state(
    ctx: GovernanceContext, subsystem_name: str
) -> SubsystemEffectiveState:
    """Complete resolved state for one subsystem. Powers /why, admin diagnostics."""
    vis = await resolve_visibility(ctx)
    cleanup = await resolve_cleanup_policy(ctx)

    state = (
        SubsystemState.ENABLED
        if subsystem_name in vis.visible_subsystems
        else SubsystemState.DISABLED
    )
    trace = vis.traces.get(
        subsystem_name,
        ResolutionTrace(
            subsystem=subsystem_name,
            checked_scopes=[],
            matched_scope=None,
            dependency_blocks=[],
            final_state=state,
        ),
    )
    source = vis.resolved_from.get(subsystem_name, PolicySource.REGISTRY_DEFAULT)

    return SubsystemEffectiveState(
        name=subsystem_name,
        state=trace.final_state,
        visibility_source=source,
        execution_allowed=subsystem_name in vis.visible_subsystems,
        execution_source=source,
        dependency_blocks=trace.dependency_blocks,
        cleanup_policy=cleanup,
        trace=trace,
    )


# ---------------------------------------------------------------------------
# Public API — governance snapshot
# ---------------------------------------------------------------------------


async def build_governance_snapshot(ctx: GovernanceContext) -> GovernanceSnapshot:
    """Complete governance state for a context.
    Powers dashboards, /why, AI reasoning, diagnostics.
    """
    vis = await resolve_visibility(ctx)
    cleanup = await resolve_cleanup_policy(ctx)
    cap_map = await resolve_all_capabilities(ctx)

    all_names = set(SUBSYSTEMS.keys())
    denied = all_names - vis.visible_subsystems
    dep_blocks: dict[str, list[str]] = {}
    for name, trace in vis.traces.items():
        if trace.dependency_blocks:
            dep_blocks[name] = trace.dependency_blocks

    return GovernanceSnapshot(
        visible_subsystems=vis.visible_subsystems,
        denied_subsystems=denied,
        dependency_blocks=dep_blocks,
        cleanup_policy=cleanup,
        member_tier=vis.member_tier,
        scope_provenance=vis.resolved_from,
        capability_map=cap_map,
        registry_version=REGISTRY_VERSION,
        registry_schema_version=REGISTRY_SCHEMA_VERSION,
    )


# ---------------------------------------------------------------------------
# Public API — health diagnostics
# ---------------------------------------------------------------------------


async def run_governance_healthcheck(guild_id: int) -> GovernanceHealthReport:
    """Check for orphan overrides, stale versions, and invalid configs."""
    known_subsystems = set(SUBSYSTEMS.keys())
    rows = await db.get_all_visibility_for_guild(guild_id)
    orphans = [
        {
            "scope_type": r["scope_type"],
            "scope_id": r["scope_id"],
            "subsystem": r["subsystem"],
        }
        for r in rows
        if r["subsystem"] not in known_subsystems
    ]

    stored = await db.get_setting(
        guild_id, settings_keys.GOVERNANCE_VERSION, default="0"
    )
    stale = [guild_id] if int(stored) < REGISTRY_VERSION else []

    summary = (
        f"{len(orphans)} orphan override(s), " f"{len(stale)} stale version guild(s)"
    )
    return GovernanceHealthReport(
        orphan_overrides=orphans,
        stale_version_guilds=stale,
        invalid_cleanup_configs=[],
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Public API — governance writes (all cogs must route through here)
# ---------------------------------------------------------------------------


async def set_subsystem_visibility(
    ctx: GovernanceContext,
    scope_type: str,
    scope_id: int,
    subsystem: str,
    enabled: bool | None,
) -> None:
    """Set a subsystem visibility override. enabled=None clears the override (inherit)."""
    await db.set_subsystem_visibility(
        ctx.guild_id, scope_type, scope_id, subsystem, enabled
    )
    invalidate_guild_cache(ctx.guild_id)
    await _emit_governance_event(
        EVT_VISIBILITY_CHANGED,
        {
            "guild_id": ctx.guild_id,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "subsystem": subsystem,
            "enabled": enabled,
        },
    )


async def set_cleanup_policy_for_scope(
    ctx: GovernanceContext,
    scope_type: str,
    scope_id: int,
    delete_invalid_commands: bool = True,
    delete_failed_commands: bool = True,
    delete_after_seconds: int = 5,
) -> None:
    await db.set_cleanup_policy(
        ctx.guild_id,
        scope_type,
        scope_id,
        delete_invalid_commands=delete_invalid_commands,
        delete_failed_commands=delete_failed_commands,
        delete_after_seconds=delete_after_seconds,
    )
    invalidate_guild_cache(ctx.guild_id)
    await _emit_governance_event(
        EVT_CLEANUP_CHANGED,
        {
            "guild_id": ctx.guild_id,
            "scope_type": scope_type,
            "scope_id": scope_id,
        },
    )


# ---------------------------------------------------------------------------
# Governance version management
# ---------------------------------------------------------------------------


async def check_governance_version(guild_id: int) -> None:
    """Check and upgrade governance version for a guild if needed."""
    stored = await db.get_setting(
        guild_id, settings_keys.GOVERNANCE_VERSION, default="0"
    )
    if int(stored) < REGISTRY_VERSION:
        await _run_governance_upgrade(guild_id, from_version=int(stored))


async def _run_governance_upgrade(guild_id: int, from_version: int) -> None:
    logger.info(
        "governance upgrade guild=%d from v%d to v%d",
        guild_id,
        from_version,
        REGISTRY_VERSION,
    )
    await db.set_setting(
        guild_id, settings_keys.GOVERNANCE_VERSION, str(REGISTRY_VERSION)
    )


# ---------------------------------------------------------------------------
# Internal event hook
# ---------------------------------------------------------------------------


async def _emit_governance_event(event_name: str, payload: dict) -> None:
    """Internal hook. Currently DEBUG-logs only.
    Future: route to core.events.EventBus — do NOT inline analytics here.
    governance_service must not become an analytics service.
    """
    logger.debug("governance_event %s %s", event_name, payload)
    # Future: await event_bus.publish(event_name, payload)
