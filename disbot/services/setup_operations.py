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
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from services.setup_change_plan import ChangePlanEntry, ChangeValue

logger = logging.getLogger("bot.services.setup_operations")


# ---------------------------------------------------------------------------
# Single-flight apply lock
# ---------------------------------------------------------------------------
#
# Final Review is the wizard's only mutation gate.  This lock prevents
# two apply batches from running for the same guild at the same time
# (double-click on ``Apply staged setup``, or two authorised users
# pressing apply nearly simultaneously).  It is intentionally
# in-process — single-shard bot — and never awaits between the check
# and the add, so it is race-free under asyncio.  A distributed
# primitive would be needed if SuperBot grew to multiple shards.


class SetupApplyInProgressError(RuntimeError):
    """Raised by :func:`acquire_setup_apply_lock` when an apply batch
    for the same guild is already running.

    Callers (the Final Review view) catch this and surface an ephemeral
    "Setup apply is already in progress — wait for the result message"
    reply.
    """

    def __init__(self, guild_id: int) -> None:
        super().__init__(
            f"setup apply already in progress for guild_id={guild_id}",
        )
        self.guild_id = guild_id


_apply_inflight: set[int] = set()


@asynccontextmanager
async def acquire_setup_apply_lock(guild_id: int) -> AsyncIterator[None]:
    """Single-flight guard around the Final Review apply path.

    The check + add happen without an intervening ``await``, so under
    asyncio's cooperative scheduling the operation is atomic — a
    concurrent ``async with`` either sees the guild in the set and
    raises :class:`SetupApplyInProgressError`, or wins the slot and runs.

    UI button disabling stays as a UX courtesy; this lock is the
    actual mechanism.
    """
    if guild_id in _apply_inflight:
        raise SetupApplyInProgressError(guild_id)
    _apply_inflight.add(guild_id)
    try:
        yield
    finally:
        _apply_inflight.discard(guild_id)


def _reset_apply_inflight_for_tests() -> None:
    """Test-only helper: drop every tracked guild lock.

    Tests that share module state across cases must call this in a
    teardown to avoid one test's leaked guild id failing the next.
    Not part of the public API; do not call from production code.
    """
    _apply_inflight.clear()


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
    "set_cleanup_policy",
    "set_cog_routing",
    "set_role_threshold",
    "create_managed_role",
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
        # Per-feature op kinds.  ``set_cleanup_policy`` routes through
        # governance.writes.set_cleanup_policy_for_scope; ``set_cog_routing``
        # routes through services.command_routing.set_policy;
        # ``set_role_threshold`` routes through
        # services.role_automation.set_{time,xp}_threshold;
        # ``create_managed_role`` routes through
        # services.role_lifecycle_service.RoleLifecycleService (PR13 role
        # templates).  See the dispatch arms in this module.  Keep this set in
        # lockstep with utils.db.setup_draft._KNOWN_OP_KINDS and the
        # migration-059 CHECK (pinned by test_setup_draft_op_kind_parity.py).
        "set_cleanup_policy",
        "set_cog_routing",
        "set_role_threshold",
        "create_managed_role",
    },
)

# set_role_threshold sub-kinds carried on ``op.setting_name``.
_ROLE_THRESHOLD_KINDS: frozenset[str] = frozenset({"time", "xp"})

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

