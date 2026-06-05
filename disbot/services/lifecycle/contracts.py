"""Lifecycle mutation contract — request / preview / result / reversibility.

Generalises the :class:`services.resource_provisioning.ResourceProvisioningPipeline`
contract for the *change* operations provisioning does not own (rename, move,
delete, overwrite, reorder).  A coordinated domain service (channels, roles)
builds a typed request, exposes a side-effect-free :class:`LifecyclePreview`,
then performs an ordered apply whose outcome is a :class:`LifecycleResult`
carrying a per-target :class:`StepResult` list and a reversibility class.

Reversibility is honest about Discord's lack of transactions:

* **reversible** — restoring a prior name/category while permissions remain
  (e.g. rename).
* **compensatable** — undoable by a follow-up mutation, without a transaction
  guarantee (e.g. move back to the original category).
* **irreversible** — deleting a channel/role; the id and external references
  are gone, so recreation is never "rollback".

Audit follows the platform standard: a best-effort ``audit.action_recorded``
companion (via :func:`services.audit_events.emit_audit_action`) plus a
domain-owned catalogued event emitted by the service.  This module owns only
the shared companion helper and the typed result shapes; the domain event name
and the Discord calls live in the domain service.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from services.audit_events import emit_audit_action

logger = logging.getLogger("bot.services.lifecycle")

# ---------------------------------------------------------------------------
# Reversibility classes
# ---------------------------------------------------------------------------

REVERSIBLE = "reversible"
COMPENSATABLE = "compensatable"
IRREVERSIBLE = "irreversible"

# ---------------------------------------------------------------------------
# Outcomes — a partial Discord batch is never a transaction.
# ---------------------------------------------------------------------------

SUCCESS = "success"  # every step applied
PARTIAL = "partial"  # some steps applied, some failed
BLOCKED = "blocked"  # bot lacked permission / feasibility — nothing attempted
DECLINED = "declined"  # confirmation required for an irreversible op, not given
DISCORD_FAILED = "discord_failed"  # every attempted step failed at the API


@dataclass(frozen=True)
class StepResult:
    """Outcome of one target within a (possibly batched) operation."""

    target_id: int
    target_name: str
    ok: bool
    error: str | None = None


@dataclass(frozen=True)
class LifecyclePreview:
    """What an apply *would* do, with no side effects."""

    allowed: bool
    operation: str
    summary: str
    reversibility: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class LifecycleResult:
    """Outcome of a lifecycle apply."""

    mutation_id: str
    guild_id: int
    domain: str
    operation: str
    outcome: str
    reversibility: str
    steps: tuple[StepResult, ...] = field(default_factory=tuple)
    committed_at: datetime | None = None
    audit_emitted: bool = False
    event_emitted: bool = False

    @property
    def applied(self) -> tuple[StepResult, ...]:
        return tuple(s for s in self.steps if s.ok)

    @property
    def failed(self) -> tuple[StepResult, ...]:
        return tuple(s for s in self.steps if not s.ok)


def classify_outcome(steps: tuple[StepResult, ...]) -> str:
    """Map per-step results to a batch :data:`SUCCESS`/:data:`PARTIAL`/…."""
    if not steps:
        return DISCORD_FAILED
    ok = sum(1 for s in steps if s.ok)
    if ok == len(steps):
        return SUCCESS
    if ok == 0:
        return DISCORD_FAILED
    return PARTIAL


def now_utc() -> datetime:
    """Return a tz-aware "now" — INV-N forbids bare datetime.utcnow."""
    return datetime.now(timezone.utc)


async def emit_lifecycle_audit(
    *,
    mutation_id: str,
    domain: str,
    operation: str,
    guild_id: int,
    target: str,
    summary: str,
    actor_id: int | None,
    actor_type: str,
    occurred_at: datetime,
) -> bool:
    """Best-effort ``audit.action_recorded`` companion for a lifecycle apply.

    Wraps :func:`services.audit_events.emit_audit_action` with the lifecycle
    field mapping; the helper is failure-safe (returns ``False`` on bus error)
    so a dropped audit event never invalidates the Discord mutation.
    """
    return await emit_audit_action(
        mutation_id=mutation_id,
        subsystem=domain,
        mutation_type=f"{domain}_{operation}",
        target=target,
        scope="guild",
        guild_id=guild_id,
        prev_value=None,
        new_value=summary,
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=occurred_at,
    )


__all__ = [
    "BLOCKED",
    "COMPENSATABLE",
    "DECLINED",
    "DISCORD_FAILED",
    "IRREVERSIBLE",
    "PARTIAL",
    "REVERSIBLE",
    "SUCCESS",
    "LifecyclePreview",
    "LifecycleResult",
    "StepResult",
    "classify_outcome",
    "emit_lifecycle_audit",
    "now_utc",
]
