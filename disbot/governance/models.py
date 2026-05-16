"""Governance dataclasses, enums, and scope constants.

Layer: bottom — no imports from other governance submodules.

Phase 3.2 — Visibility / Execution / Exposure separation
─────────────────────────────────────────────────────────
The current implementation combines three logically distinct concepts.  Future
platform evolution should separate them explicitly:

  Visibility  — Should the subsystem appear in help menus and navigation UIs?
                Resolved by resolve_visibility() via scope chain.

  Execution   — May the member invoke the subsystem's commands and interactions?
                Currently derived from visibility, but independently overridable
                via capability_execution_overrides (resolve_execution()).

  Exposure    — Should the subsystem be discoverable at all (e.g. in public
                listings, diagnostics, or AI reasoning)?
                Currently conflated with visibility_mode == "internal".

Architectural direction: these three are intentionally unified in the current
implementation for simplicity.  As subsystem count and permission complexity
grow, they should be split into distinct resolution paths with independent DB
override tables.  The GovernanceContext and resolution interfaces are already
designed to support this split without breaking changes to callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import discord

# ---------------------------------------------------------------------------
# Scope resolution constants
# ---------------------------------------------------------------------------

SCOPE_PRIORITY: list[str] = ["thread", "channel", "category", "guild"]
SCOPE_PARENT: dict[str, str | None] = {
    "thread": "channel",  # ISSUE-016
    "channel": "category",
    "category": "guild",
    "guild": None,
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
    THREAD_OVERRIDE = "thread"
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
        thread_id = None
        if isinstance(channel, discord.Thread):
            thread_id = channel.id
            channel_id = channel.parent_id
            category_id = getattr(channel.parent, "category_id", None)
        else:
            channel_id = getattr(channel, "id", None)
            category_id = getattr(channel, "category_id", None)
        member = ctx.author
        return cls(
            guild_id=ctx.guild.id,
            channel_id=channel_id,
            category_id=category_id,
            thread_id=thread_id,
            member=member,
            role_ids={r.id for r in getattr(member, "roles", [])},
        )

    @classmethod
    def from_interaction(cls, interaction: discord.Interaction) -> "GovernanceContext":
        channel = interaction.channel
        thread_id = None
        if isinstance(channel, discord.Thread):
            thread_id = channel.id
            channel_id = channel.parent_id
            category_id = getattr(channel.parent, "category_id", None)
        else:
            channel_id = getattr(channel, "id", None)
            category_id = getattr(channel, "category_id", None)
        raw_user = interaction.user
        member = raw_user if isinstance(raw_user, discord.Member) else None
        return cls(
            guild_id=interaction.guild_id,
            channel_id=channel_id,
            category_id=category_id,
            thread_id=thread_id,
            member=member,
            role_ids={r.id for r in getattr(raw_user, "roles", [])},
        )

    @classmethod
    def from_message(cls, message: discord.Message) -> "GovernanceContext":
        channel = message.channel
        thread_id = None
        if isinstance(channel, discord.Thread):
            thread_id = channel.id
            channel_id = channel.parent_id
            category_id = getattr(channel.parent, "category_id", None)
        else:
            channel_id = getattr(channel, "id", None)
            category_id = getattr(channel, "category_id", None)
        raw_author = message.author
        member = raw_author if isinstance(raw_author, discord.Member) else None
        return cls(
            guild_id=message.guild.id if message.guild else 0,
            channel_id=channel_id,
            category_id=category_id,
            thread_id=thread_id,
            member=member,
            role_ids={r.id for r in getattr(raw_author, "roles", [])},
        )


@dataclass
class ResolutionTrace:
    subsystem: str
    checked_scopes: list[str]
    matched_scope: PolicySource | None
    dependency_blocks: list[str]
    final_state: SubsystemState
    request_id: str | None = None

    def to_dict(self) -> dict:
        d = {
            "subsystem": self.subsystem,
            "checked_scopes": sorted(self.checked_scopes),
            "matched_scope": self.matched_scope.value if self.matched_scope else None,
            "dependency_blocks": sorted(self.dependency_blocks),
            "final_state": self.final_state.value,
        }
        if self.request_id is not None:
            d["request_id"] = self.request_id
        return d


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


@dataclass
class GovernanceDiff:
    """Difference between two GovernanceSnapshots.

    Returned by diff_governance_snapshots(); powers change-review UI,
    audit log display, and AI-readable governance change summaries.
    """

    added_visible: set[str]
    removed_visible: set[str]
    changed_sources: dict[
        str, tuple[str, str]
    ]  # subsystem → (old, new) PolicySource value
    capability_changes: dict[str, tuple[bool, bool]]  # cap → (old, new)
    cleanup_changed: bool

    @property
    def is_empty(self) -> bool:
        return (
            not self.added_visible
            and not self.removed_visible
            and not self.changed_sources
            and not self.capability_changes
            and not self.cleanup_changed
        )

    def to_dict(self) -> dict:
        return {
            "added_visible": sorted(self.added_visible),
            "removed_visible": sorted(self.removed_visible),
            "changed_sources": {
                k: list(v) for k, v in sorted(self.changed_sources.items())
            },
            "capability_changes": {
                k: list(v) for k, v in sorted(self.capability_changes.items())
            },
            "cleanup_changed": self.cleanup_changed,
        }
