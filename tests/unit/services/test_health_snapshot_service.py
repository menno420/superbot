"""Unit tests for services.health_snapshot_service — PR1 (bot awareness).

Covers the deterministic contract surface that the rest of the
programme relies on:

* severity / status mapping tables are pinned;
* a failed sync source degrades only its own subsystem (isolation);
* an async source that times out is isolated and flags the snapshot
  ``partial`` without breaking collection;
* subsystem ordering is stable;
* finding output is bounded;
* a ``partial`` snapshot never reports ``HEALTHY``.

Redaction is covered separately in ``test_health_redaction.py``.
"""

from __future__ import annotations

import asyncio
import datetime

import pytest

from services import diagnostics_service
from services import health_snapshot_service as hss
from services.health_contracts import (
    FindingSeverity,
    HealthAudience,
    HealthSnapshotRequest,
    OperationalHealthFinding,
    SnapshotStatus,
    SubsystemHealth,
    derive_overall_status,
    status_for_severity,
    worst_status,
)


def _sub(
    name: str,
    status: SnapshotStatus,
    *,
    required: bool = False,
    findings: tuple[OperationalHealthFinding, ...] = (),
) -> SubsystemHealth:
    return SubsystemHealth(
        name=name,
        status=status,
        summary=f"{name} {status.value}",
        generated_at=datetime.datetime.now(tz=datetime.timezone.utc),
        findings=findings,
        required=required,
    )


# --- pure mapping / aggregation -------------------------------------------


def test_status_for_severity_table() -> None:
    assert status_for_severity(FindingSeverity.INFO) is SnapshotStatus.HEALTHY
    assert status_for_severity(FindingSeverity.WARNING) is SnapshotStatus.DEGRADED
    assert status_for_severity(FindingSeverity.ERROR) is SnapshotStatus.DEGRADED
    assert status_for_severity(FindingSeverity.CRITICAL) is SnapshotStatus.CRITICAL


def test_worst_status_ranks_unknown_below_degraded() -> None:
    assert worst_status(()) is SnapshotStatus.HEALTHY
    assert (
        worst_status([SnapshotStatus.HEALTHY, SnapshotStatus.UNKNOWN])
        is SnapshotStatus.UNKNOWN
    )
    assert (
        worst_status([SnapshotStatus.UNKNOWN, SnapshotStatus.DEGRADED])
        is SnapshotStatus.DEGRADED
    )
    assert (
        worst_status([SnapshotStatus.DEGRADED, SnapshotStatus.CRITICAL])
        is SnapshotStatus.CRITICAL
    )


def test_overall_critical_only_from_required() -> None:
    # Optional subsystem critical -> overall degraded, not critical.
    optional_crit = _sub("ai", SnapshotStatus.CRITICAL, required=False)
    healthy_req = _sub("runtime", SnapshotStatus.HEALTHY, required=True)
    assert (
        derive_overall_status((optional_crit, healthy_req))
        is SnapshotStatus.DEGRADED
    )
    # Required subsystem critical -> overall critical.
    req_crit = _sub("database", SnapshotStatus.CRITICAL, required=True)
    assert derive_overall_status((req_crit, healthy_req)) is SnapshotStatus.CRITICAL


def test_overall_all_unknown_is_unknown() -> None:
    subs = (
        _sub("a", SnapshotStatus.UNKNOWN, required=True),
        _sub("b", SnapshotStatus.UNKNOWN, required=False),
    )
    assert derive_overall_status(subs) is SnapshotStatus.UNKNOWN


def test_required_unknown_degrades() -> None:
    subs = (
        _sub("runtime", SnapshotStatus.UNKNOWN, required=True),
        _sub("tasks", SnapshotStatus.HEALTHY, required=True),
    )
    assert derive_overall_status(subs) is SnapshotStatus.DEGRADED


def test_optional_unknown_does_not_degrade() -> None:
    subs = (
        _sub("runtime", SnapshotStatus.HEALTHY, required=True),
        _sub("ai", SnapshotStatus.UNKNOWN, required=False),
    )
    assert derive_overall_status(subs) is SnapshotStatus.HEALTHY


def test_partial_never_healthy() -> None:
    subs = (_sub("runtime", SnapshotStatus.HEALTHY, required=True),)
    assert derive_overall_status(subs, partial=False) is SnapshotStatus.HEALTHY
    assert derive_overall_status(subs, partial=True) is SnapshotStatus.DEGRADED


def test_source_vocabulary_maps_are_pinned() -> None:
    assert hss._SECTION_STATUS == {
        "clean": SnapshotStatus.HEALTHY,
        "warning": SnapshotStatus.DEGRADED,
        "fatal": SnapshotStatus.CRITICAL,
        "skipped": SnapshotStatus.UNKNOWN,
    }
    assert hss._SUMMARY_STATUS == {
        "ok": SnapshotStatus.HEALTHY,
        "degraded": SnapshotStatus.DEGRADED,
        "failed": SnapshotStatus.CRITICAL,
        "empty": SnapshotStatus.UNKNOWN,
    }
    # resource_health uses "warn" (not "warning").
    assert hss._RESOURCE_SEVERITY == {
        "info": FindingSeverity.INFO,
        "warn": FindingSeverity.WARNING,
        "error": FindingSeverity.ERROR,
    }


