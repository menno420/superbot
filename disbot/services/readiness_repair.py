"""Readiness repair previews + apply — Phase 9d / Track 2 PR 6.

Turns a stream of :class:`ResourceHealthFinding` records from
:mod:`services.resource_health` into actionable
:class:`RepairPreview` records, and provides an ``apply_repair``
function that routes accepted previews through the existing mutation
pipelines.

Design
------
* **Read at preview time, write at apply time.** ``build_previews``
  is pure; ``apply_repair`` is the only call that triggers a
  pipeline write.
* **No new mutation surface.** Every write goes through an existing
  service: :mod:`services.binding_mutation`,
  :mod:`services.settings_mutation`, or
  :mod:`services.resource_provisioning`. That preserves auditing /
  cache invalidation / event emission for free.
* **No destructive deletes.** v1 has no "delete this channel /
  role" action. ``clear_stale_binding`` only NULLs the
  ``subsystem_bindings`` row; the underlying Discord resource is
  untouched.
* **Owner-gated creates.** ``create_*`` actions require
  ``actor_id == guild_owner_id``. The Track 4 setup-access service
  will eventually replace the inline check; until then the caller
  passes ``guild_owner_id`` explicitly.
* **Track-6 automation placeholder.** ``create_automation_rule``
  exists in the type system but apply is a no-op until Track 6's
  automation pipeline ships.

Public surface
--------------
* :class:`RepairPreview` — frozen dataclass.
* :class:`RepairResult` — frozen dataclass returned by
  :func:`apply_repair`.
* :func:`build_previews` — finding-stream → preview-tuple.
* :func:`apply_repair` — preview → result (writes via pipelines).
* ``REPAIR_ACTIONS`` — frozenset of legal action tokens.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from services.resource_health import (
    HIERARCHY_BLOCKED,
    MISSING,
    NOT_CONFIGURED,
    PERMISSION_BLOCKED,
    STALE_BINDING,
    UNBOUND,
    WRONG_TYPE,
    ResourceHealthFinding,
)

if TYPE_CHECKING:
    import discord

logger = logging.getLogger("bot.services.readiness_repair")

# Repair action tokens.
BIND_EXISTING_CHANNEL = "bind_existing_channel"
BIND_EXISTING_ROLE = "bind_existing_role"
CLEAR_STALE_BINDING = "clear_stale_binding"
CREATE_MISSING_CHANNEL = "create_missing_channel"
CREATE_MISSING_ROLE = "create_missing_role"
ENABLE_LOGGING = "enable_logging"
OPEN_SETTINGS_EDITOR = "open_settings_editor"
OPEN_PERMISSIONS_HINT = "open_permissions_hint"
CREATE_AUTOMATION_RULE = "create_automation_rule"

REPAIR_ACTIONS: frozenset[str] = frozenset(
    {
        BIND_EXISTING_CHANNEL,
        BIND_EXISTING_ROLE,
        CLEAR_STALE_BINDING,
        CREATE_MISSING_CHANNEL,
        CREATE_MISSING_ROLE,
        ENABLE_LOGGING,
        OPEN_SETTINGS_EDITOR,
        OPEN_PERMISSIONS_HINT,
        CREATE_AUTOMATION_RULE,
    },
)

# Outcomes returned by ``apply_repair``.
OUTCOME_OK = "ok"
OUTCOME_SKIPPED = "skipped"  # ``is_no_op`` previews
OUTCOME_UNAUTHORIZED = "unauthorized"
OUTCOME_NO_OP = "no_op"  # placeholder action (track-6 stubs)
OUTCOME_PIPELINE_ERROR = "pipeline_error"

OUTCOMES: frozenset[str] = frozenset(
    {
        OUTCOME_OK,
        OUTCOME_SKIPPED,
        OUTCOME_UNAUTHORIZED,
        OUTCOME_NO_OP,
        OUTCOME_PIPELINE_ERROR,
    },
)


@dataclass(frozen=True)
class RepairPreview:
    """One proposed repair for a single :class:`ResourceHealthFinding`."""

    action: str
    finding: ResourceHealthFinding
    description: str
    requires_owner: bool = False
    is_advisory: bool = False  # UI-redirect actions that do not write.
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.action not in REPAIR_ACTIONS:
            raise ValueError(
                f"unknown repair action {self.action!r}; "
                f"must be one of {sorted(REPAIR_ACTIONS)}",
            )


@dataclass(frozen=True)
class RepairResult:
    """Outcome of an :func:`apply_repair` call."""

    preview: RepairPreview
    outcome: str
    mutation_id: str | None = None
    error: str | None = None

    @property
    def applied(self) -> bool:
        """True iff a pipeline actually wrote something."""
        return self.outcome == OUTCOME_OK


# ---------------------------------------------------------------------------
# Preview generation
# ---------------------------------------------------------------------------


def build_previews(
    findings: Iterable[ResourceHealthFinding],
) -> tuple[RepairPreview, ...]:
    """Convert findings into a tuple of :class:`RepairPreview` records.

    Findings with no obvious automated repair (``ok`` / ``unknown``)
    are dropped. Findings with manual-only fixes
    (``permission_blocked`` / ``hierarchy_blocked``) get an advisory
    ``open_permissions_hint`` preview so the wizard can render a hint
    without offering a button.
    """
    previews: list[RepairPreview] = []
    for finding in findings:
        preview = _preview_for(finding)
        if preview is not None:
            previews.append(preview)
    return tuple(previews)


def _preview_for(finding: ResourceHealthFinding) -> RepairPreview | None:
    """Map one finding to one preview (or ``None`` to skip)."""
    if finding.status == STALE_BINDING:
        return RepairPreview(
            action=CLEAR_STALE_BINDING,
            finding=finding,
            description=(
                f"Clear stale binding {finding.subsystem}.{finding.binding_name}"
                f" (was → {finding.target_id})."
            ),
        )
    if finding.status in (UNBOUND, NOT_CONFIGURED, WRONG_TYPE):
        return RepairPreview(
            action=OPEN_SETTINGS_EDITOR,
            finding=finding,
            description=(
                f"Open the settings editor for "
                f"{finding.subsystem}.{finding.binding_name} so the operator "
                "can pick the right target."
            ),
            is_advisory=True,
        )
    if finding.status == MISSING:
        # ``create_*`` is owner-only; the wizard surfaces both options:
        # pick existing or create new. We default to the safer
        # open-editor preview; the UI may override by constructing a
        # ``CREATE_MISSING_*`` preview directly.
        return RepairPreview(
            action=OPEN_SETTINGS_EDITOR,
            finding=finding,
            description=(
                f"Bind {finding.subsystem}.{finding.binding_name} "
                "(required) — open the settings editor."
            ),
            is_advisory=True,
        )
    if finding.status in (PERMISSION_BLOCKED, HIERARCHY_BLOCKED):
        return RepairPreview(
            action=OPEN_PERMISSIONS_HINT,
            finding=finding,
            description=(
                f"Manual fix: {finding.message} Adjust Discord "
                "permissions / role hierarchy before re-running readiness."
            ),
            is_advisory=True,
        )
    return None


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


async def apply_repair(
    preview: RepairPreview,
    *,
    guild: discord.Guild,
    actor_id: int,
    guild_owner_id: int,
) -> RepairResult:
    """Apply ``preview`` via the appropriate mutation pipeline.

    Routing:

    * ``clear_stale_binding`` → :class:`BindingMutationPipeline.clear_binding`.
    * ``bind_existing_channel`` / ``bind_existing_role`` →
      :class:`BindingMutationPipeline.set_binding`.
    * ``create_missing_channel`` / ``create_missing_role`` →
      :class:`ResourceProvisioningPipeline.provision`.
    * ``enable_logging`` → :class:`SettingsMutationPipeline.set_value`
      (``logging.enabled`` → ``"true"``).
    * ``open_settings_editor`` / ``open_permissions_hint`` →
      no-op (``OUTCOME_SKIPPED``). These previews exist to drive UI
      navigation, not state changes.
    * ``create_automation_rule`` → no-op until Track 6 ships
      (``OUTCOME_NO_OP``).

    Owner gate: ``create_missing_*`` and ``create_automation_rule``
    refuse anything other than ``actor_id == guild_owner_id``.
    """
    if preview.is_advisory or preview.action in (
        OPEN_SETTINGS_EDITOR,
        OPEN_PERMISSIONS_HINT,
    ):
        return RepairResult(preview=preview, outcome=OUTCOME_SKIPPED)

    if preview.requires_owner and actor_id != guild_owner_id:
        return RepairResult(
            preview=preview,
            outcome=OUTCOME_UNAUTHORIZED,
            error=(
                f"action {preview.action!r} requires guild-owner authority "
                f"(actor_id={actor_id}, owner_id={guild_owner_id})."
            ),
        )

    handler = _APPLY_HANDLERS.get(preview.action)
    if handler is None:
        return RepairResult(
            preview=preview,
            outcome=OUTCOME_NO_OP,
            error=(
                f"no apply handler registered for action {preview.action!r}; "
                "this action is a placeholder for a future track."
            ),
        )

    try:
        mutation_id = await handler(preview, guild=guild, actor_id=actor_id)
    except Exception as exc:  # noqa: BLE001 — service boundary
        logger.exception(
            "readiness_repair: apply failed for action=%s (subsystem=%s, binding=%s).",
            preview.action,
            preview.finding.subsystem,
            preview.finding.binding_name,
        )
        return RepairResult(
            preview=preview,
            outcome=OUTCOME_PIPELINE_ERROR,
            error=f"{type(exc).__name__}: {exc}",
        )

    return RepairResult(
        preview=preview,
        outcome=OUTCOME_OK,
        mutation_id=mutation_id,
    )


# ---------------------------------------------------------------------------
# Per-action handlers
# ---------------------------------------------------------------------------


async def _apply_clear_stale_binding(
    preview: RepairPreview,
    *,
    guild: discord.Guild,
    actor_id: int,
) -> str:
    from core.runtime.subsystem_schema import BindingKind, get_schema
    from services.binding_mutation import BindingMutationPipeline

    schema = get_schema(preview.finding.subsystem)
    if schema is None:
        raise ValueError(
            f"no SubsystemSchema registered for "
            f"{preview.finding.subsystem!r}; cannot clear binding.",
        )
    kind = preview.finding.kind
    if not isinstance(kind, BindingKind):
        raise TypeError(
            f"preview.finding.kind must be BindingKind, got {type(kind).__name__}",
        )
    actor = _bridge_actor(guild=guild, actor_id=actor_id)
    result = await BindingMutationPipeline().clear_binding(
        guild,
        preview.finding.subsystem,
        preview.finding.binding_name,
        kind,
        actor,
    )
    return result.mutation_id


async def _apply_bind_existing(
    preview: RepairPreview,
    *,
    guild: discord.Guild,
    actor_id: int,
) -> str:
    from core.runtime.subsystem_schema import BindingKind
    from services.binding_mutation import BindingMutationPipeline

    target_id = preview.payload.get("target_id")
    if not isinstance(target_id, int):
        raise ValueError(
            "bind_existing previews require payload['target_id'] as int.",
        )
    kind = preview.finding.kind
    if not isinstance(kind, BindingKind):
        raise TypeError(
            f"preview.finding.kind must be BindingKind, got {type(kind).__name__}",
        )
    actor = _bridge_actor(guild=guild, actor_id=actor_id)
    result = await BindingMutationPipeline().set_binding(
        guild,
        preview.finding.subsystem,
        preview.finding.binding_name,
        kind,
        target_id,
        actor,
    )
    return result.mutation_id


async def _apply_create_missing(
    preview: RepairPreview,
    *,
    guild: discord.Guild,
    actor_id: int,
) -> str:
    from services.resource_provisioning import (
        ProvisioningRequest,
        ResourceProvisioningPipeline,
    )

    mode = preview.payload.get("mode", "create")
    custom_name = preview.payload.get("custom_name")
    actor = _bridge_actor(guild=guild, actor_id=actor_id)
    request = ProvisioningRequest(
        subsystem=preview.finding.subsystem,
        binding_name=preview.finding.binding_name,
        mode=mode,
        custom_name=custom_name,
    )
    result = await ResourceProvisioningPipeline().provision(
        guild,
        request,
        actor,
        confirmed=True,
    )
    return result.mutation_id


async def _apply_enable_logging(
    preview: RepairPreview,
    *,
    guild: discord.Guild,
    actor_id: int,
) -> str:
    from services.settings_mutation import SettingsMutationPipeline

    actor = _bridge_actor(guild=guild, actor_id=actor_id)
    result = await SettingsMutationPipeline().set_value(
        guild,
        "logging",
        "enabled",
        True,
        actor,
    )
    return result.mutation_id


_APPLY_HANDLERS = {
    CLEAR_STALE_BINDING: _apply_clear_stale_binding,
    BIND_EXISTING_CHANNEL: _apply_bind_existing,
    BIND_EXISTING_ROLE: _apply_bind_existing,
    CREATE_MISSING_CHANNEL: _apply_create_missing,
    CREATE_MISSING_ROLE: _apply_create_missing,
    ENABLE_LOGGING: _apply_enable_logging,
    # CREATE_AUTOMATION_RULE intentionally absent → NO_OP outcome.
}


def _bridge_actor(*, guild: discord.Guild, actor_id: int) -> Any:
    """Look up the actor :class:`discord.Member` for pipeline calls.

    Pipelines accept ``discord.Member`` (mutation pipelines call
    ``actor.id`` for audit rows and the visibility-tier resolver
    walks ``actor.guild`` / ``actor.roles``). The repair flow gets
    its ``actor_id`` from the wizard layer (eventually
    :mod:`services.setup_access`); resolve it against the cache.
    """
    from core.runtime.guild_resources import resolve_member

    member = resolve_member(guild, actor_id)
    if member is None:
        raise ValueError(
            f"actor {actor_id!r} is not a member of guild {guild.id}; "
            "repair apply requires a guild-member actor context.",
        )
    return member


__all__ = [
    "BIND_EXISTING_CHANNEL",
    "BIND_EXISTING_ROLE",
    "CLEAR_STALE_BINDING",
    "CREATE_AUTOMATION_RULE",
    "CREATE_MISSING_CHANNEL",
    "CREATE_MISSING_ROLE",
    "ENABLE_LOGGING",
    "OPEN_PERMISSIONS_HINT",
    "OPEN_SETTINGS_EDITOR",
    "OUTCOMES",
    "OUTCOME_NO_OP",
    "OUTCOME_OK",
    "OUTCOME_PIPELINE_ERROR",
    "OUTCOME_SKIPPED",
    "OUTCOME_UNAUTHORIZED",
    "REPAIR_ACTIONS",
    "RepairPreview",
    "RepairResult",
    "apply_repair",
    "build_previews",
]
