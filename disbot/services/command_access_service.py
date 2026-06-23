"""Command-access mutation service — PR-3.

The canonical write path for per-guild command-access policy.  Every
admin write (setup wizard, settings UI, future admin command) MUST go
through this module so the cache invalidation and audit emission
happen in lock-step with the DB commit.

Pattern follows the 6-step contract used by the lighter-weight
mutation services in this codebase (``services.command_routing``,
``services.role_automation``):

  1. Input validation        — mode literal / channel_id ints
  2. Read previous state     — for the audit row's ``prev_value``
  3. DB write                — via ``utils.db.command_access`` primitives
  4. Cache invalidation      — ``invalidate_command_access_policy`` runs
                                INLINE after the DB commit, BEFORE event
                                emission (cache consistency does not
                                depend on a subscriber)
  5. Audit emission          — ``audit.action_recorded`` via
                                ``services.audit_events.emit_audit_action``,
                                best-effort, never raises
  6. Return typed result     — frozen ``CommandAccessMutationResult``
                                carrying mutation_id for cross-pipeline
                                correlation

The richer per-pipeline events used by the binding / settings pipelines
(``settings.changed``, ``bindings.changed`` etc.) are deliberately NOT
added here yet — no subscriber needs them.  When one does, register a
new name in ``core.events_catalogue.KNOWN_EVENTS`` and emit it from
this module; the audit emit stays.

The resolver (``core.runtime.command_access.resolve_command_access``)
remains the read path.  This service never reads policy state for
admission decisions — it only reads to compute audit ``prev_value``.

Adds two composite operations on top of the four primitives:

* :func:`set_policy` — atomic mode + channel-list replace; the shape the
  setup wizard / settings UI uses to apply a whole-policy edit in one
  request.  Emits one audit event per actual change (so a switch from
  ``selected_channels`` mode with channels [100] to ``selected_channels``
  with channels [200] emits a channel-replace event but no mode event).
* :func:`get_policy_snapshot` — thin read-through to the typed accessor
  so admin UIs do not have to wire up their own cache discipline.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from services.audit_events import emit_audit_action
from utils.db import command_access as db
from utils.guild_config_accessors import (
    CommandAccessPolicySnapshot,
    get_command_access_policy,
    invalidate_command_access_policy,
)

logger = logging.getLogger("bot.services.command_access")


SUBSYSTEM = "command_access"

MutationType = Literal[
    "set_mode",
    "add_allowed_channel",
    "remove_allowed_channel",
    "replace_allowed_channels",
    "set_delete_blocked_commands",
]

_ALLOWED_ACTOR_TYPES: frozenset[str] = frozenset(
    {"admin", "system", "backfill"},
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class CommandAccessMutationError(Exception):
    """Base class for failures from this service."""


class InvalidCommandAccessModeError(CommandAccessMutationError):
    """Raised when the supplied mode is not recognised by the schema."""


class UnauthorizedCommandAccessActorError(CommandAccessMutationError):
    """Raised when ``actor_type`` is outside the allowed set.

    Entry-points (settings UI, wizard) are still responsible for
    checking the *user's* permission (Manage Guild, etc.); this is a
    last-line guard that the mutation isn't coming from an unexpected
    pipeline.
    """


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CommandAccessMutationResult:
    """Outcome of a single command-access mutation.

    ``audit_emitted`` is informational — DB state is always authoritative.
    """

    mutation_id: str
    guild_id: int
    mutation_type: MutationType
    prev_value: str | None
    new_value: str | None
    actor_id: int | None
    actor_type: str
    committed_at: datetime
    audit_emitted: bool


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _validate_mode(mode: str) -> None:
    if mode not in db.KNOWN_MODES:
        raise InvalidCommandAccessModeError(
            f"mode must be one of {sorted(db.KNOWN_MODES)}, got {mode!r}",
        )


def _validate_actor_type(actor_type: str) -> None:
    if actor_type not in _ALLOWED_ACTOR_TYPES:
        raise UnauthorizedCommandAccessActorError(
            f"actor_type must be one of {sorted(_ALLOWED_ACTOR_TYPES)}, "
            f"got {actor_type!r}",
        )


def _render_channels(channel_ids: Iterable[int]) -> str:
    """Render a stable, comparable string for an allowed-channel list."""
    return "[" + ",".join(str(c) for c in sorted(set(channel_ids))) + "]"


async def _emit_audit(
    *,
    mutation_id: str,
    mutation_type: MutationType,
    target: str,
    guild_id: int,
    prev_value: str | None,
    new_value: str | None,
    actor_id: int | None,
    actor_type: str,
    committed_at: datetime,
) -> bool:
    """Wrap the shared publisher so callers don't repeat the kwarg list."""
    return await emit_audit_action(
        mutation_id=mutation_id,
        subsystem=SUBSYSTEM,
        mutation_type=mutation_type,
        target=target,
        scope="guild",
        guild_id=guild_id,
        prev_value=prev_value,
        new_value=new_value,
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=committed_at,
    )