# A ``create`` recommendation maps to the create-and-bind provisioning op for
# its resource kind (the pipeline creates the resource, then binds it). Only
# these three kinds are creatable; anything else stays a binding op.
_TARGET_KIND_TO_CREATE_OP_KIND: dict[str, str] = {
    "channel": "create_channel",
    "role": "create_role",
    "category": "create_category",
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

    Kept as the sync fast path; consumers wanting a real current /
    proposed diff call :func:`preflight_operations` (PR-04a).
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


# ---------------------------------------------------------------------------
# PR-04a — Preflight (read-only ChangePlan diff)
# ---------------------------------------------------------------------------


import os  # noqa: E402

_PREFLIGHT_FLAG_ENV = "SETUP_PREFLIGHT_DIFF"


def is_preflight_enabled() -> bool:
    """Return ``True`` when the preflight diff feature is enabled.

    Reads the ``SETUP_PREFLIGHT_DIFF`` env var.  **PR-04b: default is
    now on** after the PR-04a canary.  Set ``SETUP_PREFLIGHT_DIFF=0``
    (or ``false`` / ``no`` / ``off``) to opt out and fall back to the
    validation-only :func:`preview_operations` path.

    Consumers like the Final Review embed call this helper to decide
    whether to invoke :func:`preflight_operations` for the
    current/proposed diff.
    """
    val = os.getenv(_PREFLIGHT_FLAG_ENV, "").strip().lower()
    return val not in ("0", "false", "no", "off")


def preflight_gate_state() -> dict[str, Any]:
    """Read-only visibility surface for the ``SETUP_PREFLIGHT_DIFF`` gate.

    Plan §D2: the preflight diff is a **safety / diagnostic** gate, kept
    deliberately **env-only** (not a DB-editable feature flag).  This
    helper lets diagnostics explain *why* preview behaviour changed
    without promoting the gate into the flag registry.  Returns the gate
    name, its effective state, ownership, the default, and the raw env
    value (``None`` when unset).
    """
    return {
        "name": _PREFLIGHT_FLAG_ENV,
        "enabled": is_preflight_enabled(),
        "ownership": "env-only",
        "default_enabled": True,
        "raw": os.getenv(_PREFLIGHT_FLAG_ENV),
    }


async def preflight_operations(
    ops: list[SetupOperation],
    *,
    guild: Any,
) -> list[ChangePlanEntry]:
    """Return one :class:`ChangePlanEntry` per operation.

    PR-04a: real current/proposed diff for the most common operation
    kinds (``bind_*`` / ``clear_binding``, ``set_setting``,
    ``set_cog_routing``).  Other kinds emit a ChangePlanEntry with
    ``preflight_skipped_reason="no_adapter"`` so the Final Review
    embed can label them ``"preflight unavailable"`` rather than
    silently dropping the op.

    **Read-only** by contract: adapters here must not write to the
    DB or call a mutation pipeline.  The
    ``tests/unit/invariants/test_setup_preflight_readonly.py``
    invariant enforces this at AST level.

    Failures in a single adapter are isolated — the entry gets a
    ``read_error`` string and the rest of the batch continues.  An
    unknown ``op.kind`` produces a no-adapter entry rather than
    raising.
    """
    from services.setup_change_plan import (
        ABSENT,
        UNKNOWN,
        ChangePlanEntry,
        ChangeValue,
    )

    entries: list[ChangePlanEntry] = []
    guild_id = getattr(guild, "id", None)
    for op in ops:
        meta = op.metadata or {}
        risk = meta.get("risk", "unknown") if isinstance(meta, dict) else "unknown"
        rollback = meta.get("rollback_note", "") if isinstance(meta, dict) else ""
        if risk not in ("low", "medium", "high", "unknown"):
            risk = "unknown"

        # Defaults — overwritten by per-kind adapters below.
        current: ChangeValue = UNKNOWN
        proposed: ChangeValue = UNKNOWN
        would_change = True
        read_error: str | None = None
        skipped_reason: str | None = None

        kind = op.kind
        if kind not in _KNOWN_KINDS:
            # Validation-time failure: render as no-adapter.
            skipped_reason = "unknown_op_kind"
            proposed = ChangeValue(kind="value", value=op.target_id or op.value)
        elif kind in _BINDING_KINDS:
            current, proposed, would_change, read_error = await _preflight_bind(
                op,
                guild_id,
            )
        elif kind == "clear_binding":
            (
                current,
                proposed,
                would_change,
                read_error,
            ) = await _preflight_clear_binding(
                op,
                guild_id,
            )
        elif kind == "set_setting":
            current, proposed, would_change, read_error = await _preflight_set_setting(
                op,
                guild_id,
            )
        elif kind == "set_cog_routing":
            (
                current,
                proposed,
                would_change,
                read_error,
            ) = await _preflight_set_cog_routing(
                op,
                guild_id,
            )
        elif kind == "set_role_threshold":
            # Needs the live guild (not just guild_id) for the read-only
            # bot-feasibility note (can the bot actually assign this role?).
            (
                current,
                proposed,
                would_change,
                read_error,
            ) = await _preflight_set_role_threshold(
                op,
                guild,
            )
        elif kind == "create_managed_role":
            # Needs the live guild for the read-only Manage-Roles note.
            (
                current,
                proposed,
                would_change,
                read_error,
            ) = await _preflight_create_managed_role(
                op,
                guild,
            )
        else:
            # Known kind without a v1 read adapter (create_*, automation,
            # cleanup_policy).  Render proposed value where available;
            # signal that the diff is not computed.
            skipped_reason = "no_adapter"
            current = ABSENT if kind.startswith("create_") else UNKNOWN
            proposed_val = (
                op.value if op.value is not None else op.target_id or op.target_name
            )
            proposed = ChangeValue(kind="value", value=proposed_val)

        entries.append(
            ChangePlanEntry(
                op=op,
                label=_label(op),
                current=current,
                proposed=proposed,
                would_change=would_change,
                risk=risk,
                rollback_note=rollback,
                read_error=read_error,
                preflight_skipped_reason=skipped_reason,
            ),
        )
    return entries


async def _preflight_bind(
    op: SetupOperation,
    guild_id: int | None,
) -> tuple[ChangeValue, ChangeValue, bool, str | None]:
    """Read the current binding row to diff against ``op``."""
    from services.setup_change_plan import ABSENT, UNKNOWN, ChangeValue

    if guild_id is None or not op.subsystem or not op.binding_name:
        return (
            UNKNOWN,
            ChangeValue(kind="value", value=op.target_id),
            True,
            "missing guild/subsystem/binding_name on op",
        )
    try:
        from utils.db import bindings as bindings_db

        row = await bindings_db.get_one(guild_id, op.subsystem, op.binding_name)
    except Exception as exc:  # noqa: BLE001 — preflight is fail-safe
        return (
            UNKNOWN,
            ChangeValue(kind="value", value=op.target_id),
            True,
            f"{type(exc).__name__}: {exc}",
        )
    current: ChangeValue
    if row is None:
        current = ABSENT
    else:
        current = ChangeValue(kind="value", value=row.get("target_id"))
    proposed = ChangeValue(kind="value", value=op.target_id)
    if current.kind != "value" or proposed.kind != "value":
        would_change = True
    else:
        would_change = current.value != proposed.value
    return current, proposed, would_change, None


async def _preflight_clear_binding(
    op: SetupOperation,
    guild_id: int | None,
) -> tuple[ChangeValue, ChangeValue, bool, str | None]:
    """Read the current binding row to determine whether clear is a no-op."""
    from services.setup_change_plan import ABSENT, UNKNOWN, ChangeValue

    if guild_id is None or not op.subsystem or not op.binding_name:
        return (UNKNOWN, ABSENT, True, "missing guild/subsystem/binding_name on op")
    try:
        from utils.db import bindings as bindings_db

        row = await bindings_db.get_one(guild_id, op.subsystem, op.binding_name)
    except Exception as exc:  # noqa: BLE001 — preflight is fail-safe
        return (UNKNOWN, ABSENT, True, f"{type(exc).__name__}: {exc}")
    if row is None:
        return (ABSENT, ABSENT, False, None)
    current = ChangeValue(kind="value", value=row.get("target_id"))
    return (current, ABSENT, True, None)


async def _preflight_set_setting(
    op: SetupOperation,
    guild_id: int | None,
) -> tuple[ChangeValue, ChangeValue, bool, str | None]:
    """Read the current setting value to diff against ``op.value``.

    Uses :func:`services.setup_change_plan.values_equivalent` for the
    diff so settings stored as TEXT in the DB compare correctly to the
    typed values the wizard stages (e.g. ``"true"`` vs ``True``,
    ``"100"`` vs ``int 100``, ``""`` vs ``None``).  Naive string
    comparison would either hide real mismatches or render false
    positives — see ``test_setup_change_plan.TestValuesEquivalent`` for
    the full equivalence table.
    """
    from services.setup_change_plan import UNKNOWN, ChangeValue, values_equivalent

    if guild_id is None or not op.subsystem or not op.setting_name:
        return (
            UNKNOWN,
            ChangeValue(kind="value", value=op.value),
            True,
            "missing guild/subsystem/setting_name on op",
        )
    try:
        from utils import db

        current_raw = await db.get_setting(
            guild_id,
            f"{op.subsystem}.{op.setting_name}",
        )
    except Exception as exc:  # noqa: BLE001 — preflight is fail-safe
        return (
            UNKNOWN,
            ChangeValue(kind="value", value=op.value),
            True,
            f"{type(exc).__name__}: {exc}",
        )
    current = ChangeValue(kind="value", value=current_raw)
    proposed = ChangeValue(kind="value", value=op.value)
    would_change = not values_equivalent(current_raw, op.value)
    return current, proposed, would_change, None


async def _preflight_set_cog_routing(
    op: SetupOperation,
    guild_id: int | None,
) -> tuple[ChangeValue, ChangeValue, bool, str | None]:
    """Read the current cog-routing policy for a given scope."""
    from services.setup_change_plan import UNKNOWN, ChangeValue

    if guild_id is None or not op.subsystem:
        return (
            UNKNOWN,
            ChangeValue(kind="value", value=op.value),
            True,
            "missing guild/subsystem on op",
        )
    proposed_val = bool(op.value) if op.value is not None else False
    proposed = ChangeValue(kind="value", value=proposed_val)
    try:
        from services import command_routing

        # The cog-routing scope is per-channel; the op carries the
        # scope target_id when present.  Without a target_id we read
        # the guild-level policy.
        current_val = await command_routing.is_cog_enabled(
            guild_id,
            op.subsystem,
            channel_id=op.target_id,
        )
    except Exception as exc:  # noqa: BLE001 — preflight is fail-safe
        return (
            UNKNOWN,
            proposed,
            True,
            f"{type(exc).__name__}: {exc}",
        )
    current = ChangeValue(kind="value", value=bool(current_val))
    would_change = bool(current_val) != proposed_val
    return current, proposed, would_change, None


async def _preflight_set_role_threshold(
    op: SetupOperation,
    guild: Any,
) -> tuple[ChangeValue, ChangeValue, bool, str | None]:
    """Read-only current/proposed diff for a role-threshold op + a bot-feasibility note.

    Two read-only signals, so Final Review is not blind to role tiers (the
    gap before this adapter — the op fell to ``no_adapter``):

    * **diff** — the role's current time/XP tier vs. the proposed one
      (id-first, so a renamed role is matched by id);
    * **feasibility** — a hint folded into the proposed display when the bot
      could not actually *assign* the role (missing / above the bot / no
      Manage Roles), surfacing the ``role_automation.check_preflight`` class
      of blocker at review time. The threshold write itself is benign config
      (assignment is separately guarded in ``role_automation.apply``); this is
      transparency, not a gate.

    **Read-only by contract** (``test_setup_preflight_readonly``): no DB write,
    no mutation pipeline — only ``get_role_thresholds`` (read), ``resolve_role``,
    and ``evaluate_role``.
    """
    from services.setup_change_plan import UNKNOWN, ChangeValue

    sub_kind = (op.setting_name or "").strip().lower()
    proposed = ChangeValue(kind="value", value=_fmt_threshold(sub_kind, op.value))
    guild_id = getattr(guild, "id", None)
    if guild_id is None or sub_kind not in ("time", "xp") or op.target_id is None:
        return (UNKNOWN, proposed, True, "missing guild/sub-kind/target on op")

    current: ChangeValue = UNKNOWN
    would_change = True
    try:
        from utils.db import roles as roles_db

        rows = await roles_db.get_role_thresholds(guild_id)
        row = next((r for r in rows if r.get("role_id") == op.target_id), None)
        if row is not None:
            cur = (
                row.get("days_required")
                if sub_kind == "time"
                else row.get(
                    "level_required",
                )
            )
            current = ChangeValue(
                kind="value",
                value=(_fmt_threshold(sub_kind, cur) if cur else None),
            )
            try:
                would_change = int(cur or 0) != int(op.value)
            except (TypeError, ValueError):
                would_change = True
    except Exception as exc:  # noqa: BLE001 — preflight is fail-safe
        return (UNKNOWN, proposed, True, f"{type(exc).__name__}: {exc}")

    # Bot-feasibility note (read-only): can the bot actually assign this role?
    try:
        from core.runtime import guild_resources as resources
        from utils.role_feasibility import (
            ABOVE_BOT,
            BOT_MISSING_MANAGE_ROLES,
            evaluate_role,
        )

        role = resources.resolve_role(guild, role_id=op.target_id)
        if role is None:
            note = "⚠ role missing — automation can't assign"
        else:
            code = evaluate_role(role, bot_member=getattr(guild, "me", None)).code
            note = {
                BOT_MISSING_MANAGE_ROLES: "⚠ bot lacks Manage Roles",
                ABOVE_BOT: "⚠ above bot's top role — automation can't assign",
            }.get(code, "")
        if note:
            proposed = ChangeValue(
                kind="value",
                value=f"{_fmt_threshold(sub_kind, op.value)}  {note}",
            )
    except Exception:  # noqa: BLE001 — the note is best-effort, never fatal
        pass

    return current, proposed, would_change, None


async def _preflight_create_managed_role(
    op: SetupOperation,
    guild: Any,
) -> tuple[ChangeValue, ChangeValue, bool, str | None]:
    """Read-only preview for a ``create_managed_role`` op.

    The role does not exist yet (``current = ABSENT``); the proposed value is a
    compact description of the role + any auto-role tier, with a Manage-Roles
    feasibility note folded in so Final Review is not blind to the case where
    the create would be blocked.  No DB read, no mutation — only
    ``guild.me.guild_permissions`` is inspected.
    """
    from services.setup_change_plan import ABSENT, ChangeValue

    name = (op.resource_name or "?").strip() or "?"
    spec = (op.metadata or {}).get("role_template") or {}
    bits = [f"@{name}"]
    if spec.get("hoist"):
        bits.append("hoisted")
    if spec.get("time_days"):
        bits.append(f"+{spec['time_days']}d tier")
    if spec.get("xp_level"):
        bits.append(f"+XP L{spec['xp_level']} tier")
    proposed_text = " · ".join(bits)

    note = ""
    try:
        me = getattr(guild, "me", None)
        perms = getattr(me, "guild_permissions", None)
        if not bool(getattr(perms, "manage_roles", False)):
            note = "  ⚠ bot lacks Manage Roles — creation will be blocked"
    except Exception:  # noqa: BLE001 — the note is best-effort, never fatal
        pass

    proposed = ChangeValue(kind="value", value=proposed_text + note)
    return (ABSENT, proposed, True, None)


async def _resolve_apply_actor_type(actor: Any, guild: Any, actor_type: str) -> str:
    """Resolve the effective ``actor_type`` for an apply batch (Q-0098).

    This seam is the **sole minter** of ``actor_type="setup_delegate"`` — the
    Final Review view never passes it (an AST fence,
    ``tests/unit/invariants/test_setup_delegate_actor_boundary.py``, forbids the
    literal outside this module).  Instead this function decides, re-verifying
    the delegation **live** so a stale view gate can never be trusted (the same
    fresh-session ``can_apply_setup`` re-check ``final_review._gate_apply``
    does):

    * Explicit non-``user`` callers (scripted ``system`` / ``backfill`` paths)
      pass through unchanged — only the human apply path is delegate-eligible.
    * The server **owner** or any **administrator** already clears the per-op
      administrator floor, so they write as ``"user"``.  Keeping them ``"user"``
      keeps the audit honest: a delegate write must stay distinguishable from an
      administrator write.
    * A non-admin member writes as ``"setup_delegate"`` **only** when a fresh
      :class:`~services.setup_session.SetupSession` still lists them in
      ``delegated_admins`` (``setup_access.can_apply_setup``).  Delegation lost
      since Final Review opened ⇒ stays ``"user"`` ⇒ the per-op administrator
      floor denies the write — exactly the intended live re-verification.

    On any ambiguity or error the original ``actor_type`` is returned — this
    function never escalates.  For the common owner case it is sync and does no
    DB read (``is_server_owner`` short-circuits before ``resume_session``).
    """
    if actor_type != "user":
        return actor_type
    if actor is None or guild is None:
        return actor_type
    try:
        from services import setup_access

        # Owner / administrator already satisfy the administrator floor; keep
        # the honest "user" (admin-tier) audit label and skip the session read.
        if setup_access.is_server_owner(actor) or setup_access.is_administrator(
            actor,
        ):
            return "user"
        from services import setup_session

        guild_id = getattr(guild, "id", None)
        if guild_id is None:
            return "user"
        session = await setup_session.resume_session(guild_id)
        if setup_access.can_apply_setup(actor, session):
            return "setup_delegate"
    except Exception:  # noqa: BLE001 — resolution never escalates; fall back
        logger.exception(
            "apply_operations: delegated-apply actor_type resolution failed; "
            "falling back to actor_type=%r (the per-op floor still governs)",
            actor_type,
        )
    return "user"


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

    Authority (Q-0098): the incoming ``actor_type`` is resolved through
    :func:`_resolve_apply_actor_type`, which is the only place a
    ``"setup_delegate"`` actor is minted — and only after re-verifying the live
    delegation.  The resolved type flows to the three capability-gated pipelines
    (binding / settings / resource), where a delegated apply is authorized at
    the floor (``governance.capability``) and audited as ``setup_delegate``.

    Returns :class:`SetupOperationBatchResult` whose ``.applied``,
    ``.failed``, ``.skipped``, and ``.not_yet_implemented`` properties
    provide pre-partitioned views for embed rendering.
    """
    effective_actor_type = await _resolve_apply_actor_type(actor, guild, actor_type)
    batch = SetupOperationBatchResult()
    for op in ops:
        result = await _dispatch_one(
            op,
            guild=guild,
            actor=actor,
            actor_type=effective_actor_type,
        )
        batch.results.append(result)
    return batch


def preset_operations_to_setup_operations(
    preset_ops: list[Any],  # list[services.automation_templates.PresetOperation]
    *,
    preset_slug: str,
) -> list[SetupOperation]:
    """Adapt :class:`services.automation_templates.PresetOperation` items
    to :class:`SetupOperation` records the wizard's draft store can hold.

    Each adapted op carries ``metadata.source = f"preset:{preset_slug}"``
    so the Final Review embed can group preset-staged ops together
    and the apply path can audit them with the right provenance.

    Mapping:

    * ``bind_channel`` — payload provides subsystem + binding_name;
      no target_id yet (the wizard's per-binding picker fills it).
    * ``create_channel`` — payload provides subsystem + binding_name
      + name; the wizard's resource picker confirms before apply.
    * ``create_role`` — payload provides name (subsystem set to "roles").
    * ``set_setting`` — payload provides subsystem + setting_name + value.
    * ``set_binding_target`` — payload provides subsystem + binding_name
      + target_id.  Adapts to a ``bind_channel`` op.
    * ``add_rule`` — payload provides template_slug; adapts to
      ``add_automation_rule`` with the slug as the rule name.

    Unknown preset kinds adapt to a SetupOperation whose ``kind`` is
    not in ``_KNOWN_KINDS``; the dispatcher will surface them as
    ``not_yet_implemented`` rather than silently dropping them.
    """
    result: list[SetupOperation] = []
    base_metadata: dict[str, str] = {
        "source": f"preset:{preset_slug}",
        "confidence": "high",
        "risk": "low",
        "reason": f"Operator chose preset {preset_slug!r}",
        "rollback_note": "",
    }

    for op in preset_ops:
        kind = getattr(op, "kind", None) or ""
        payload: dict[str, Any] = dict(getattr(op, "payload", {}) or {})
        description = getattr(op, "description", "") or ""
        metadata = dict(base_metadata)
        if description:
            metadata["reason"] = description

        if kind == "bind_channel":
            result.append(
                SetupOperation(
                    kind="bind_channel",
                    subsystem=payload.get("subsystem", ""),
                    binding_name=payload.get("binding_name"),
                    target_kind="channel",
                    metadata=metadata,
                ),
            )
            continue
        if kind == "set_binding_target":
            result.append(
                SetupOperation(
                    kind="bind_channel",
                    subsystem=payload.get("subsystem", ""),
                    binding_name=payload.get("binding_name"),
                    target_id=payload.get("target_id"),
                    target_kind=payload.get("target_kind", "channel"),
                    metadata=metadata,
                ),
            )
            continue
        if kind == "create_channel":
            metadata["risk"] = "medium"
            result.append(
                SetupOperation(
                    kind="create_channel",
                    subsystem=payload.get("subsystem", ""),
                    binding_name=payload.get("binding_name"),
                    resource_name=payload.get("name"),
                    resource_mode="create",
                    metadata=metadata,
                ),
            )
            continue
        if kind == "create_role":
            metadata["risk"] = "high"
            result.append(
                SetupOperation(
                    kind="create_role",
                    subsystem=payload.get("subsystem", "roles"),
                    resource_name=payload.get("name"),
                    resource_mode="create",
                    metadata=metadata,
                ),
            )
            continue
        if kind == "set_setting":
            result.append(
                SetupOperation(
                    kind="set_setting",
                    subsystem=payload.get("subsystem", ""),
                    setting_name=payload.get("setting_name"),
                    value=payload.get("value"),
                    metadata=metadata,
                ),
            )
            continue
        if kind == "add_rule":
            metadata["risk"] = "medium"
            result.append(
                SetupOperation(
                    kind="add_automation_rule",
                    subsystem="automation",
                    automation_rule_name=payload.get("template_slug"),
                    trigger_kind=payload.get("trigger_kind"),
                    action_kind=payload.get("action_kind"),
                    trigger_config=payload.get("trigger_config"),
                    action_config=payload.get("action_config"),
                    metadata=metadata,
                ),
            )
            continue

        # Unknown preset kind — preserve as-is for the dispatcher's
        # not_yet_implemented surface so it doesn't get silently dropped.
        result.append(
            SetupOperation(
                kind=f"preset_unknown:{kind}",
                subsystem=payload.get("subsystem", ""),
                metadata=metadata,
            ),
        )

    return result


def metadata_from_recommendation(rec: Any) -> dict[str, str]:
    """Map a :class:`services.setup_plan.SetupRecommendation` to the
    canonical metadata dict consumed by the wizard's draft store and
    render layer.

    Canonical keys: ``reason``, ``confidence``, ``source``, ``risk``,
    ``rollback_note``.

    Defaults:

    * ``reason`` — ``rec.reason`` if present, else empty string.
    * ``confidence`` — ``rec.confidence`` (high/medium/low).
    * ``source`` — ``rec.source`` (deterministic / ai_advisor /
      readiness_repair / etc.).  Empty source falls back to
      ``"deterministic"`` to match the recommendation model's default.
    * ``risk`` — ``"low"``.  Bindings carry low default risk because
      the canonical pipeline isolates failures and the operator
      reviewed each one before Final Review.
    * ``rollback_note`` — empty string for bindings (rebind to the
      previous target or clear).

    The helper is intentionally narrow — sections that build
    metadata for non-binding ops should populate the canonical keys
    themselves with appropriate risk / rollback values.
    """
    return {
        "reason": str(getattr(rec, "reason", "") or ""),
        "confidence": str(getattr(rec, "confidence", "medium") or "medium"),
        "source": str(getattr(rec, "source", "deterministic") or "deterministic"),
        "risk": "low",
        "rollback_note": "",
    }


def operations_from_recommendations(
    recs: list[Any],  # list[services.setup_plan.SetupRecommendation]
) -> list[SetupOperation]:
    """Adapt :class:`services.setup_plan.SetupRecommendation` objects to
    :class:`SetupOperation`s.

    A ``mode="bind"`` recommendation maps to a ``bind_*`` operation against an
    existing resource. A ``mode="create"`` recommendation maps to a
    ``create_<kind>`` operation (``resource_mode="create"``) — the provisioning
    pipeline creates the resource named ``target_name`` and then binds it to
    ``subsystem.binding_name`` in one audited step. Unknown ``target_kind``
    values produce operations whose kind is not in ``_KNOWN_KINDS`` — the
    dispatcher surfaces them as ``"not_yet_implemented"`` rather than silently
    dropping them.

    Future recommendation shapes (``set_setting``, …) will extend this adapter.
    """
    result: list[SetupOperation] = []
    for rec in recs:
        raw_kind = (rec.target_kind or "").lower()
        if getattr(rec, "mode", "bind") == "create":
            # Create-and-bind: the new resource has no id yet; its name rides
            # ``resource_name`` for the provisioning pipeline.
            kind = _TARGET_KIND_TO_CREATE_OP_KIND.get(
                raw_kind,
                f"create_{raw_kind}" if raw_kind else "create_unknown",
            )
            result.append(
                SetupOperation(
                    kind=kind,
                    subsystem=rec.subsystem,
                    binding_name=rec.binding_name,
                    target_kind=rec.target_kind,
                    resource_name=rec.target_name,
                    resource_mode="create",
                    metadata=metadata_from_recommendation(rec),
                ),
            )
            continue
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
                metadata=metadata_from_recommendation(rec),
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
            return await _apply_binding(
                op,
                guild=guild,
                actor=actor,
                actor_type=actor_type,
                label=label,
            )

        if op.kind == "clear_binding":
            return await _apply_clear_binding(
                op,
                guild=guild,
                actor=actor,
                actor_type=actor_type,
                label=label,
            )

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

        if op.kind == "set_cleanup_policy":
            return await _apply_set_cleanup_policy(
                op,
                guild=guild,
                actor=actor,
                label=label,
            )

        if op.kind == "set_cog_routing":
            return await _apply_set_cog_routing(
                op,
                guild=guild,
                actor=actor,
                label=label,
            )

        if op.kind == "set_role_threshold":
            return await _apply_set_role_threshold(
                op,
                guild=guild,
                actor=actor,
                label=label,
            )

        if op.kind == "create_managed_role":
            return await _apply_create_managed_role(
                op,
                guild=guild,
                actor=actor,
                actor_type=actor_type,
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
    actor_type: str,
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
        actor_type=actor_type,
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
    actor_type: str,
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
        actor_type=actor_type,
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
    """Route a ``create_*`` op through :class:`ResourceProvisioningPipeline`.

    The pipeline can return non-success outcomes — most importantly
    ``"binding_failed"``, where the resource was created or reused
    but the subsequent binding step failed.  Pre-Phase-0 this method
    returned ``"applied"`` regardless, which caused Final Review to
    clear the draft and mark the session complete after a half-done
    apply.  See ``services.resource_provisioning._ProvisioningOutcome``
    for the full list.

    Mapping: every ``ProvisioningResult.outcome != "success"`` becomes
    a ``failed`` :class:`SetupOperationResult`.  The error message
    carries the outcome name so the recovery embed can render a
    targeted hint.  This deliberately reuses the existing ``failed``
    status — adding a new ``OperationStatus`` value would force
    coordinated updates to :class:`SetupOperationBatchResult`,
    :class:`~views.setup.final_review.ApplySummary`, every renderer,
    and every existing test.
    """
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
    outcome = getattr(result, "outcome", None)
    if outcome != "success":
        # Surface the outcome so the recovery embed can suggest a
        # targeted next step (e.g. binding_failed → "rebind manually
        # or re-run setup").
        mutation_id = getattr(result, "mutation_id", None)
        logger.warning(
            "setup_operations: resource_create %s returned outcome=%r "
            "(mutation_id=%s) — marking failed",
            label,
            outcome,
            mutation_id,
        )
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            mutation_id=mutation_id,
            error=f"resource provisioning outcome={outcome!r}",
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
# Cleanup policy + cog routing dispatchers
# ---------------------------------------------------------------------------
#
# Both arms route through the existing canonical writers:
#
# * ``set_cleanup_policy`` → ``governance.writes.set_cleanup_policy_for_scope``
#   (atomic upsert + governance audit row + ``audit.action_recorded``
#   event, all in one transaction).
# * ``set_cog_routing`` → ``services.command_routing.set_policy``
#   (existing per-scope upsert primitive).  Routing rows do not yet
#   ship through a mutation pipeline; we emit ``audit.action_recorded``
#   here so the apply still surfaces in the audit channel.
#
# No direct DB writes from these helpers — every persistence call is
# delegated.

_CLEANUP_SCOPE_TYPES: frozenset[str] = frozenset({"guild", "category", "channel"})
_ROUTING_SCOPE_TYPES: frozenset[str] = frozenset({"guild", "category", "channel"})


def _coerce_routing_enabled(op: SetupOperation) -> bool:
    """Return the operator-chosen enabled flag for a ``set_cog_routing`` op.

    The wizard's cog-routing section stages the boolean as a string in
    ``op.metadata["enabled"]`` ("true" / "false") so the JSONB column
    in ``setup_draft_operations`` doesn't need a bespoke schema.  This
    helper handles the round-trip cleanly.
    """
    raw = (op.metadata or {}).get("enabled")
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        return raw.strip().lower() == "true"
    # Default to True so a drafting bug doesn't silently disable a cog.
    return True


async def _apply_set_cleanup_policy(
    op: SetupOperation,
    *,
    guild: Any,
    actor: Any,
    label: str,
) -> SetupOperationResult:
    """Persist a cleanup-policy draft via :mod:`governance.writes`.

    Translates the operator-facing level (``Off`` / ``Light`` /
    ``Standard`` / ``Strict``) to ``cleanup_policies`` columns via
    :mod:`services.cleanup_levels` and calls
    :func:`governance.writes.set_cleanup_policy_for_scope`, which
    handles the DB write, governance audit row, cache invalidation,
    and ``audit.action_recorded`` event in one transaction.
    """
    from governance.models import GovernanceContext
    from governance.writes import set_cleanup_policy_for_scope
    from services.cleanup_levels import (
        cleanup_scope_id,
        columns_for_level,
        known_level_names,
    )

    scope_kind = (op.target_kind or "").strip().lower()
    if scope_kind not in _CLEANUP_SCOPE_TYPES:
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            error=(
                f"set_cleanup_policy: target_kind {scope_kind!r} is not one "
                f"of {sorted(_CLEANUP_SCOPE_TYPES)}"
            ),
        )

    level = op.value if isinstance(op.value, str) else None
    if level is None or level not in known_level_names():
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            error=(
                f"set_cleanup_policy: level {op.value!r} is not one of "
                f"{sorted(known_level_names())}"
            ),
        )

    # Category/channel writes need a target_id snowflake.  Guild scope is keyed
    # by guild_id (NOT 0): the resolver looks up guild policy at
    # scope_id=guild_id, so a 0 here was a silent no-op — guild-default cleanup
    # never took effect.  cleanup_scope_id() is the single source of truth.
    if scope_kind != "guild" and op.target_id is None:
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            error=f"set_cleanup_policy: {scope_kind} scope requires target_id",
        )
    scope_id = cleanup_scope_id(scope_kind, guild.id, op.target_id)

    columns = columns_for_level(level)
    ctx = GovernanceContext(guild_id=guild.id, member=actor)
    await set_cleanup_policy_for_scope(
        ctx,
        scope_kind,
        scope_id,
        delete_invalid_commands=columns["delete_invalid_commands"],
        delete_failed_commands=columns["delete_failed_commands"],
        delete_after_seconds=columns["delete_after_seconds"],
    )
    return SetupOperationResult(
        status="applied",
        operation=op,
        label=label,
    )


async def _apply_set_cog_routing(
    op: SetupOperation,
    *,
    guild: Any,
    actor: Any,
    label: str,
) -> SetupOperationResult:
    """Persist a cog-routing draft via :mod:`services.command_routing`.

    Reads the enabled flag from ``op.metadata["enabled"]`` (the wizard
    section stages it as a "true"/"false" string), validates the scope,
    and hands off to :func:`services.command_routing.set_policy` — the
    canonical routing mutation owner, which performs the write, emits
    ``audit.action_recorded`` with the real previous value, and returns
    the typed result this arm consumes.  The dispatcher owns only
    draft-shape validation/coercion here, not mutation or audit.
    """
    from services import command_routing

    scope_kind = (op.target_kind or "").strip().lower()
    if scope_kind not in _ROUTING_SCOPE_TYPES:
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            error=(
                f"set_cog_routing: target_kind {scope_kind!r} is not one "
                f"of {sorted(_ROUTING_SCOPE_TYPES)}"
            ),
        )

    cog_name = op.value if isinstance(op.value, str) else None
    if not cog_name:
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            error="set_cog_routing: value must be the cog name (non-empty string)",
        )

    if scope_kind != "guild" and op.target_id is None:
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            error=f"set_cog_routing: {scope_kind} scope requires target_id",
        )

    enabled = _coerce_routing_enabled(op)
    scope_id = op.target_id if scope_kind != "guild" else None
    actor_id = getattr(actor, "id", None)

    result = await command_routing.set_policy(
        guild_id=guild.id,
        scope_type=scope_kind,
        scope_id=scope_id,
        cog_name=cog_name,
        enabled=enabled,
        actor_id=actor_id,
    )
    return SetupOperationResult(
        status="applied",
        operation=op,
        label=label,
        mutation_id=result.mutation_id,
    )


async def _apply_set_role_threshold(
    op: SetupOperation,
    *,
    guild: Any,
    actor: Any,
    label: str,
) -> SetupOperationResult:
    """Persist an auto-role threshold via :mod:`services.role_automation`.

    The threshold sub-kind (``"time"`` / ``"xp"``) rides ``op.setting_name``
    and the numeric value (days for time, level for xp) rides ``op.value``;
    ``op.target_id`` is the role id.  Routes through the audited
    ``role_automation.set_{time,xp}_threshold`` seam — a service, not a raw
    DB write — mirroring the cog-routing arm's no-pipeline pattern (the
    setup-operations invariant forbids a top-level ``utils.db`` import).
    """
    from services import role_automation

    sub_kind = (op.setting_name or "").strip().lower()
    if sub_kind not in _ROLE_THRESHOLD_KINDS:
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            error=(
                f"set_role_threshold: setting_name {op.setting_name!r} must be "
                f"one of {sorted(_ROLE_THRESHOLD_KINDS)}"
            ),
        )

    if op.target_id is None:
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            error="set_role_threshold: requires target_id (the role id)",
        )

    # Drafts round-trip values as strings; coerce back to int.
    try:
        value = int(op.value)
    except (TypeError, ValueError):
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            error=f"set_role_threshold: value {op.value!r} is not an integer",
        )
    if value <= 0:
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            error="set_role_threshold: value must be a positive integer",
        )

    # Resolve the role name id-first via the canonical resolver; the row is
    # keyed by role_name with role_id captured so a later rename does not
    # orphan the tier.
    from core.runtime import guild_resources as resources

    role = resources.resolve_role(guild, role_id=op.target_id)
    role_name = getattr(role, "name", None) or op.target_name
    if not role_name:
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            error="set_role_threshold: could not resolve the role name",
        )

    actor_id = getattr(actor, "id", None)
    if sub_kind == "time":
        mutation_id = await role_automation.set_time_threshold(
            guild_id=guild.id,
            role_id=op.target_id,
            role_name=role_name,
            days=value,
            actor_id=actor_id,
        )
    else:  # "xp"
        mutation_id = await role_automation.set_xp_threshold(
            guild_id=guild.id,
            role_id=op.target_id,
            role_name=role_name,
            level=value,
            actor_id=actor_id,
        )
    return SetupOperationResult(
        status="applied",
        operation=op,
        label=label,
        mutation_id=mutation_id,
    )


async def _apply_create_managed_role(
    op: SetupOperation,
    *,
    guild: Any,
    actor: Any,
    actor_type: str,
    label: str,
) -> SetupOperationResult:
    """Create a standalone operator role via :class:`RoleLifecycleService`.

    Role-template creation routes through the role lifecycle service — the
    audited owner of *manual* role create/edit/delete (server-management PR5),
    and an allowlisted ``guild.create_role`` caller — rather than
    :class:`ResourceProvisioningPipeline`, which owns *subsystem-bound*
    create-or-reuse.  A template role is an unbound operator label, so the
    lifecycle service is the right owner (and keeps this module free of any
    direct ``guild.create_*`` call, per ``test_setup_operations_invariants``).

    The role's cosmetic spec (name / colour / hoist / mentionable) and any
    optional auto-role tier ride ``op.metadata["role_template"]`` (built by
    :func:`services.setup_role_templates.suggestion_to_spec`).  When the suggestion
    carries a ``time_days`` / ``xp_level`` tier, the freshly-created role's id
    is threaded into the audited ``role_automation.set_{time,xp}_threshold``
    seam as a **best-effort companion**: a failed tier never undoes the
    already-created role (mirrors the moderation post-action cleanup pattern).
    """
    from services import setup_role_templates
    from services.lifecycle import contracts as lc
    from services.role_lifecycle_service import (
        RoleLifecycleRequest,
        RoleLifecycleService,
    )

    name = (op.resource_name or "").strip()
    if not name:
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            error="create_managed_role: requires resource_name (the role name)",
        )

    spec = (op.metadata or {}).get("role_template") or {}
    request = RoleLifecycleRequest(
        operation="create",
        name=name,
        color=setup_role_templates.parse_color(spec.get("color")),
        hoist=bool(spec.get("hoist")),
        mentionable=bool(spec.get("mentionable")),
        reason=f"setup role template ({spec.get('template_slug') or 'manual'})",
    )
    result = await RoleLifecycleService().apply(
        guild,
        request,
        actor,
        confirmed=True,
        actor_type=actor_type,
    )
    if result.outcome != lc.SUCCESS:
        return SetupOperationResult(
            status="failed",
            operation=op,
            label=label,
            mutation_id=result.mutation_id,
            error=f"role create outcome={result.outcome!r}: {result.first_error}",
        )

    new_role_id = result.steps[0].target_id if result.steps else None
    if new_role_id:
        # The tier needs the role id, which only exists post-create — so the
        # companion runs here, after the create succeeds.
        await _apply_template_role_tiers(
            guild=guild,
            role_id=new_role_id,
            role_name=name,
            spec=spec,
            actor=actor,
            label=label,
        )
    return SetupOperationResult(
        status="applied",
        operation=op,
        label=label,
        mutation_id=result.mutation_id,
    )


async def _apply_template_role_tiers(
    *,
    guild: Any,
    role_id: int,
    role_name: str,
    spec: dict[str, Any],
    actor: Any,
    label: str,
) -> None:
    """Best-effort auto-role tier companion for a created template role.

    Failure is logged but never raised: the role itself was created (the
    primary mutation), so a tier write that fails must not flip the op to
    ``failed`` — the operator can set the tier by hand in ``!roles``.
    """
    time_days = spec.get("time_days")
    xp_level = spec.get("xp_level")
    if not time_days and not xp_level:
        return
    from services import role_automation

    actor_id = getattr(actor, "id", None)
    try:
        if time_days:
            await role_automation.set_time_threshold(
                guild_id=guild.id,
                role_id=role_id,
                role_name=role_name,
                days=int(time_days),
                actor_id=actor_id,
            )
        if xp_level:
            await role_automation.set_xp_threshold(
                guild_id=guild.id,
                role_id=role_id,
                role_name=role_name,
                level=int(xp_level),
                actor_id=actor_id,
            )
    except Exception:
        logger.exception(
            "create_managed_role: auto-role tier companion failed "
            "(role_id=%s label=%r) — the role itself was created",
            role_id,
            label,
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
            f"{op.kind}: {op.resource_name or '?'} ({op.subsystem}.{op.binding_name})"
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
    if op.kind == "set_cleanup_policy":
        scope = op.target_kind or "?"
        scope_label = op.target_name or (
            str(op.target_id) if op.target_id is not None else "guild"
        )
        return f"cleanup.{scope}({scope_label}) = {op.value!r}"
    if op.kind == "set_cog_routing":
        scope = op.target_kind or "?"
        scope_label = op.target_name or (
            str(op.target_id) if op.target_id is not None else "guild"
        )
        enabled = _coerce_routing_enabled(op)
        flag = "enabled" if enabled else "disabled"
        return f"cog_routing.{scope}({scope_label}).{op.value!r} = {flag}"
    if op.kind == "set_role_threshold":
        sub_kind = op.setting_name or "?"
        role_label = op.target_name or (
            str(op.target_id) if op.target_id is not None else "?"
        )
        return (
            f"role_threshold.{sub_kind}({role_label}) = "
            f"{_fmt_threshold(sub_kind, op.value)}"
        )
    if op.kind == "create_managed_role":
        spec = (op.metadata or {}).get("role_template") or {}
        extra = ""
        if spec.get("time_days"):
            extra += f" +{spec['time_days']}d"
        if spec.get("xp_level"):
            extra += f" +L{spec['xp_level']}"
        return f"create role @{op.resource_name or '?'}{extra}"
    return f"{op.kind}: {op.subsystem}"


def _fmt_threshold(sub_kind: str, value: Any) -> str:
    """Human label for a role-threshold value: time → ``"7d"``, xp → ``"L10"``."""
    if sub_kind == "time":
        return f"{value}d"
    if sub_kind == "xp":
        return f"L{value}"
    return f"{value}"


__all__ = [
    "OperationKind",
    "OperationStatus",
    "SetupApplyInProgressError",
    "SetupOperation",
    "SetupOperationBatchResult",
    "SetupOperationResult",
    "acquire_setup_apply_lock",
    "apply_operations",
    "operations_from_recommendations",
    "preview_operations",
    "validate_operation",
]
