"""Cleanup-policy operator service: diagnostics, dry-run preview, audited apply.

Backend for the dedicated cleanup panel (server-management PR9).  Three
read/preview/apply entry points, all presets-only — every write maps to the
three ``cleanup_policies`` columns via :mod:`services.cleanup_levels` and goes
through the unchanged :func:`governance.writes.set_cleanup_policy_for_scope`
pipeline (DB row + governance audit row + ``audit.action_recorded`` +
``EVT_CLEANUP_CHANGED`` + ``EVT_CACHE_INVALIDATED`` in one transaction).

* :func:`collect_cleanup_diagnostics` — read-only inheritance/health report:
  every stored policy named back to its level, with stale-scope detection
  (channel/category deleted) and ineffective-row detection (a legacy guild row
  keyed by something other than ``guild_id`` is never read by the resolver).
* :func:`preview_cleanup_change` — side-effect-free dry-run: what a scope
  currently resolves to (via the real resolver, so preview == runtime) and what
  it would resolve to after the change.  Emits nothing, writes nothing.
* :func:`apply_cleanup_change` — the audited apply through the pipeline.

Layer: services → governance + utils (no views/cogs).  The resolver is reused,
never reimplemented, so the preview can never drift from runtime behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass

import discord

from governance.cleanup import resolve_cleanup_policy
from governance.models import CleanupPolicy, GovernanceContext, PolicySource
from governance.writes import (
    remove_cleanup_policy_for_scope,
    set_cleanup_policy_for_scope,
)
from services.cleanup_levels import (
    cleanup_scope_id,
    columns_for_level,
    known_level_names,
    level_for_columns,
)
from utils.db import governance as gov_db

# Cleanup scopes the resolver honours (RC-5: no thread scope).
CLEANUP_SCOPE_TYPES: frozenset[str] = frozenset({"guild", "category", "channel"})

# Bounds for a custom (non-preset) ``delete_after_seconds`` value.  0 = delete
# immediately; the upper bound keeps the auto-delete timer sane (5 minutes).
MAX_DELETE_AFTER_SECONDS = 300

_SOURCE_FOR_SCOPE: dict[str, PolicySource] = {
    "guild": PolicySource.GUILD_OVERRIDE,
    "category": PolicySource.CATEGORY_OVERRIDE,
    "channel": PolicySource.CHANNEL_OVERRIDE,
}

CUSTOM_LEVEL_LABEL = "Custom"


# ---------------------------------------------------------------------------
# Read model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CleanupScopeRow:
    """One stored ``cleanup_policies`` row, named and health-checked."""

    scope_type: str
    scope_id: int
    level_name: str | None  # None → operator-tuned ("Custom")
    delete_invalid_commands: bool
    delete_failed_commands: bool
    delete_after_seconds: int
    policy_version: int
    target_label: str
    is_stale: bool  # channel/category no longer exists
    is_ineffective: bool  # guild row not keyed by guild_id → resolver never reads it

    @property
    def display_level(self) -> str:
        return self.level_name or CUSTOM_LEVEL_LABEL


@dataclass(frozen=True)
class CleanupDiagnostics:
    """Aggregated per-guild cleanup-policy health report."""

    guild_id: int
    rows: tuple[CleanupScopeRow, ...]
    level_counts: dict[str, int]

    @property
    def total(self) -> int:
        return len(self.rows)

    @property
    def stale_rows(self) -> tuple[CleanupScopeRow, ...]:
        return tuple(r for r in self.rows if r.is_stale)

    @property
    def ineffective_rows(self) -> tuple[CleanupScopeRow, ...]:
        return tuple(r for r in self.rows if r.is_ineffective)


def _target_label(
    guild: discord.Guild,
    scope_type: str,
    scope_id: int,
) -> tuple[str, bool]:
    """Return ``(label, is_stale)`` for a scope row."""
    if scope_type == "guild":
        return "Guild default", False
    channel = guild.get_channel(scope_id)
    if channel is None:
        return f"{scope_type} {scope_id} (deleted)", True
    if scope_type == "category":
        return f"Category {channel.name}", False
    return f"#{channel.name}", False


async def collect_cleanup_diagnostics(guild: discord.Guild) -> CleanupDiagnostics:
    """Read-only inheritance + health report for a guild's cleanup policies."""
    raw = await gov_db.get_all_cleanup_for_guild(guild.id)
    rows: list[CleanupScopeRow] = []
    level_counts: dict[str, int] = {}
    for r in raw:
        scope_type = r["scope_type"]
        scope_id = int(r["scope_id"])
        level_name = level_for_columns(
            delete_invalid_commands=r["delete_invalid_commands"],
            delete_failed_commands=r["delete_failed_commands"],
            delete_after_seconds=r["delete_after_seconds"],
        )
        label, is_stale = _target_label(guild, scope_type, scope_id)
        # A guild row keyed by anything other than guild_id (the legacy
        # scope_id=0 bug) is never read by the resolver — flag it so an
        # operator can re-apply or clean it up.
        is_ineffective = scope_type == "guild" and scope_id != guild.id
        row = CleanupScopeRow(
            scope_type=scope_type,
            scope_id=scope_id,
            level_name=level_name,
            delete_invalid_commands=r["delete_invalid_commands"],
            delete_failed_commands=r["delete_failed_commands"],
            delete_after_seconds=r["delete_after_seconds"],
            policy_version=int(r.get("policy_version", 1)),
            target_label=label,
            is_stale=is_stale,
            is_ineffective=is_ineffective,
        )
        rows.append(row)
        key = row.display_level
        level_counts[key] = level_counts.get(key, 0) + 1

    # Stable order: guild first, then category, then channel; by id within.
    order = {"guild": 0, "category": 1, "channel": 2}
    rows.sort(key=lambda r: (order.get(r.scope_type, 9), r.scope_id))
    return CleanupDiagnostics(
        guild_id=guild.id,
        rows=tuple(rows),
        level_counts=level_counts,
    )