# ---------------------------------------------------------------------------
# Public read passthrough
# ---------------------------------------------------------------------------


async def get_policy_snapshot(guild_id: int) -> CommandAccessPolicySnapshot:
    """Return the cached policy snapshot for ``guild_id``.

    Thin passthrough to the typed accessor so admin UIs reach state
    through this module — the resolver remains the read path for
    admission, but admin UIs reading the SAME state through a different
    route (``utils.db.command_access`` direct) would skip the cache and
    risk divergence.
    """
    return await get_command_access_policy(guild_id)


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


async def set_mode(
    *,
    guild_id: int,
    mode: str,
    actor_id: int | None,
    actor_type: str = "admin",
) -> CommandAccessMutationResult:
    """Upsert the access mode for ``guild_id``.

    Channel allowlist rows are preserved across mode changes — switching
    from ``selected_channels`` to ``all_channels`` and back keeps the
    previously configured channels intact.  Callers that want a clean
    slate should follow with :func:`replace_allowed_channels`.
    """
    _validate_mode(mode)
    _validate_actor_type(actor_type)

    mutation_id = str(uuid.uuid4())
    prev_row = await db.get_policy(guild_id)
    prev_mode = str(prev_row["mode"]) if prev_row else None

    await db.set_mode(guild_id=guild_id, mode=mode, updated_by=actor_id)
    invalidate_command_access_policy(guild_id)

    committed_at = _now_utc()
    audit_emitted = await _emit_audit(
        mutation_id=mutation_id,
        mutation_type="set_mode",
        target="command_access:mode",
        guild_id=guild_id,
        prev_value=prev_mode,
        new_value=mode,
        actor_id=actor_id,
        actor_type=actor_type,
        committed_at=committed_at,
    )
    return CommandAccessMutationResult(
        mutation_id=mutation_id,
        guild_id=guild_id,
        mutation_type="set_mode",
        prev_value=prev_mode,
        new_value=mode,
        actor_id=actor_id,
        actor_type=actor_type,
        committed_at=committed_at,
        audit_emitted=audit_emitted,
    )


async def add_allowed_channel(
    *,
    guild_id: int,
    channel_id: int,
    actor_id: int | None,
    actor_type: str = "admin",
) -> CommandAccessMutationResult:
    """Add a single channel to the allowlist for ``guild_id``.

    Requires a policy row to already exist (FK).  The settings UI is
    expected to call :func:`set_mode` first (or use :func:`set_policy`
    to do both in one call).
    """
    _validate_actor_type(actor_type)
    if not isinstance(channel_id, int):
        raise TypeError(f"channel_id must be int, got {type(channel_id).__name__}")

    mutation_id = str(uuid.uuid4())
    prev_channels = await db.list_allowed_channels(guild_id)
    if channel_id in prev_channels:
        # Idempotent — DB primitive is also idempotent, but skipping the
        # audit emission keeps the audit log free of zero-effect rows.
        committed_at = _now_utc()
        return CommandAccessMutationResult(
            mutation_id=mutation_id,
            guild_id=guild_id,
            mutation_type="add_allowed_channel",
            prev_value=str(channel_id),
            new_value=str(channel_id),
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
            audit_emitted=False,
        )

    await db.add_allowed_channel(
        guild_id=guild_id,
        channel_id=channel_id,
        created_by=actor_id,
    )
    invalidate_command_access_policy(guild_id)

    committed_at = _now_utc()
    audit_emitted = await _emit_audit(
        mutation_id=mutation_id,
        mutation_type="add_allowed_channel",
        target=f"command_access:channel:{channel_id}",
        guild_id=guild_id,
        prev_value=None,
        new_value=str(channel_id),
        actor_id=actor_id,
        actor_type=actor_type,
        committed_at=committed_at,
    )
    return CommandAccessMutationResult(
        mutation_id=mutation_id,
        guild_id=guild_id,
        mutation_type="add_allowed_channel",
        prev_value=None,
        new_value=str(channel_id),
        actor_id=actor_id,
        actor_type=actor_type,
        committed_at=committed_at,
        audit_emitted=audit_emitted,
    )


