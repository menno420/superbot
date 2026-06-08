"""Setup diagnostics & repair — server-management PR12.

A **read-only** diagnostics layer that inspects a guild's
server-management configuration, classifies what is broken / stale /
unsafe / incomplete, explains each finding, and — for the safe,
deterministic cases — generates typed :class:`SetupOperation` repair
batches that Final Review (the wizard's only apply gate) dispatches
through the existing canonical mutation pipelines.

Ownership / boundaries (binding):

* **This module owns finding *detection orchestration*, *classification*,
  the *repairability decision*, and *repair-operation generation*.** It
  does **not** own mutation.  Every repair it produces is a
  :class:`services.setup_operations.SetupOperation`; this service never
  writes the DB, never creates a Discord resource, and never calls a
  mutation pipeline.  ``tests/unit/invariants/test_setup_diagnostics_readonly.py``
  pins the read-only contract at AST level.
* **It composes existing read-only detectors — it does not re-detect.**
  Binding health comes from :func:`services.resource_health.inspect`;
  role-threshold staleness from ``utils.db.roles`` + the shared pure
  :mod:`utils.role_feasibility`; moderator / trusted role config from
  :mod:`core.runtime.config_arbitration`; cleanup-policy health from
  :func:`services.cleanup_diagnostics.collect_cleanup_diagnostics`.
* **It is UI-agnostic.**  It returns a typed
  :class:`SetupDiagnosticsReport`; the setup wizard's *Diagnose & repair*
  section renders it and stages the repairs, and the future Server
  Management Hub (PR14) can render the same report without change — which
  is why the model lives in ``services/`` rather than in a view.

Stages the prompt's six-step model maps onto:

1. **Detection** — :func:`collect_setup_diagnostics` fans out to the
   ``_diagnose_*`` collectors, each wrapping one existing detector.
2. **Classification** — the ``_map_*`` helpers turn a raw detector verdict
   into a :class:`SetupDiagnosticFinding` with a severity.
3. **Repairability decision** — encoded on each finding's
   ``repairability``.
4. **Repair-operation generation** — repairable findings carry a
   ``repair_ops`` batch of :class:`SetupOperation`.
5. **Final Review staging** — the section appends the batch to the draft;
   Final Review applies it.  (Not this module's concern; it only
   produces the ops.)
6. **Apply-result rendering** — inherited for free: repairs are ordinary
   :class:`SetupOperation`s, so ``views/setup/final_review.py`` renders
   partial-apply outcomes the same way it does for every other op.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from services import resource_health
from services.setup_operations import SetupOperation

if TYPE_CHECKING:
    import discord

    from services.resource_health import ResourceHealthFinding

logger = logging.getLogger("bot.services.setup_diagnostics")


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

# Severity — how urgent / impactful a finding is.
SEV_BLOCKER = "blocker"  # setup cannot safely apply or continue
SEV_WARNING = "warning"  # usable but config is likely broken / incomplete
SEV_ADVISORY = "advisory"  # useful improvement or manual follow-up
SEV_INFO = "info"  # state explanation only

SEVERITIES: frozenset[str] = frozenset(
    {SEV_BLOCKER, SEV_WARNING, SEV_ADVISORY, SEV_INFO},
)

# Render / sort precedence — lower sorts first (most urgent on top).
_SEVERITY_ORDER: dict[str, int] = {
    SEV_BLOCKER: 0,
    SEV_WARNING: 1,
    SEV_ADVISORY: 2,
    SEV_INFO: 3,
}

# Repairability — whether and how a finding can be repaired.
REPAIR_AUTO = "auto_repairable"  # safe to stage automatically once selected
REPAIR_CONDITIONAL = "conditionally_repairable"  # needs a user choice / confirm
REPAIR_ADVISORY = "advisory_only"  # no automatic repair should be generated
REPAIR_BLOCKED = "blocked"  # cannot repair until an external issue is fixed

REPAIRABILITIES: frozenset[str] = frozenset(
    {REPAIR_AUTO, REPAIR_CONDITIONAL, REPAIR_ADVISORY, REPAIR_BLOCKED},
)


# ---------------------------------------------------------------------------
# Finding + report models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SetupDiagnosticFinding:
    """One typed diagnostic verdict about a guild's setup configuration.

    Notes on the model:

    * ``code`` is a **stable** snake_case identifier (e.g.
      ``"stale_channel_binding"``) so dashboards / tests can key on it
      without parsing prose.
    * ``repair_ops`` is the staged :class:`SetupOperation` batch — empty
      unless ``repairability == REPAIR_AUTO``.  The ops are not applied
      here; the section appends them to the draft and Final Review
      dispatches them.
    * ``advisory_note`` explains the manual follow-up when there is no
      safe automatic repair.
    * ``notes`` carries risk / permission / feasibility caveats the UI
      can surface verbatim.

    The dataclass is frozen for the same reason the other finding models
    in this codebase are (``ResourceHealthFinding``, ``RoleFeasibility``):
    a verdict is a value, not a mutable record.  It is intentionally not
    used as a set/dict key (``repair_ops`` holds mutable
    :class:`SetupOperation`s), so hashing it is not part of the contract.
    """

    code: str
    severity: str
    subsystem: str
    section_slug: str | None
    resource_type: str | None
    resource_id: int | None
    summary: str
    detail: str
    repairability: str
    repair_label: str = ""
    repair_ops: tuple[SetupOperation, ...] = ()
    advisory_note: str = ""
    notes: tuple[str, ...] = ()

    @property
    def is_auto_repairable(self) -> bool:
        """True when this finding carries a safe, ready-to-stage repair."""
        return self.repairability == REPAIR_AUTO and bool(self.repair_ops)


@dataclass(frozen=True)
class SetupDiagnosticsReport:
    """Aggregated, severity-sorted diagnostics snapshot for one guild.

    The properties give pre-partitioned views the renderer + the staging
    button consume so neither has to re-filter the tuple.
    """

    guild_id: int
    findings: tuple[SetupDiagnosticFinding, ...]

    @property
    def has_findings(self) -> bool:
        return bool(self.findings)

    @property
    def is_healthy(self) -> bool:
        """True when nothing needs attention (no warning/blocker/advisory).

        ``info`` findings are state explanations and do not count as
        "needs attention", mirroring ``resource_health``'s benign-info
        posture.
        """
        return not any(
            f.severity in (SEV_BLOCKER, SEV_WARNING, SEV_ADVISORY)
            for f in self.findings
        )

    @property
    def counts(self) -> dict[str, int]:
        """Finding count per severity (every severity present as a key)."""
        out = {sev: 0 for sev in (SEV_BLOCKER, SEV_WARNING, SEV_ADVISORY, SEV_INFO)}
        for f in self.findings:
            if f.severity in out:
                out[f.severity] += 1
        return out

    @property
    def repairable(self) -> tuple[SetupDiagnosticFinding, ...]:
        """Findings that carry a safe, ready-to-stage repair batch."""
        return tuple(f for f in self.findings if f.is_auto_repairable)

    @property
    def advisory(self) -> tuple[SetupDiagnosticFinding, ...]:
        """Findings with no automatic repair (manual follow-up / blocked)."""
        return tuple(f for f in self.findings if not f.is_auto_repairable)

    def by_severity(self, severity: str) -> tuple[SetupDiagnosticFinding, ...]:
        return tuple(f for f in self.findings if f.severity == severity)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def collect_setup_diagnostics(guild: discord.Guild) -> SetupDiagnosticsReport:
    """Inspect ``guild``'s server-management config; return a typed report.

    **Read-only.**  Fans out to the existing detectors, maps each verdict
    to a :class:`SetupDiagnosticFinding`, and sorts the result by
    ``(severity, subsystem, code)`` so the most urgent issues render
    first and the order is stable across calls.

    Each ``_diagnose_*`` collector is fail-safe: a detector that raises is
    logged and contributes no findings, so one broken collector can never
    blank the whole report.
    """
    findings: list[SetupDiagnosticFinding] = []
    for collector in (
        _diagnose_bindings,
        _diagnose_role_thresholds,
        _diagnose_moderation_roles,
        _diagnose_cleanup,
    ):
        try:
            findings.extend(await collector(guild))
        except Exception:
            logger.exception(
                "setup_diagnostics: collector %s raised; skipping it",
                collector.__name__,
            )

    findings.sort(
        key=lambda f: (_SEVERITY_ORDER.get(f.severity, 9), f.subsystem, f.code),
    )
    return SetupDiagnosticsReport(guild_id=guild.id, findings=tuple(findings))


def staged_repair_ops(
    findings: tuple[SetupDiagnosticFinding, ...] | list[SetupDiagnosticFinding],
) -> list[SetupOperation]:
    """Flatten every auto-repairable finding's batch into one op list.

    The order follows ``findings`` so the staged operations land in the
    same severity-sorted order the operator saw.  Advisory / conditional /
    blocked findings contribute nothing.
    """
    ops: list[SetupOperation] = []
    for f in findings:
        if f.is_auto_repairable:
            ops.extend(f.repair_ops)
    return ops


# ---------------------------------------------------------------------------
# Collector: bindings / channels (via services.resource_health)
# ---------------------------------------------------------------------------


async def _diagnose_bindings(
    guild: discord.Guild,
) -> list[SetupDiagnosticFinding]:
    """Map :func:`resource_health.inspect` verdicts to diagnostics.

    Healthy slots (``ok`` / ``not_configured``) contribute nothing — the
    report is a problem list, not an inventory (the readiness section
    already owns the full inventory).
    """
    try:
        verdicts = await resource_health.inspect(guild)
    except Exception:
        logger.exception("setup_diagnostics: resource_health.inspect failed")
        return []
    findings: list[SetupDiagnosticFinding] = []
    for v in verdicts:
        mapped = _map_binding_finding(v)
        if mapped is not None:
            findings.append(mapped)
    return findings


# Binding kinds whose re-bind home in the wizard is the Channels section.
_CHANNELISH_KINDS: frozenset[str] = frozenset({"channel", "category", "thread"})


def _binding_section(kind_value: str) -> str | None:
    """Section slug an operator would use to (re)bind this kind, or None."""
    return "channels" if kind_value in _CHANNELISH_KINDS else None


def _map_binding_finding(
    v: ResourceHealthFinding,
) -> SetupDiagnosticFinding | None:
    """Classify one :class:`ResourceHealthFinding`.

    Repairable cases (``stale_binding`` / ``wrong_type``) generate a
    single ``clear_binding`` :class:`SetupOperation` — the one binding
    repair that is always safe, deterministic, ID-free, and reversible
    (re-bind to a live resource).  Permission / hierarchy blockers stay
    ``blocked`` (the fix is a Discord-side change the bot must not and
    cannot make).  Missing / unbound slots stay advisory (the operator
    must pick the intended target — PR12 never guesses or auto-creates).
    """
    status = v.status
    kind_value = v.kind.value
    slot = f"{v.subsystem}.{v.binding_name}"

    if status in (resource_health.OK, resource_health.NOT_CONFIGURED):
        return None

    if status in (resource_health.STALE_BINDING, resource_health.WRONG_TYPE):
        stale = status == resource_health.STALE_BINDING
        summary = (
            f"`{slot}` points at a {kind_value} that no longer exists"
            if stale
            else f"`{slot}` is bound to the wrong resource type"
        )
        return SetupDiagnosticFinding(
            code="stale_binding" if stale else "wrong_type_binding",
            severity=SEV_WARNING,
            subsystem=v.subsystem,
            section_slug="diagnostics",
            resource_type=kind_value,
            resource_id=v.target_id,
            summary=summary,
            detail=v.message,
            repairability=REPAIR_AUTO,
            repair_label=f"Clear the dead `{slot}` binding",
            repair_ops=(_clear_binding_op(v),),
            notes=(
                "Clearing only removes the stale link — re-bind to a live "
                f"{kind_value} afterwards (Channels section).",
            ),
        )

    if status == resource_health.MISSING:
        return SetupDiagnosticFinding(
            code="missing_required_binding",
            severity=SEV_WARNING,
            subsystem=v.subsystem,
            section_slug=_binding_section(kind_value),
            resource_type=kind_value,
            resource_id=None,
            summary=f"Required binding `{slot}` is not set",
            detail=v.message,
            repairability=REPAIR_ADVISORY,
            advisory_note=(
                f"Bind a {kind_value} for `{slot}` in the "
                f"{_binding_section(kind_value) or 'relevant'} section — PR12 "
                "won't guess the target or auto-create it."
            ),
        )

    if status == resource_health.UNBOUND:
        return SetupDiagnosticFinding(
            code="unbound_binding",
            severity=SEV_ADVISORY,
            subsystem=v.subsystem,
            section_slug=_binding_section(kind_value),
            resource_type=kind_value,
            resource_id=None,
            summary=f"`{slot}` exists but points at no live resource",
            detail=v.message,
            repairability=REPAIR_ADVISORY,
            advisory_note=(
                f"Re-bind `{slot}` to a live {kind_value} in the "
                f"{_binding_section(kind_value) or 'relevant'} section, or "
                "leave it cleared."
            ),
        )

    if status == resource_health.PERMISSION_BLOCKED:
        return SetupDiagnosticFinding(
            code="binding_permission_blocked",
            severity=SEV_WARNING,
            subsystem=v.subsystem,
            section_slug=None,
            resource_type=kind_value,
            resource_id=v.target_id,
            summary=f"`{slot}` is bound but the bot lacks permission on it",
            detail=v.message,
            repairability=REPAIR_BLOCKED,
            advisory_note=(
                "Grant the bot the missing permission on that resource in "
                "Discord, then re-scan — setup can't grant Discord "
                "permissions to itself."
            ),
        )

    if status == resource_health.HIERARCHY_BLOCKED:
        return SetupDiagnosticFinding(
            code="binding_hierarchy_blocked",
            severity=SEV_WARNING,
            subsystem=v.subsystem,
            section_slug=None,
            resource_type=kind_value,
            resource_id=v.target_id,
            summary=f"`{slot}` is bound to a role above the bot's top role",
            detail=v.message,
            repairability=REPAIR_BLOCKED,
            advisory_note=(
                "Move the bot's role above the bound role in Server Settings → "
                "Roles, then re-scan — the bot can't reorder its own role and "
                "PR12 won't attempt it."
            ),
        )

    # status == UNKNOWN or any future BindingKind the inspector can't probe.
    return SetupDiagnosticFinding(
        code="binding_unknown_state",
        severity=SEV_INFO,
        subsystem=v.subsystem,
        section_slug=None,
        resource_type=kind_value,
        resource_id=v.target_id,
        summary=f"`{slot}` is in an unrecognised state",
        detail=v.message,
        repairability=REPAIR_ADVISORY,
        advisory_note="Inspect this binding manually; no automatic repair.",
    )


def _clear_binding_op(v: ResourceHealthFinding) -> SetupOperation:
    """Build the ``clear_binding`` repair op for a dead binding finding.

    The dispatcher (``services.setup_operations._apply_clear_binding``)
    reads only ``subsystem`` / ``binding_name`` / ``target_kind`` and
    routes through :class:`services.binding_mutation.BindingMutationPipeline`,
    so no ``target_id`` is needed.
    """
    kind_value = v.kind.value
    slot = f"{v.subsystem}.{v.binding_name}"
    return SetupOperation(
        kind="clear_binding",
        subsystem=v.subsystem,
        binding_name=v.binding_name,
        target_kind=kind_value,
        metadata={
            "source": "diagnostics_repair",
            "confidence": "high",
            "risk": "low",
            "reason": f"Clear the dead {slot} binding (points at a missing {kind_value})",
            "rollback_note": (
                f"Re-bind {slot} to a live {kind_value} in the Channels section."
            ),
        },
    )


# ---------------------------------------------------------------------------
# Collector: time / XP auto-role thresholds (via utils.db.roles + feasibility)
# ---------------------------------------------------------------------------


async def _diagnose_role_thresholds(
    guild: discord.Guild,
) -> list[SetupDiagnosticFinding]:
    """Flag auto-role tiers whose role is gone or that the bot can't assign.

    Stale references are advisory-only: there is no ``clear_role_threshold``
    SetupOperation kind in PR12, so the safe automatic repair would be
    PR13 work — instead the finding points the operator at ``!roles``
    (which already owns per-tier clearing).  A configured-but-unassignable
    tier is a Discord hierarchy / permission blocker the bot must not fix
    by reordering roles.
    """
    try:
        from core.runtime import guild_resources as resources
        from utils.db import roles as roles_db
        from utils.role_feasibility import (
            ABOVE_BOT,
            BOT_MISSING_MANAGE_ROLES,
            evaluate_role,
        )

        rows = await roles_db.get_role_thresholds(guild.id)
    except Exception:
        logger.exception("setup_diagnostics: role-threshold read failed")
        return []

    findings: list[SetupDiagnosticFinding] = []
    bot_member = getattr(guild, "me", None)
    for row in rows:
        role_id = row.get("role_id")
        role_name = row.get("display_name") or row.get("role_name") or "?"
        role = None
        if role_id:
            role = resources.resolve_role(guild, role_id=role_id)
        if role is None and row.get("role_name"):
            # Legacy name-only rows: resolve by exact name like the
            # automation resolver's fallback before declaring it stale.
            role = resources.resolve_role(guild, name=row.get("role_name"))

        if role is None:
            findings.append(
                SetupDiagnosticFinding(
                    code="stale_role_threshold",
                    severity=SEV_WARNING,
                    subsystem="roles",
                    section_slug="roles",
                    resource_type="role",
                    resource_id=role_id,
                    summary=(
                        f"Auto-role tier for `@{role_name}` references a role "
                        "that no longer exists"
                    ),
                    detail=(
                        "A time/XP threshold is configured for a role the bot "
                        "can no longer resolve (deleted or renamed beyond "
                        "recovery), so the tier never assigns."
                    ),
                    repairability=REPAIR_ADVISORY,
                    advisory_note=(
                        "Clear or re-point this tier in `!roles` (the role "
                        "panels own per-tier editing). PR12 has no automatic "
                        "threshold-clear operation."
                    ),
                ),
            )
            continue

        # Role resolves — is it actually assignable by the bot?
        if bot_member is not None:
            verdict = evaluate_role(role, bot_member=bot_member)
            if not verdict.ok and verdict.code in (
                ABOVE_BOT,
                BOT_MISSING_MANAGE_ROLES,
            ):
                findings.append(
                    SetupDiagnosticFinding(
                        code="role_threshold_unassignable",
                        severity=SEV_WARNING,
                        subsystem="roles",
                        section_slug="roles",
                        resource_type="role",
                        resource_id=role.id,
                        summary=(
                            f"Auto-role tier for `@{role.name}` can't be "
                            "assigned by the bot"
                        ),
                        detail=(
                            f"The tier is configured but {verdict.reason}, so "
                            "automation can't grant it."
                        ),
                        repairability=REPAIR_BLOCKED,
                        advisory_note=(
                            "Give the bot Manage Roles and move its role above "
                            f"`@{role.name}` in Server Settings → Roles, then "
                            "re-scan. PR12 never reorders roles."
                        ),
                    ),
                )
    return findings


# ---------------------------------------------------------------------------
# Collector: moderator / trusted role config (via config_arbitration)
# ---------------------------------------------------------------------------


async def _diagnose_moderation_roles(
    guild: discord.Guild,
) -> list[SetupDiagnosticFinding]:
    """Flag a configured moderator/trusted role that points at a dead role.

    These are *authority* roles (ADR-008): the bot does not assign them,
    so feasibility/hierarchy is irrelevant — the only failure that matters
    is a configured id that no longer resolves, which silently drops the
    capability grant.  Re-picking is a Moderation-section task, so the
    finding is advisory (no second mutation path from diagnostics).
    """
    try:
        from core.runtime import config_arbitration, guild_resources
    except Exception:
        logger.exception("setup_diagnostics: config_arbitration import failed")
        return []

    findings: list[SetupDiagnosticFinding] = []
    probes = (
        ("moderator role", config_arbitration.get_moderator_tier_role),
        ("trusted role", config_arbitration.get_trusted_tier_role),
    )
    for label, getter in probes:
        try:
            result = await getter(guild.id)
            role_id = result.value
        except Exception:
            logger.exception("setup_diagnostics: %s read failed", label)
            continue
        if not role_id:
            continue  # not configured — perfectly fine
        role = guild_resources.resolve_role(guild, role_id=role_id)
        if role is None:
            findings.append(
                SetupDiagnosticFinding(
                    code="stale_moderation_role",
                    severity=SEV_WARNING,
                    subsystem="moderation",
                    section_slug="moderation",
                    resource_type="role",
                    resource_id=int(role_id),
                    summary=f"Configured {label} points at a deleted role (`{role_id}`)",
                    detail=(
                        f"The {label} grants a capability tier to its members "
                        "(ADR-008), but the role no longer exists, so the grant "
                        "never applies."
                    ),
                    repairability=REPAIR_ADVISORY,
                    advisory_note=(
                        "Re-pick the role in the Moderation section, or clear it "
                        "in `!settings → Moderation`."
                    ),
                ),
            )
    return findings


# ---------------------------------------------------------------------------
# Collector: cleanup policy health (via services.cleanup_diagnostics)
# ---------------------------------------------------------------------------


async def _diagnose_cleanup(
    guild: discord.Guild,
) -> list[SetupDiagnosticFinding]:
    """Surface cleanup rows the resolver can never apply.

    Reuses the cleanup subsystem's own health report; PR12 does not
    re-derive cleanup resolution.  Both cases are advisory: the dedicated
    cleanup panel (`!cleanup → Cleanup Policies`) already owns the
    versioned builder / dry-run / audited apply that fixes them, so
    diagnostics points there rather than opening a parallel write path.
    """
    try:
        from services.cleanup_diagnostics import collect_cleanup_diagnostics

        diag = await collect_cleanup_diagnostics(guild)
    except Exception:
        logger.exception("setup_diagnostics: cleanup diagnostics failed")
        return []

    findings: list[SetupDiagnosticFinding] = []
    for row in diag.ineffective_rows:
        findings.append(
            SetupDiagnosticFinding(
                code="ineffective_cleanup_policy",
                severity=SEV_WARNING,
                subsystem="cleanup",
                section_slug="cleanup",
                resource_type="guild",
                resource_id=row.scope_id,
                summary="Guild cleanup policy is stored under the wrong key",
                detail=(
                    "A guild-default cleanup row keyed by something other than "
                    "the guild id is never read by the resolver, so the policy "
                    "never takes effect."
                ),
                repairability=REPAIR_ADVISORY,
                advisory_note=(
                    "Re-set the guild cleanup level in `!cleanup → Cleanup "
                    "Policies` (it writes the correct key and supersedes the "
                    "dead row)."
                ),
            ),
        )
    for row in diag.stale_rows:
        findings.append(
            SetupDiagnosticFinding(
                code="stale_cleanup_policy",
                severity=SEV_ADVISORY,
                subsystem="cleanup",
                section_slug="cleanup",
                resource_type=row.scope_type,
                resource_id=row.scope_id,
                summary=(
                    f"Cleanup policy targets a deleted {row.scope_type} "
                    f"(`{row.scope_id}`)"
                ),
                detail=(
                    f"A {row.scope_type}-scoped cleanup policy points at a "
                    "channel/category that no longer exists, so it can never "
                    "match."
                ),
                repairability=REPAIR_ADVISORY,
                advisory_note=(
                    "Remove the stale scope in `!cleanup → Cleanup Policies`."
                ),
            ),
        )
    return findings


__all__ = [
    "REPAIRABILITIES",
    "REPAIR_ADVISORY",
    "REPAIR_AUTO",
    "REPAIR_BLOCKED",
    "REPAIR_CONDITIONAL",
    "SEVERITIES",
    "SEV_ADVISORY",
    "SEV_BLOCKER",
    "SEV_INFO",
    "SEV_WARNING",
    "SetupDiagnosticFinding",
    "SetupDiagnosticsReport",
    "collect_setup_diagnostics",
    "staged_repair_ops",
]