# ---------------------------------------------------------------------------
# Dry-run preview
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CleanupPolicyPreview:
    """Side-effect-free preview of setting ``scope`` to ``level``."""

    scope_type: str
    scope_id: int
    target_label: str
    level: str  # preset name, or "Custom" for an operator-tuned policy
    new_delete_message: bool  # == delete_invalid_commands (drives resolution)
    new_delete_failed_commands: bool
    new_delete_after_seconds: int
    current: CleanupPolicy
    will_change: bool
    warnings: tuple[str, ...]

    @property
    def current_source(self) -> PolicySource:
        return self.current.resolved_from


def _resolve_ctx_for_scope(
    guild: discord.Guild,
    scope_type: str,
    scope_id: int,
) -> GovernanceContext:
    """Build the context the resolver needs to evaluate ``scope`` today."""
    if scope_type == "guild":
        return GovernanceContext(guild_id=guild.id)
    if scope_type == "category":
        return GovernanceContext(guild_id=guild.id, category_id=scope_id)
    channel = guild.get_channel(scope_id)
    category_id = getattr(channel, "category_id", None)
    return GovernanceContext(
        guild_id=guild.id,
        channel_id=scope_id,
        category_id=category_id,
    )


async def preview_cleanup_columns(
    guild: discord.Guild,
    scope_type: str,
    scope_id: int,
    *,
    delete_invalid_commands: bool,
    delete_failed_commands: bool,
    delete_after_seconds: int,
    level_label: str | None = None,
) -> CleanupPolicyPreview:
    """Dry-run preview for setting ``scope`` to explicit column values.

    Reuses the real :func:`resolve_cleanup_policy` for the *current* state so
    the preview matches runtime exactly.  Writes nothing, emits nothing.
    ``level_label`` is the display name (a preset name, else "Custom" by the
    matching preset or ``CUSTOM_LEVEL_LABEL``).
    """
    _validate_scope(scope_type)
    _validate_columns(delete_after_seconds)
    new_delete = bool(delete_invalid_commands)
    new_failed = bool(delete_failed_commands)
    new_after = int(delete_after_seconds)

    label_name = level_label or (
        level_for_columns(
            delete_invalid_commands=new_delete,
            delete_failed_commands=new_failed,
            delete_after_seconds=new_after,
        )
        or CUSTOM_LEVEL_LABEL
    )

    current = await resolve_cleanup_policy(
        _resolve_ctx_for_scope(guild, scope_type, scope_id),
    )

    this_source = _SOURCE_FOR_SCOPE[scope_type]
    effect_differs = (
        current.delete_message != new_delete
        or current.delete_after_seconds != new_after
    )
    pins_source = current.resolved_from is not this_source
    will_change = effect_differs or pins_source

    label, is_stale = _target_label(guild, scope_type, scope_id)
    warnings: list[str] = []
    if is_stale:
        warnings.append(
            f"This {scope_type} no longer exists in the server — the policy "
            "will be stored but never matched until it is recreated.",
        )
    if not effect_differs and pins_source:
        warnings.append(
            "Same effect as today, but this pins an explicit override on the "
            f"{scope_type} (currently inherited from "
            f"{current.resolved_from.value}).",
        )

    return CleanupPolicyPreview(
        scope_type=scope_type,
        scope_id=scope_id,
        target_label=label,
        level=label_name,
        new_delete_message=new_delete,
        new_delete_failed_commands=new_failed,
        new_delete_after_seconds=new_after,
        current=current,
        will_change=will_change,
        warnings=tuple(warnings),
    )