async def remove_allowed_channel(
    *,
    guild_id: int,
    channel_id: int,
    actor_id: int | None,
    actor_type: str = "admin",
) -> CommandAccessMutationResult:
    """Remove a single channel from the allowlist for ``guild_id``."""
    _validate_actor_type(actor_type)
    if not isinstance(channel_id, int):
        raise TypeError(f"channel_id must be int, got {type(channel_id).__name__}")

    mutation_id = str(uuid.uuid4())
    prev_channels = await db.list_allowed_channels(guild_id)
    if channel_id not in prev_channels:
        # Idempotent — same rationale as add: no audit row for no-op.
        committed_at = _now_utc()
        return CommandAccessMutationResult(
            mutation_id=mutation_id,
            guild_id=guild_id,
            mutation_type="remove_allowed_channel",
            prev_value=None,
            new_value=None,
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
            audit_emitted=False,
        )

    await db.remove_allowed_channel(guild_id=guild_id, channel_id=channel_id)
    invalidate_command_access_policy(guild_id)

    committed_at = _now_utc()
    audit_emitted = await _emit_audit(
        mutation_id=mutation_id,
        mutation_type="remove_allowed_channel",
        target=f"command_access:channel:{channel_id}",
        guild_id=guild_id,
        prev_value=str(channel_id),
        new_value=None,
        actor_id=actor_id,
        actor_type=actor_type,
        committed_at=committed_at,
    )
    return CommandAccessMutationResult(
        mutation_id=mutation_id,
        guild_id=guild_id,
        mutation_type="remove_allowed_channel",
        prev_value=str(channel_id),
        new_value=None,
        actor_id=actor_id,
        actor_type=actor_type,
        committed_at=committed_at,
        audit_emitted=audit_emitted,
    )


async def replace_allowed_channels(
    *,
    guild_id: int,
    channel_ids: Iterable[int],
    actor_id: int | None,
    actor_type: str = "admin",
) -> CommandAccessMutationResult:
    """Atomic bulk replace of the allowed-channel list for ``guild_id``.

    Wraps :func:`utils.db.command_access.replace_allowed_channels`,
    invalidates the cache, and emits a single audit row with the
    before/after channel lists as comparable strings.  Skips the audit
    emission when prev == new (true no-op).
    """
    _validate_actor_type(actor_type)
    desired = sorted({int(cid) for cid in channel_ids})

    mutation_id = str(uuid.uuid4())
    prev_channels = await db.list_allowed_channels(guild_id)
    prev_rendered = _render_channels(prev_channels)
    new_rendered = _render_channels(desired)

    if prev_rendered == new_rendered:
        committed_at = _now_utc()
        return CommandAccessMutationResult(
            mutation_id=mutation_id,
            guild_id=guild_id,
            mutation_type="replace_allowed_channels",
            prev_value=prev_rendered,
            new_value=new_rendered,
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
            audit_emitted=False,
        )

    await db.replace_allowed_channels(
        guild_id=guild_id,
        channel_ids=desired,
        created_by=actor_id,
    )
    invalidate_command_access_policy(guild_id)

    committed_at = _now_utc()
    audit_emitted = await _emit_audit(
        mutation_id=mutation_id,
        mutation_type="replace_allowed_channels",
        target="command_access:channels",
        guild_id=guild_id,
        prev_value=prev_rendered,
        new_value=new_rendered,
        actor_id=actor_id,
        actor_type=actor_type,
        committed_at=committed_at,
    )
    return CommandAccessMutationResult(
        mutation_id=mutation_id,
        guild_id=guild_id,
        mutation_type="replace_allowed_channels",
        prev_value=prev_rendered,
        new_value=new_rendered,
        actor_id=actor_id,
        actor_type=actor_type,
        committed_at=committed_at,
        audit_emitted=audit_emitted,
    )


