"""Tests for services.health_findings_service — PR6 (bot awareness).

The sole writer of the persistent findings store. The SQL-level dedupe / reopen
(ON CONFLICT) is integration-tested against real Postgres; here we pin the
service contract: it records each finding through utils.db.health_findings with
the right arguments, is best-effort (swallows DB errors), and runs retention as
roll-up-then-prune.
"""

from __future__ import annotations

import datetime

from services import health_findings_service as svc
from services.health_contracts import (
    FindingSeverity,
    HealthAudience,
    HealthSnapshot,
    OperationalHealthFinding,
    SnapshotStatus,
)


def _snapshot(*findings: OperationalHealthFinding) -> HealthSnapshot:
    return HealthSnapshot(
        snapshot_id="snap1",
        generated_at=datetime.datetime(2026, 6, 6, tzinfo=datetime.timezone.utc),
        purpose="startup",
        status=SnapshotStatus.DEGRADED,
        summary="x",
        subsystems=(),
        findings=tuple(findings),
        redaction_audience=HealthAudience.PLATFORM_OWNER,
    )


def _finding(fp: str = "errors:x", count: int = 1) -> OperationalHealthFinding:
    return OperationalHealthFinding(
        fingerprint=fp,
        severity=FindingSeverity.ERROR,
        category="runtime.log_error",
        message="boom",
        occurrence_count=count,
        related_subsystem="errors",
        source="log_buffer",
    )


async def test_record_findings_upserts_each(monkeypatch) -> None:
    calls: list[dict] = []

    async def fake_upsert(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(svc._db, "upsert_finding", fake_upsert)
    n = await svc.record_findings(
        _snapshot(_finding("a", 2), _finding("b", 1)),
        session_id="boot-1",
    )
    assert n == 2
    assert {c["fingerprint"] for c in calls} == {"a", "b"}
    first = next(c for c in calls if c["fingerprint"] == "a")
    assert first["session_id"] == "boot-1"
    assert first["snapshot_id"] == "snap1"
    assert first["occurrence_count"] == 2
    assert first["severity"] == "error"  # enum -> value
    assert first["seen_at"].year == 2026


async def test_record_findings_swallows_db_error(monkeypatch) -> None:
    async def boom(**kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(svc._db, "upsert_finding", boom)
    # Must not raise; nothing recorded.
    assert await svc.record_findings(_snapshot(_finding())) == 0


async def test_record_findings_empty_snapshot_writes_nothing(monkeypatch) -> None:
    async def fake_upsert(**kwargs):
        raise AssertionError("should not be called for an empty snapshot")

    monkeypatch.setattr(svc._db, "upsert_finding", fake_upsert)
    assert await svc.record_findings(_snapshot()) == 0


async def test_run_retention_rolls_up_then_prunes(monkeypatch) -> None:
    order: list[tuple[str, datetime.datetime]] = []

    async def fake_rollup(cutoff):
        order.append(("rollup", cutoff))

    async def fake_prune(cutoff):
        order.append(("prune", cutoff))
        return 3

    monkeypatch.setattr(svc._db, "roll_up_to_aggregates", fake_rollup)
    monkeypatch.setattr(svc._db, "prune_expired", fake_prune)

    pruned = await svc.run_retention(ttl_days=30)
    assert pruned == 3
    assert [step[0] for step in order] == ["rollup", "prune"]  # roll up BEFORE prune
    age = datetime.datetime.now(tz=datetime.timezone.utc) - order[0][1]
    assert 29 <= age.days <= 30  # cutoff is ~ttl_days ago


async def test_run_retention_swallows_error(monkeypatch) -> None:
    async def boom(cutoff):
        raise RuntimeError("db down")

    monkeypatch.setattr(svc._db, "roll_up_to_aggregates", boom)
    assert await svc.run_retention() == 0