# --- finalize: ordering + bounds ------------------------------------------


def test_finalize_orders_subsystems() -> None:
    unordered = [
        _sub("ai", SnapshotStatus.HEALTHY),
        _sub("runtime", SnapshotStatus.HEALTHY),
        _sub("database", SnapshotStatus.HEALTHY),
    ]
    snap = hss._finalize(unordered, purpose="summary", partial=False)
    assert [s.name for s in snap.subsystems] == ["runtime", "database", "ai"]


def test_finalize_bounds_total_findings() -> None:
    many = tuple(
        OperationalHealthFinding(
            fingerprint=f"x{i}",
            severity=FindingSeverity.WARNING,
            category="x",
            message="m",
            related_subsystem="diagnostics",
        )
        for i in range(40)
    )
    sub = SubsystemHealth(
        name="diagnostics",
        status=SnapshotStatus.DEGRADED,
        summary="many",
        generated_at=datetime.datetime.now(tz=datetime.timezone.utc),
        findings=many,
    )
    snap = hss._finalize([sub], purpose="summary", partial=False)
    assert len(snap.findings) == hss.MAX_TOTAL_FINDINGS


def test_finalize_sorts_findings_by_severity() -> None:
    sub = SubsystemHealth(
        name="diagnostics",
        status=SnapshotStatus.CRITICAL,
        summary="x",
        generated_at=datetime.datetime.now(tz=datetime.timezone.utc),
        findings=(
            OperationalHealthFinding(
                fingerprint="info", severity=FindingSeverity.INFO,
                category="c", message="m", related_subsystem="d",
            ),
            OperationalHealthFinding(
                fingerprint="crit", severity=FindingSeverity.CRITICAL,
                category="c", message="m", related_subsystem="d",
            ),
        ),
    )
    snap = hss._finalize([sub], purpose="summary", partial=False)
    assert snap.findings[0].severity is FindingSeverity.CRITICAL


# --- sync source isolation -------------------------------------------------


def test_safe_wraps_raising_builder() -> None:
    def boom() -> SubsystemHealth:
        raise RuntimeError("kaboom")

    sub = hss._safe(boom, "explodey", required=True)
    assert sub.name == "explodey"
    assert sub.status is SnapshotStatus.UNKNOWN
    assert sub.required is True


def test_failed_diagnostics_provider_is_isolated() -> None:
    """A provider that raises becomes a finding, not an exception."""
    name = "test_health_boom_provider"

    def _raiser() -> dict:
        raise RuntimeError("provider exploded")

    diagnostics_service.register(name, _raiser)
    try:
        sub = hss._diagnostics_subsystem()
    finally:
        diagnostics_service.unregister(name)

    assert sub.status is SnapshotStatus.DEGRADED
    assert sub.facts["failed_count"] >= 1
    assert any(f.related_provider == name for f in sub.findings)


# --- async source isolation ------------------------------------------------


async def test_collect_snapshot_isolates_async_timeout(monkeypatch) -> None:
    async def _slow() -> SubsystemHealth:
        await asyncio.sleep(5)
        raise AssertionError("should have timed out")

    monkeypatch.setattr(hss, "_database_subsystem", _slow)
    monkeypatch.setattr(hss, "DB_TIMEOUT", 0.01)

    snap = await hss.collect_snapshot(HealthSnapshotRequest())
    db = next(s for s in snap.subsystems if s.name == "database")
    assert db.status is SnapshotStatus.CRITICAL  # DB failure_status
    assert snap.partial is True
    # partial must never be reported as healthy.
    assert snap.status is not SnapshotStatus.HEALTHY


async def test_collect_snapshot_isolates_async_exception(monkeypatch) -> None:
    async def _broken() -> SubsystemHealth:
        raise RuntimeError("db down")

    monkeypatch.setattr(hss, "_database_subsystem", _broken)
    snap = await hss.collect_snapshot(HealthSnapshotRequest())
    db = next(s for s in snap.subsystems if s.name == "database")
    assert db.status is SnapshotStatus.CRITICAL
    assert snap.partial is True


# --- smoke: cached collection works in a bare env --------------------------


def test_collect_cached_smoke() -> None:
    snap = hss.collect_cached_snapshot(HealthSnapshotRequest())
    names = {s.name for s in snap.subsystems}
    # process-local subsystems are always present (no bot supplied -> no gateway)
    assert {"runtime", "tasks", "diagnostics", "startup", "ai", "consistency"} <= names
    assert "gateway" not in names
    assert snap.redaction_audience is HealthAudience.GUILD_ADMIN
    assert isinstance(snap.status, SnapshotStatus)