async def set_delete_blocked_commands(
    *,
    guild_id: int,
    enabled: bool,
    actor_id: int | None,
    actor_type: str = "admin",
) -> CommandAccessMutationResult:
    """Set the ``delete_blocked_commands`` toggle for ``guild_id``.

    When ON, a command-style message typed in a channel where Command
    Access denies it is auto-deleted on sight (with a brief notice) by
    the cleanup auto-mod path, instead of being silently ignored.
    Skips the audit emission when the value is unchanged (true no-op).
    """
    _validate_actor_type(actor_type)

    mutation_id = str(uuid.uuid4())
    prev_row = await db.get_policy(guild_id)
    prev_enabled = bool(prev_row["delete_blocked_commands"]) if prev_row else False
    new_enabled = bool(enabled)

    if prev_enabled == new_enabled:
        committed_at = _now_utc()
        return CommandAccessMutationResult(
            mutation_id=mutation_id,
            guild_id=guild_id,
            mutation_type="set_delete_blocked_commands",
            prev_value=str(prev_enabled),
            new_value=str(new_enabled),
            actor_id=actor_id,
            actor_type=actor_type,
            committed_at=committed_at,
            audit_emitted=False,
        )

    await db.set_delete_blocked_commands(
        guild_id=guild_id,
        enabled=new_enabled,
        updated_by=actor_id,
    )
    invalidate_command_access_policy(guild_id)

    committed_at = _now_utc()
    audit_emitted = await _emit_audit(
        mutation_id=mutation_id,
        mutation_type="set_delete_blocked_commands",
        target="command_access:delete_blocked_commands",
        guild_id=guild_id,
        prev_value=str(prev_enabled),
        new_value=str(new_enabled),
        actor_id=actor_id,
        actor_type=actor_type,
        committed_at=committed_at,
    )
    return CommandAccessMutationResult(
        mutation_id=mutation_id,
        guild_id=guild_id,
        mutation_type="set_delete_blocked_commands",
        prev_value=str(prev_enabled),
        new_value=str(new_enabled),
        actor_id=actor_id,
        actor_type=actor_type,
        committed_at=committed_at,
        audit_emitted=audit_emitted,
    )


# ---------------------------------------------------------------------------
# Composite
# ---------------------------------------------------------------------------


async def set_policy(
    *,
    guild_id: int,
    mode: str,
    channel_ids: Iterable[int] | None,
    actor_id: int | None,
    actor_type: str = "admin",
) -> list[CommandAccessMutationResult]:
    """Apply a whole-policy edit in the canonical order.

    Mode is upserted first so the FK on the channel rows is satisfied,
    then the channel list is replaced atomically.  Each underlying
    mutation runs through its own primitive (and so emits its own audit
    row when it actually changes anything), keeping the audit trail
    granular.

    ``channel_ids=None`` leaves the channel list untouched — useful for
    the settings-UI "change mode only" path.  Pass ``[]`` to clear the
    list explicitly.

    Returns the list of underlying results in execution order
    (``[set_mode_result]`` or ``[set_mode_result, replace_result]``) so
    callers can introspect what actually changed.
    """
    results: list[CommandAccessMutationResult] = [
        await set_mode(
            guild_id=guild_id,
            mode=mode,
            actor_id=actor_id,
            actor_type=actor_type,
        ),
    ]
    if channel_ids is not None:
        results.append(
            await replace_allowed_channels(
                guild_id=guild_id,
                channel_ids=channel_ids,
                actor_id=actor_id,
                actor_type=actor_type,
            ),
        )
    return results


__all__ = [
    "SUBSYSTEM",
    "CommandAccessMutationError",
    "CommandAccessMutationResult",
    "InvalidCommandAccessModeError",
    "MutationType",
    "UnauthorizedCommandAccessActorError",
    "add_allowed_channel",
    "get_policy_snapshot",
    "remove_allowed_channel",
    "replace_allowed_channels",
    "set_delete_blocked_commands",
    "set_mode",
    "set_policy",
]