async def preview_cleanup_change(
    guild: discord.Guild,
    scope_type: str,
    scope_id: int,
    level: str,
) -> CleanupPolicyPreview:
    """Compute the dry-run preview for setting ``scope`` to a preset ``level``."""
    _validate(scope_type, level)
    cols = columns_for_level(level)
    return await preview_cleanup_columns(
        guild,
        scope_type,
        scope_id,
        delete_invalid_commands=bool(cols["delete_invalid_commands"]),
        delete_failed_commands=bool(cols["delete_failed_commands"]),
        delete_after_seconds=int(cols["delete_after_seconds"]),
        level_label=level,
    )


# ---------------------------------------------------------------------------
# Audited apply / remove
# ---------------------------------------------------------------------------


async def apply_cleanup_columns(
    guild: discord.Guild,
    member: discord.Member,
    scope_type: str,
    scope_id: int | None,
    *,
    delete_invalid_commands: bool,
    delete_failed_commands: bool,
    delete_after_seconds: int,
) -> None:
    """Persist explicit column values for ``scope`` via the pipeline (audited).

    The single apply seam for both presets and custom-tuned policies.  Guild
    scope is keyed by ``guild_id`` (see
    :func:`services.cleanup_levels.cleanup_scope_id`); the pipeline writes the
    row + governance audit + events in one transaction and enforces authority.
    """
    _validate_scope(scope_type)
    _validate_columns(delete_after_seconds)
    effective_id = cleanup_scope_id(scope_type, guild.id, scope_id)
    ctx = GovernanceContext(guild_id=guild.id, member=member)
    await set_cleanup_policy_for_scope(
        ctx,
        scope_type,
        effective_id,
        delete_invalid_commands=bool(delete_invalid_commands),
        delete_failed_commands=bool(delete_failed_commands),
        delete_after_seconds=int(delete_after_seconds),
    )


async def apply_cleanup_change(
    guild: discord.Guild,
    member: discord.Member,
    scope_type: str,
    scope_id: int | None,
    level: str,
) -> None:
    """Persist a preset ``level`` for ``scope`` (audited).  Thin wrapper over
    :func:`apply_cleanup_columns`.
    """
    _validate(scope_type, level)
    cols = columns_for_level(level)
    await apply_cleanup_columns(
        guild,
        member,
        scope_type,
        scope_id,
        delete_invalid_commands=bool(cols["delete_invalid_commands"]),
        delete_failed_commands=bool(cols["delete_failed_commands"]),
        delete_after_seconds=int(cols["delete_after_seconds"]),
    )


async def remove_cleanup_change(
    guild: discord.Guild,
    member: discord.Member,
    scope_type: str,
    scope_id: int,
) -> bool:
    """Delete one stored cleanup override for ``scope`` (audited).

    Keyed by the *literal* ``scope_id`` so a stale or legacy-keyed row (e.g. a
    guild row written at ``scope_id=0`` the resolver never reads) can be cleared
    from the panel — unlike apply, this does **not** remap guild scope to
    ``guild_id``.  Returns ``True`` if a row was removed.
    """
    _validate_scope(scope_type)
    ctx = GovernanceContext(guild_id=guild.id, member=member)
    return await remove_cleanup_policy_for_scope(ctx, scope_type, int(scope_id))


def _validate_scope(scope_type: str) -> None:
    if scope_type not in CLEANUP_SCOPE_TYPES:
        raise ValueError(
            f"cleanup scope_type {scope_type!r} is not one of "
            f"{sorted(CLEANUP_SCOPE_TYPES)} (threads inherit; RC-5)",
        )


def _validate_columns(delete_after_seconds: int) -> None:
    if not 0 <= int(delete_after_seconds) <= MAX_DELETE_AFTER_SECONDS:
        raise ValueError(
            f"delete_after_seconds must be between 0 and "
            f"{MAX_DELETE_AFTER_SECONDS} (got {delete_after_seconds!r})",
        )


def _validate(scope_type: str, level: str) -> None:
    _validate_scope(scope_type)
    if level not in known_level_names():
        raise ValueError(
            f"cleanup level {level!r} is not one of {sorted(known_level_names())}",
        )
