"""Setup-wizard finalization readiness rollup — setup-wizard PR1.

A small, sync, fail-safe registry that reports how far the setup-wizard
*finalization* tranche (the PR1–PR3 sequence in
``docs/setup_wizard_finalization_plan.md``) has progressed.  It is
surfaced as an informational section of ``!platform consistency`` so
operators and contributors can see, at a glance, which finalization
steps have landed.

Design mirrors :mod:`services.setup_blockers`:

* Every item has a zero-arg **sync** status provider that consults
  cached / importable in-process state and never performs I/O.
* A provider that raises is rendered ``"unknown"`` so one broken check
  cannot blank the section.
* All imports inside providers are **function-local** so this module
  does not trigger an import cycle with ``core.runtime`` at import time
  (the consistency report's collectors enforce the same discipline).
* **No** ``views`` import — this is a ``services`` module and the
  ``services → views`` boundary is a hard rule.  Cross-PR signals are
  therefore detected via neutral seams (a capability attribute on a
  ``core`` module, or a registered diagnostics provider) rather than by
  inspecting the view layer.

Status vocabulary::

    resolved    — the finalization step has landed.
    in_progress — partially landed / behind a flag.
    pending     — not started yet (a later PR in the tranche).
    deferred    — intentionally out of this tranche (see plan §D1).
    unknown     — the status provider raised (fail-safe fallback).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger("bot.wizard_finalization")

ItemStatus = Literal[
    "resolved",
    "in_progress",
    "pending",
    "deferred",
    "unknown",
]


@dataclass(frozen=True)
class FinalizationItem:
    """A single finalization step with metadata + a sync status provider."""

    id: str
    summary: str
    pr: str
    status_provider: Callable[[], ItemStatus]


@dataclass(frozen=True)
class FinalizationState:
    """Resolved status of a :class:`FinalizationItem` at snapshot time."""

    id: str
    summary: str
    pr: str
    status: ItemStatus


# ---------------------------------------------------------------------------
# Status providers (all sync; all imports function-local; no views import)
# ---------------------------------------------------------------------------


def _fallback_attribution_status() -> ItemStatus:
    """Resolved once config arbitration exposes per-key fallback attribution.

    PR1 adds ``attribution_snapshot`` to
    :mod:`core.runtime.config_arbitration`; its presence is the
    capability signal.
    """
    from core.runtime import config_arbitration

    return (
        "resolved" if hasattr(config_arbitration, "attribution_snapshot") else "pending"
    )


def _ai_advisor_review_status() -> ItemStatus:
    """Resolved when the AI setup advisor is wired in (PR3).

    Detected via a neutral seam — a registered ``setup_ai_advisor``
    diagnostics provider — because a ``services`` module must not import
    the ``views`` layer to inspect the wizard directly.  PR3 registers
    that provider as part of wiring the advisor into the wizard's
    optional review action.
    """
    from services import diagnostics_service

    return (
        "resolved"
        if "setup_ai_advisor" in diagnostics_service.registered_names()
        else "pending"
    )


def _preflight_gate_visible_status() -> ItemStatus:
    """Resolved when the preflight gate is surfaced in diagnostics (PR3).

    PR3 registers a ``setup_preflight`` diagnostics provider that
    exposes ``SETUP_PREFLIGHT_DIFF`` as an env-only gate (kept env-only
    per plan §D2); its registration is the resolution signal.
    """
    from services import diagnostics_service

    return (
        "resolved"
        if "setup_preflight" in diagnostics_service.registered_names()
        else "pending"
    )


def _provisioning_availability_gate_status() -> ItemStatus:
    """Intentionally deferred — see plan §D1.

    ``resource_provisioning.primary`` is declaration-only and the wizard
    has no legacy provisioning path, so enforcing a default-OFF flag now
    would regress live provisioning.  This step is deliberately out of
    the PR1–PR3 tranche.
    """
    return "deferred"


# ---------------------------------------------------------------------------
# Canonical registry
# ---------------------------------------------------------------------------


ITEMS: tuple[FinalizationItem, ...] = (
    FinalizationItem(
        id="fallback_attribution",
        summary="Config arbitration names which key fell back to legacy",
        pr="PR1",
        status_provider=_fallback_attribution_status,
    ),
    FinalizationItem(
        id="ai_advisor_review",
        summary="AI setup advisor reachable as an optional wizard review action",
        pr="PR3",
        status_provider=_ai_advisor_review_status,
    ),
    FinalizationItem(
        id="preflight_gate_visible",
        summary="SETUP_PREFLIGHT_DIFF surfaced as an env-only gate in diagnostics",
        pr="PR3",
        status_provider=_preflight_gate_visible_status,
    ),
    FinalizationItem(
        id="provisioning_availability_gate",
        summary="resource_provisioning.primary kill-switch (deferred — plan §D1)",
        pr="future",
        status_provider=_provisioning_availability_gate_status,
    ),
)


def status_for(item: FinalizationItem) -> ItemStatus:
    """Invoke ``item.status_provider`` with a fail-safe wrapper.

    A raising provider becomes ``"unknown"`` so a broken cached-state
    accessor cannot blank the readiness section.
    """
    try:
        return item.status_provider()
    except Exception as exc:  # noqa: BLE001 — registry is fail-safe
        logger.warning(
            "wizard_finalization: status_provider for %r raised %s",
            item.id,
            exc,
        )
        return "unknown"


def statuses() -> list[FinalizationState]:
    """Resolve every item's status into a list of :class:`FinalizationState`."""
    return [
        FinalizationState(
            id=item.id,
            summary=item.summary,
            pr=item.pr,
            status=status_for(item),
        )
        for item in ITEMS
    ]


__all__ = [
    "ITEMS",
    "FinalizationItem",
    "FinalizationState",
    "ItemStatus",
    "status_for",
    "statuses",
]
