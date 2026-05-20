"""Setup operation dispatcher — PR 1 of the setup-operations refactor.

:mod:`services.setup_operations` is the canonical setup/preset/repair
operation dispatcher.  All setup views, preset flows, and readiness-repair
actions must produce :class:`SetupOperation` batches and route them through
:func:`apply_operations` rather than calling individual mutation pipelines
directly.

Routing contract:

* Binding operations (``bind_*`` / ``clear_binding``) →
  :class:`services.binding_mutation.BindingMutationPipeline`.
* Setting operations (``set_setting``) →
  :class:`services.settings_mutation.SettingsMutationPipeline`.
* Resource creation (``create_channel`` / ``create_role`` /
  ``create_category``) →
  :class:`services.resource_provisioning.ResourceProvisioningPipeline`.
* Automation rule operations (``add_automation_rule`` /
  ``enable_automation_rule`` / ``disable_automation_rule``) →
  :class:`services.automation_mutation.AutomationMutationPipeline`.

No direct DB writes or Discord resource creation in this module —
every side effect routes through the canonical pipeline above it.

Final Review uses this dispatcher, not concrete mutation pipelines
directly; the view is orchestration-only.

Future preset and readiness-repair migration should produce
:class:`SetupOperation` batches and call :func:`apply_operations`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

logger = logging.getLogger("bot.services.setup_operations")

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

OperationKind = Literal[
    "bind_channel",
    "bind_role",
    "bind_category",
    "bind_thread",
    "bind_member",
    "clear_binding",
    "set_setting",
    "create_channel",
    "create_role",
    "create_category",
    "add_automation_rule",
    "enable_automation_rule",
    "disable_automation_rule",
]

OperationStatus = Literal["applied", "failed", "skipped", "not_yet_implemented"]

_KNOWN_KINDS: frozenset[str] = frozenset(
    {
        "bind_channel",
        "bind_role",
        "bind_category",
        "bind_thread",
        "bind_member",
        "clear_binding",
        "set_setting",
        "create_channel",
        "create_role",
        "create_category",
        "add_automation_rule",
        "enable_automation_rule",
        "disable_automation_rule",
    },
)

# bind_* kinds that route through BindingMutationPipeline.set_binding.
_BINDING_KINDS: frozenset[str] = frozenset(
    {"bind_channel", "bind_role", "bind_category", "bind_thread", "bind_member"},
)

# Adapter: SetupRecommendation.target_kind → OperationKind.
_TARGET_KIND_TO_OP_KIND: dict[str, str] = {
    "channel": "bind_channel",
    "role": "bind_role",
    "category": "bind_category",
    "thread": "bind_thread",
    "member": "bind_member",
}


@dataclass
class SetupOperation:
    """One typed setup action to be dispatched through the canonical pipelines.

    Only the fields relevant to ``kind`` need to be provided; all optional
    fields default to ``None``.  The dispatcher inspects ``kind`` first and
    reads only the fields required for that routing path.
    """

    kind: str  # OperationKind — validated at dispatch time
    subsystem: str
    binding_name: str | None = None
    setting_name: str | None = None
    target_id: int | None = None
    target_name: str | None = None
    target_kind: str | None = None
    value: Any = None
    resource_name: str | None = None
    resource_mode: str | None = None
    existing_id: int | None = None
    automation_rule_id: int | None = None
    automation_rule_name: str | None = None
    trigger_kind: str | None = None
    action_kind: str | None = None
    trigger_config: dict[str, Any] | None = None
    action_config: dict[str, Any] | None = None
    schedule: str | None = None
    timezone: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class SetupOperationResult:
    """Outcome of one :class:`SetupOperation` dispatch attempt.

    ``status`` is the canonical partition key for callers rendering results.
    ``mutation_id`` is set when the underlying pipeline returned one.
    ``error`` is set when ``status`` is ``"failed"`` or ``"not_yet_implemented"``.
    """

    status: str  # OperationStatus
    operation: SetupOperation
    label: str
    mutation_id: str | None = None
    error: str | None = None


@dataclass
class SetupOperationBatchResult:
    """Aggregated outcome of :func:`apply_operations`.

    ``results`` is the ordered list of per-operation outcomes.
    The four properties provide pre-partitioned views for embed rendering.
    """

    results: list[SetupOperationResult] = field(default_factory=list)

    @property
    def applied(self) -> list[SetupOperationResult]:
        return [r for r in self.results if r.status == "applied"]

    @property
    def failed(self) -> list[SetupOperationResult]:
        return [r for r in self.results if r.status == "failed"]

    @property
    def skipped(self) -> list[SetupOperationResult]:
        return [r for r in self.results if r.status == "skipped"]

    @property
    def not_yet_implemented(self) -> list[SetupOperationResult]:
        return [r for r in self.results if r.status == "not_yet_implemented"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_operation(op: SetupOperation) -> SetupOperationResult | None:
    """Return a ``not_yet_implemented`` result if ``op.kind`` is unknown.

    Returns ``None`` when the operation is dispatchable, allowing::

        if err := validate_operation(op):
            return err
    """
    if op.kind not in _KNOWN_KINDS:
        return SetupOperationResult(
            status="not_yet_implemented",
            operation=op,
            label=_label(op),
            error=f"operation kind {op.kind!r} is not a known OperationKind",
        )
    return None


def preview_operations(ops: list[SetupOperation]) -> list[SetupOperationResult]:
    """Return validation results for each operation without side effects.

    Validates each operation's kind only.  Operations with known kinds are
    optimistically reported as ``"applied"``; unknown kinds are
    ``"not_yet_implemented"``.  No DB reads are performed.
    """
    results: list[SetupOperationResult] = []
    for op in ops:
        err = validate_operation(op)
        if err is not None:
            results.append(err)
            continue
        results.append(
            SetupOperationResult(
                status="applied",
                operation=op,
                label=_label(op),
            ),
        )
    return results


async def apply_operations(
    ops: list[SetupOperation],
    *,
    guild: Any,
    actor: Any,
    actor_type: str = "user",
) -> SetupOperationBatchResult:
    """Dispatch each operation through the appropriate mutation pipeline.

    Failures are isolated per operation — one failure does not abort later
    operations.  Each :class:`SetupOperationResult` carries ``status``,
    ``label``, ``mutation_id`` (when the pipeline returned one), and
    ``error`` (when the pipeline raised or the kind is unsupported).

    Returns :class:`SetupOperationBatchResult` whose ``.applied``,
    ``.failed``, ``.skipped``, and ``.not_yet_implemented`` properties
    provide pre-partitioned views for embed rendering.
    """
    batch = SetupOperationBatchResult()
    for op in ops:
        result = await _dispatch_one(
            op,
            guild=guild,
            actor=actor,
            actor_type=actor_type,
        )
        batch.results.append(result)
    return batch


def operations_from_recommendations(
    recs: list[Any],  # list[services.setup_plan.SetupRecommendation]
) -> list[SetupOperation]:
    """Adapt :class:`services.setup_plan.SetupRecommendation` objects to
    :class:`SetupOperation` binding operations.

    The current recommendation model only produces binding proposals, so every
    ``SetupRecommendation`` maps to a ``bind_*`` operation.  Unknown
    ``target_kind`` values produce operations whose kind is not in
    ``_KNOWN_KINDS`` — the dispatcher will surface them as
    ``"not_yet_implemented"`` rather than silently dropping them.

    Future recommendation shapes (``set_setting``, ``create_resource``, etc.)
    will extend this adapter in follow-up PRs.
    """
    result: list[SetupOperation] = []
    for rec in recs:
        raw_kind = (rec.target_kind or "").lower()
        kind = _TARGET_KIND_TO_OP_KIND.get(
            raw_kind,
            # Unknown target_kind → synthetic kind that the dispatcher
            # will surface as not_yet_implemented, not silently dropped.
            f"bind_{raw_kind}" if raw_kind else "bind_unknown",
        )
        result.append(
            SetupOperation(
                kind=kind,
                subsystem=rec.subsystem,
                binding_name=rec.binding_name,
                target_id=rec.target_id,
                target_name=rec.target_name,
                target_kind=rec.target_kind,
                metadata={
                    "source": getattr(rec, "source", "unknown"),
                    "confidence": getattr(rec, "confidence", None),
                },
            ),
        )
    return result


# ---------------------------------------------------------------------------
# Internal dispatch
# ---------------------------------------------------------------------------


async def _dispatch_one(
    op: SetupOperation,
    *,
    guild: Any,
    actor: Any,
    actor_type: str,
) -> SetupOperationResult:
    """Route one operation to the correct pipeline.  Never raises."""
    label = _label(op)

    err = validate_operation(op)
    if err is not None:
        return err

    try:
        if op.kind in _BINDING_KINDS:
            return await _apply_binding(op, guild=guild, actor=actor, label=label)

        if op.kind == "clear_binding":
            return await _apply_clear_binding(op, guild=guild, actor=actor, label=label)

        if op.kind == "set_setting":
            return await _apply_set_setting(
                op,
                guild=guild,
                actor=actor,
                actor_type=actor_type,
                label=label,
            )

        if op.kind in ("create_channel", "create_role", "create_category"):
            return await _apply_resource_create(
                op,
                guild=guild,
                actor=actor,
                actor_type=actor_type,
                label=label,
            )

        if op.kind == "add_automation_rule":
            return await _apply_automation_create(
                op,
                guild=guild,
                actor=actor,
                label=label,
            )

        if op.kind in ("enable_automation_rule", "disable_automation_rule"):
            return await _apply_automation_set_enabled(
                op,
                guild=guild,
                actor=actor,
                label=label,
            )

        # Unreachable given validate_operation above, but explicit.
        return SetupOperationResult(
            status="not_yet_implemented",
            operation=op,
            label=label,
            error=f"operation kind {op.kind!r} has no dispatch path",
        )

    except Exception as exc:  # noqa: BLE001 — per-operation isolation boundary
        logger.exception(
            "setup_operations: failed to apply kind=%r label=%r",
            op.kind,
            label,
        )
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            error=f"{type(exc).__name__}: {exc}",
        )


async def _apply_binding(
    op: SetupOperation,
    *,
    guild: Any,
    actor: Any,
    label: str,
) -> SetupOperationResult:
    from core.runtime.subsystem_schema import BindingKind
    from services.binding_mutation import BindingMutationPipeline

    raw = (op.target_kind or "").lower()
    try:
        kind = BindingKind(raw)
    except ValueError:
        return SetupOperationResult(
            status="not_yet_implemented",
            operation=op,
            label=label,
            error=f"target_kind {raw!r} is not a known BindingKind",
        )

    result = await BindingMutationPipeline().set_binding(
        guild,
        op.subsystem,
        op.binding_name,  # type: ignore[arg-type]
        kind,
        op.target_id,  # type: ignore[arg-type]
        actor,
    )
    return SetupOperationResult(
        status="applied",
        operation=op,
        label=label,
        mutation_id=result.mutation_id,
    )


async def _apply_clear_binding(
    op: SetupOperation,
    *,
    guild: Any,
    actor: Any,
    label: str,
) -> SetupOperationResult:
    from core.runtime.subsystem_schema import BindingKind
    from services.binding_mutation import BindingMutationPipeline

    raw = (op.target_kind or "").lower()
    try:
        kind = BindingKind(raw)
    except ValueError:
        return SetupOperationResult(
            status="not_yet_implemented",
            operation=op,
            label=label,
            error=f"target_kind {raw!r} is not a known BindingKind for clear",
        )

    result = await BindingMutationPipeline().clear_binding(
        guild,
        op.subsystem,
        op.binding_name,  # type: ignore[arg-type]
        kind,
        actor,
    )
    return SetupOperationResult(
        status="applied",
        operation=op,
        label=label,
        mutation_id=result.mutation_id,
    )


async def _apply_set_setting(
    op: SetupOperation,
    *,
    guild: Any,
    actor: Any,
    actor_type: str,
    label: str,
) -> SetupOperationResult:
    from services.settings_mutation import SettingsMutationPipeline

    result = await SettingsMutationPipeline().set_value(
        guild,
        op.subsystem,
        op.setting_name,  # type: ignore[arg-type]
        op.value,
        actor,
        actor_type=actor_type,
    )
    return SetupOperationResult(
        status="applied",
        operation=op,
        label=label,
        mutation_id=result.mutation_id,
    )


async def _apply_resource_create(
    op: SetupOperation,
    *,
    guild: Any,
    actor: Any,
    actor_type: str,
    label: str,
) -> SetupOperationResult:
    from services.resource_provisioning import (
        ProvisioningRequest,
        ResourceProvisioningPipeline,
    )

    mode = op.resource_mode or (
        "use_existing" if op.existing_id is not None else "create"
    )
    request = ProvisioningRequest(
        subsystem=op.subsystem,
        binding_name=op.binding_name or "",
        mode=mode,
        existing_id=op.existing_id,
        custom_name=op.resource_name,
    )
    result = await ResourceProvisioningPipeline().provision(
        guild,
        request,
        actor,
        confirmed=True,
        actor_type=actor_type,
    )
    return SetupOperationResult(
        status="applied",
        operation=op,
        label=label,
        mutation_id=result.mutation_id,
    )


async def _apply_automation_create(
    op: SetupOperation,
    *,
    guild: Any,
    actor: Any,
    label: str,
) -> SetupOperationResult:
    from services.automation_mutation import AutomationMutationPipeline

    result = await AutomationMutationPipeline().create_rule(
        guild_id=guild.id,
        guild_owner_id=guild.owner_id,
        name=op.automation_rule_name or "",
        trigger_kind=op.trigger_kind or "",
        action_kind=op.action_kind or "",
        trigger_config=op.trigger_config or {},
        action_config=op.action_config or {},
        schedule=op.schedule,
        timezone_str=op.timezone or "UTC",
        actor_id=getattr(actor, "id", None),
        actor_type="system",
    )
    return SetupOperationResult(
        status="applied",
        operation=op,
        label=label,
        mutation_id=result.mutation_id,
    )


async def _apply_automation_set_enabled(
    op: SetupOperation,
    *,
    guild: Any,
    actor: Any,
    label: str,
) -> SetupOperationResult:
    from services.automation_mutation import AutomationMutationPipeline

    enabled = op.kind == "enable_automation_rule"
    result = await AutomationMutationPipeline().set_enabled(
        guild_id=guild.id,
        guild_owner_id=guild.owner_id,
        rule_id=op.automation_rule_id or 0,
        enabled=enabled,
        actor_id=getattr(actor, "id", None),
        actor_type="system",
    )
    return SetupOperationResult(
        status="applied",
        operation=op,
        label=label,
        mutation_id=result.mutation_id,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _label(op: SetupOperation) -> str:
    """Short human-readable description for logs and embed fields."""
    if op.kind in _BINDING_KINDS or op.kind == "clear_binding":
        target = op.target_name or (
            str(op.target_id) if op.target_id is not None else "?"
        )
        return f"{op.subsystem}.{op.binding_name} → {target}"
    if op.kind == "set_setting":
        return f"{op.subsystem}.{op.setting_name} = {op.value!r}"
    if op.kind in ("create_channel", "create_role", "create_category"):
        return (
            f"{op.kind}: {op.resource_name or '?'} "
            f"({op.subsystem}.{op.binding_name})"
        )
    if op.kind in (
        "add_automation_rule",
        "enable_automation_rule",
        "disable_automation_rule",
    ):
        name = op.automation_rule_name or (
            str(op.automation_rule_id) if op.automation_rule_id is not None else "?"
        )
        return f"{op.kind}: {name}"
    return f"{op.kind}: {op.subsystem}"


__all__ = [
    "OperationKind",
    "OperationStatus",
    "SetupOperation",
    "SetupOperationBatchResult",
    "SetupOperationResult",
    "apply_operations",
    "operations_from_recommendations",
    "preview_operations",
    "validate_operation",
]
