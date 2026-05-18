"""Resource validation status taxonomy.

A :class:`ResourceStatus` captures the result of validating a guild
resource — does it exist?  Is the bot able to access it?  Was the
last attempt a permission failure?  The taxonomy drives:

* Phase 4c resource diagnostics (orphan / missing / permission-gap
  severity tiers).
* Phase 7.5 repair flows (only ``MISSING`` and ``INVALID`` resources
  are auto-repairable; ``UNRESOLVED`` is waiting on the next probe).
* Phase 2b bindings (a binding with a ``MISSING`` target surfaces as
  an unbound slot in the wizard).

The taxonomy is intentionally small.  Anything that distinguishes finer
state belongs in subsystem-specific diagnostics, not the platform
validation enum.
"""

from __future__ import annotations

from enum import Enum


class ResourceStatus(Enum):
    """Validation state for a guild resource.

    Members:

    BOUND:
        The resource exists in the guild and the bot can interact with
        it as expected.  This is the steady state.
    UNRESOLVED:
        The resource has not been validated yet (e.g. recently bound,
        cache miss after restart).  The next probe will transition to
        ``BOUND``, ``MISSING``, or ``INVALID``.
    MISSING:
        The resource does not exist in the guild (deleted, never
        existed, or out of cache).  Phase 7.5's repair flow may offer
        to recreate it from the subsystem's resource requirement.
    INVALID:
        The resource exists but the bot cannot operate on it
        (permission gap, wrong type, archived thread, etc.).  Phase 4c
        diagnostics surface the specific reason; this enum value just
        says "exists, unusable".
    """

    BOUND = "bound"
    UNRESOLVED = "unresolved"
    MISSING = "missing"
    INVALID = "invalid"


# Tier mapping consumed by Phase 4c's setup-health finding classifier.
# Matches the existing finding-tier model in
# :data:`utils.subsystem_registry.IDENTITY_FINDING_TIER`.
STATUS_TIER: dict[ResourceStatus, str] = {
    ResourceStatus.BOUND: "ok",
    ResourceStatus.UNRESOLVED: "warn_only",
    ResourceStatus.MISSING: "auto_healable",
    ResourceStatus.INVALID: "operator_required",
}


def is_actionable(status: ResourceStatus) -> bool:
    """Return True iff Phase 7.5 repair flows can act on ``status``.

    ``UNRESOLVED`` is intentionally not actionable — a repair would race
    against the next validation probe and produce confusing results.
    """
    return STATUS_TIER[status] in {"auto_healable", "operator_required"}


__all__ = ["STATUS_TIER", "ResourceStatus", "is_actionable"]
