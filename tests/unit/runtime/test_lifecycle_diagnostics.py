"""LP-6 tests for the lifecycle diagnostics surface.

Covers:
  * ``lifecycle.diagnostics_snapshot()`` returns the expected shape
    across phases.
  * The ``lifecycle`` provider self-registers with
    :mod:`services.diagnostics_service` at import time.
  * The ``runtime_lock`` provider self-registers and exposes the
    process's boot identity.
  * The new ``_collect_lifecycle`` collector in
    :mod:`services.platform_consistency` maps lifecycle phases to the
    right ``SectionStatus`` (CLEAN for RUNNING/STARTING, WARNING for
    drain phases, FATAL for FAILED_STARTUP).
"""

from __future__ import annotations

import asyncio

import pytest

from core.runtime import lifecycle
from services import diagnostics_service
from services import platform_consistency as pc
from services import runtime as runtime_module


@pytest.fixture(autouse=True)
def _reset_lifecycle_state() -> None:
    lifecycle.reset_for_tests()
    yield
    lifecycle.reset_for_tests()


def test_diagnostics_snapshot_contains_expected_keys() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING, reason="on_ready")

    snap = lifecycle.diagnostics_snapshot()

    assert snap["phase"] == "RUNNING"
    assert snap["can_accept_commands"] is True
    assert snap["is_shutting_down"] is False
    assert snap["restart_requested"] is False
    assert snap["remaining_shutdown_seconds"] is None
    assert snap["pending"] is None
    # recent_events is a list (may contain the on_ready transition).
    assert isinstance(snap["recent_events"], list)


def test_diagnostics_snapshot_surfaces_pending_request() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown(
        "sigterm",
        actor="signal_handler",
        grace_seconds=30.0,
    )

    snap = lifecycle.diagnostics_snapshot()

    assert snap["phase"] == "DRAINING"
    assert snap["is_shutting_down"] is True
    assert snap["can_accept_commands"] is False
    assert snap["pending"] == {
        "kind": "shutdown",
        "reason": "sigterm",
        "actor": "signal_handler",
        "requested_at_monotonic": pytest.approx(
            snap["pending"]["requested_at_monotonic"],
        ),
        "grace_seconds": 30.0,
    }
    remaining = snap["remaining_shutdown_seconds"]
    assert remaining is not None
    assert 0.0 <= remaining <= 30.0


def test_lifecycle_provider_is_registered_with_diagnostics_service() -> None:
    """LP-6: lifecycle self-registers as a diagnostics provider so
    operators can read it from the unified registry."""
    assert "lifecycle" in diagnostics_service.registered_names()
    snap = diagnostics_service.snapshot("lifecycle")
    assert "phase" in snap
    assert "can_accept_commands" in snap


def test_runtime_lock_provider_is_registered_with_boot_identity() -> None:
    """LP-6: runtime self-registers as a diagnostics provider
    exposing the in-process boot identity. DB-backed introspection is
    intentionally out of scope here — sync providers cannot await."""
    assert "runtime_lock" in diagnostics_service.registered_names()
    snap = diagnostics_service.snapshot("runtime_lock")
    assert snap["boot_id"] == str(runtime_module.BOOT_ID)
    assert snap["lock_name"]


def _run_collect_lifecycle() -> pc.SectionResult:
    return asyncio.run(pc._collect_lifecycle())


def test_collect_lifecycle_running_is_clean() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    result = _run_collect_lifecycle()
    assert result.status is pc.SectionStatus.CLEAN
    assert "RUNNING" in result.summary or "RUNNING" in " ".join(result.details)


def test_collect_lifecycle_starting_is_clean() -> None:
    lifecycle.set_phase(lifecycle.Phase.STARTING)
    result = _run_collect_lifecycle()
    assert result.status is pc.SectionStatus.CLEAN


def test_collect_lifecycle_failed_startup_is_fatal() -> None:
    lifecycle.set_phase(lifecycle.Phase.FAILED_STARTUP)
    result = _run_collect_lifecycle()
    assert result.status is pc.SectionStatus.FATAL
    assert any("rebooted" in action.lower() for action in result.suggested_actions)


@pytest.mark.parametrize(
    "phase",
    [
        lifecycle.Phase.DRAINING,
        lifecycle.Phase.SHUTTING_DOWN,
        lifecycle.Phase.RESTARTING,
        lifecycle.Phase.STOPPED,
    ],
)
def test_collect_lifecycle_winding_down_phases_are_warning(
    phase: lifecycle.Phase,
) -> None:
    lifecycle.set_phase(phase)
    result = _run_collect_lifecycle()
    assert result.status is pc.SectionStatus.WARNING
    assert phase.value in result.summary


def test_collect_lifecycle_surfaces_pending_in_details() -> None:
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm", actor="signal_handler")
    result = _run_collect_lifecycle()
    # Pending must appear in details (the section is otherwise opaque).
    details_text = " ".join(result.details)
    assert "shutdown" in details_text
    assert "sigterm" in details_text


def test_lifecycle_section_in_collect_report_uses_correct_kind() -> None:
    """LP-6: when the full ``collect_report`` runs, the Lifecycle
    section ends up stamped with ``ReadinessKind.LIFECYCLE`` and slots
    into the canonical ordering between RUNTIME_PROVIDERS and
    SETUP_READINESS."""
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    report = asyncio.run(pc.collect_report(bot=None, guild=None))
    lifecycle_sections = [
        s for s in report.sections if s.kind is pc.ReadinessKind.LIFECYCLE
    ]
    assert len(lifecycle_sections) == 1
    # Position: index 9 (after the nine pre-existing runtime sections,
    # before SETUP_READINESS).
    assert report.sections[9].kind is pc.ReadinessKind.LIFECYCLE
    assert report.sections[10].kind is pc.ReadinessKind.SETUP_READINESS
