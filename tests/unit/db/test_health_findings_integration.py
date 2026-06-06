"""Real-Postgres integration for the persistent operational-health findings
store (bot-awareness PR6) — the SQL no other test executes.

Why this file exists
--------------------
``test_health_findings_service.py`` mocks ``svc._db``, so it pins the *service*
contract but never runs the actual ``ON CONFLICT`` dedupe / reopen / roll-up /
prune SQL. This suite drives that SQL against a live database via
``utils.db.pool.init()`` (which applies the full schema + every migration,
including 057), then asserts the observable behaviour.

CI safety
---------
There is **no** shared Postgres fixture (``tests/conftest.py`` deliberately has
none) and CI (``code-quality.yml``) runs **no** Postgres service. The module-local
``postgres_pool`` fixture below therefore ``pytest.skip()``s cleanly when
``DATABASE_URL`` is unset (CI) or the database is unreachable (sandbox before
local Postgres is up), so this file is a no-op there and only runs where a real
database is available. It is intentionally NOT promoted to ``conftest.py`` — no
other suite needs a live DB, and they all mock the pool.

Isolation
---------
Every fingerprint this suite writes starts with :data:`_PREFIX`
(``test:integration:``); the fixture sweeps exactly those rows from both tables
before and after each test, so it never disturbs (or asserts against) findings
the booted bot may have recorded. Count assertions use before/after deltas for
the same reason. Tests run serially (CI and ``check_quality`` both invoke pytest
without xdist), so the shared prefix is safe.
"""

from __future__ import annotations

import datetime
import os
from datetime import timedelta

import asyncpg
import pytest
import pytest_asyncio

from services import health_findings_service as svc
from services.health_contracts import (
    FindingSeverity,
    HealthAudience,
    HealthSnapshot,
    OperationalHealthFinding,
    SnapshotStatus,
)
from utils.db import health_findings as hf
from utils.db import pool

_PREFIX = "test:integration:"


def _fp(suffix: str) -> str:
    """A namespaced fingerprint guaranteed to be swept on teardown."""
    return _PREFIX + suffix


def _now() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


async def _sweep() -> None:
    """Delete only this suite's rows from both findings tables."""
    like = _PREFIX + "%"
    await pool.execute(
        "DELETE FROM operational_health_finding_aggregates WHERE fingerprint LIKE $1",
        (like,),
    )
    await pool.execute(
        "DELETE FROM operational_health_findings WHERE fingerprint LIKE $1",
        (like,),
    )


@pytest_asyncio.fixture
async def postgres_pool():
    """Module-local live-Postgres pool; skips cleanly when none is available.

    Applies the schema + migrations via ``pool.init()`` (forward-only and
    idempotent, so re-running per test is cheap once the DB is provisioned),
    then yields the pool. Sweeps the ``test:integration:*`` rows on entry and
    exit and closes the pool afterwards.
    """
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL unset — real-Postgres integration test skipped (CI)")
    try:
        await pool.init()
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(
            f"Postgres unreachable ({type(exc).__name__}) — integration test skipped",
        )
    await _sweep()
    try:
        yield pool
    finally:
        await _sweep()
        await pool.close()


# ---------------------------------------------------------------------------
# Low-level helpers (drive the writer SQL under test directly)
# ---------------------------------------------------------------------------


async def _upsert(
    fp: str,
    *,
    count: int = 1,
    seen_at: datetime.datetime | None = None,
    severity: str = "error",
    session_id: str | None = None,
    snapshot_id: str | None = None,
) -> None:
    await hf.upsert_finding(
        fingerprint=fp,
        severity=severity,
        category="runtime.log_error",
        message="boom",
        related_subsystem="errors",
        related_command=None,
        related_provider=None,
        file_hint=None,
        suggested_next_step=None,
        occurrence_count=count,
        source="log_buffer",
        session_id=session_id,
        snapshot_id=snapshot_id,
        seen_at=seen_at or _now(),
    )


async def _row(fp: str) -> dict | None:
    return await pool.fetchone(
        "SELECT * FROM operational_health_findings WHERE fingerprint = $1",
        (fp,),
    )


async def _aggregate(fp: str) -> dict | None:
    return await pool.fetchone(
        "SELECT * FROM operational_health_finding_aggregates WHERE fingerprint = $1",
        (fp,),
    )


async def _set_status(
    fp: str,
    status: str,
    *,
    first_seen: datetime.datetime | None = None,
    last_seen: datetime.datetime | None = None,
) -> None:
    """Move a finding to resolved/ignored (there is no shipped operator write
    path for this yet, so the test drives it with raw SQL — permitted here
    because the sole-writer invariant only scans ``disbot/``)."""
    await pool.execute(
        """
        UPDATE operational_health_findings
        SET status = $2,
            first_seen_at = COALESCE($3, first_seen_at),
            last_seen_at = COALESCE($4, last_seen_at)
        WHERE fingerprint = $1
        """,
        (fp, status, first_seen, last_seen),
    )


def _finding(fp: str, *, count: int = 1) -> OperationalHealthFinding:
    return OperationalHealthFinding(
        fingerprint=fp,
        severity=FindingSeverity.ERROR,
        category="runtime.log_error",
        message="boom",
        occurrence_count=count,
        related_subsystem="errors",
        source="log_buffer",
    )


def _snapshot(
    *findings: OperationalHealthFinding,
    snapshot_id: str = "snap",
    generated_at: datetime.datetime | None = None,
) -> HealthSnapshot:
    return HealthSnapshot(
        snapshot_id=snapshot_id,
        generated_at=generated_at or _now(),
        purpose="startup",
        status=SnapshotStatus.DEGRADED,
        summary="x",
        subsystems=(),
        findings=tuple(findings),
        redaction_audience=HealthAudience.PLATFORM_OWNER,
    )


# ---------------------------------------------------------------------------
# upsert / dedupe / lifecycle
# ---------------------------------------------------------------------------


async def test_upsert_inserts_open_with_count(postgres_pool):
    """First sighting inserts a single OPEN row with the given count and equal
    first/last seen timestamps."""
    fp = _fp("upsert-open")
    await _upsert(fp, count=3)

    row = await _row(fp)
    assert row is not None
    assert row["status"] == "open"
    assert row["occurrence_count"] == 3
    assert row["severity"] == "error"
    assert row["category"] == "runtime.log_error"
    assert row["first_seen_at"] == row["last_seen_at"]  # fresh insert


async def test_reupsert_delta_adds_count_and_advances_last_seen(postgres_pool):
    """A recurrence adds to the count, advances last_seen, preserves first_seen,
    and never creates a second row (dedupe by fingerprint)."""
    fp = _fp("reupsert")
    t0 = _now() - timedelta(minutes=5)
    t1 = _now()
    await _upsert(fp, count=2, seen_at=t0)
    await _upsert(fp, count=3, seen_at=t1)

    row = await _row(fp)
    assert row["occurrence_count"] == 5  # 2 + 3 (delta-add, not overwrite)
    assert row["status"] == "open"
    assert row["first_seen_at"] == t0  # preserved
    assert row["last_seen_at"] == t1  # advanced
    assert row["last_seen_at"] > row["first_seen_at"]

    rows = await pool.fetchall(
        "SELECT fingerprint FROM operational_health_findings WHERE fingerprint = $1",
        (fp,),
    )
    assert len(rows) == 1  # exactly one row


async def test_resolved_finding_reopens_on_recurrence(postgres_pool):
    """A recurrence of a RESOLVED finding reopens it (news again) while the
    occurrence count keeps accumulating across the reopen."""
    fp = _fp("reopen")
    await _upsert(fp, count=1)
    await _set_status(fp, "resolved")
    assert (await _row(fp))["status"] == "resolved"

    await _upsert(fp, count=2)
    row = await _row(fp)
    assert row["status"] == "open"  # reopened
    assert row["occurrence_count"] == 3  # 1 + 2


async def test_ignored_finding_stays_ignored_on_recurrence(postgres_pool):
    """A recurrence of an IGNORED finding stays ignored (muted noise must not
    resurface) but still accumulates its occurrence count."""
    fp = _fp("ignored")
    await _upsert(fp, count=1)
    await _set_status(fp, "ignored")

    await _upsert(fp, count=4)
    row = await _row(fp)
    assert row["status"] == "ignored"  # stays ignored
    assert row["occurrence_count"] == 5  # 1 + 4


async def test_list_and_count_by_status(postgres_pool):
    """list_by_status filters correctly and count_by_status reflects each
    status. Counts use before/after deltas so pre-existing rows (e.g. the
    booted bot's own findings) do not affect the assertions."""
    before = await svc.count_by_status()

    await _upsert(_fp("lc-open-1"))
    await _upsert(_fp("lc-open-2"))
    await _upsert(_fp("lc-res"))
    await _set_status(_fp("lc-res"), "resolved")
    await _upsert(_fp("lc-ign"))
    await _set_status(_fp("lc-ign"), "ignored")

    after = await svc.count_by_status()
    assert after.get("open", 0) - before.get("open", 0) == 2
    assert after.get("resolved", 0) - before.get("resolved", 0) == 1
    assert after.get("ignored", 0) - before.get("ignored", 0) == 1

    open_fps = {
        r["fingerprint"]
        for r in await svc.list_by_status("open", limit=1000)
        if r["fingerprint"].startswith(_PREFIX)
    }
    assert open_fps == {_fp("lc-open-1"), _fp("lc-open-2")}  # resolved/ignored excluded

    resolved_fps = {
        r["fingerprint"]
        for r in await svc.list_by_status("resolved", limit=1000)
        if r["fingerprint"].startswith(_PREFIX)
    }
    assert resolved_fps == {_fp("lc-res")}

    # status=None lists across every status.
    all_fps = {
        r["fingerprint"]
        for r in await svc.list_by_status(None, limit=1000)
        if r["fingerprint"].startswith(_PREFIX)
    }
    assert all_fps == {_fp("lc-open-1"), _fp("lc-open-2"), _fp("lc-res"), _fp("lc-ign")}


# ---------------------------------------------------------------------------
# retention: roll-up then prune
# ---------------------------------------------------------------------------


async def test_roll_up_then_prune_folds_resolved_ignored_and_keeps_open(
    postgres_pool,
):
    """Roll-up folds resolved/ignored detail past the cutoff into aggregates;
    prune then deletes exactly those rows and returns the count. Open rows —
    even old ones — survive both steps."""
    old = _now() - timedelta(days=40)
    cutoff = _now() - timedelta(days=30)

    open_fp = _fp("rp-open")
    res_fp = _fp("rp-res")
    ign_fp = _fp("rp-ign")

    await _upsert(open_fp, count=1, seen_at=old)  # OLD but open -> must survive
    await _upsert(res_fp, count=2, seen_at=old)
    await _set_status(res_fp, "resolved", last_seen=old)
    await _upsert(ign_fp, count=3, seen_at=old)
    await _set_status(ign_fp, "ignored", last_seen=old)

    # prune_expired returns the count of rows matching its own predicate.
    prunable = await pool.fetchone(
        "SELECT COUNT(*) AS n FROM operational_health_findings "
        "WHERE status IN ('resolved', 'ignored') AND last_seen_at < $1",
        (cutoff,),
    )
    expected = int(prunable["n"])
    assert expected >= 2  # at least our resolved + ignored rows

    await hf.roll_up_to_aggregates(cutoff)
    pruned = await hf.prune_expired(cutoff)

    assert pruned == expected
    assert await _row(res_fp) is None  # pruned
    assert await _row(ign_fp) is None  # pruned
    assert await _row(open_fp) is not None  # open survives

    res_agg = await _aggregate(res_fp)
    ign_agg = await _aggregate(ign_fp)
    assert res_agg is not None and res_agg["total_occurrences"] == 2
    assert ign_agg is not None and ign_agg["total_occurrences"] == 3
    assert res_agg["category"] == "runtime.log_error"
    assert res_agg["severity"] == "error"


async def test_roll_up_accumulates_totals_and_widens_window(postgres_pool):
    """A second fold of the same fingerprint sums total_occurrences and widens
    the aggregate window via LEAST(first_seen)/GREATEST(last_seen)."""
    fp = _fp("agg-sum")
    cutoff = _now() - timedelta(days=30)
    a, b = _now() - timedelta(days=50), _now() - timedelta(days=49)
    c, d = _now() - timedelta(days=60), _now() - timedelta(days=31)

    # Fold 1: total=2, window [a, b].
    await _upsert(fp, count=2, seen_at=a)
    await _set_status(fp, "resolved", first_seen=a, last_seen=b)
    await hf.roll_up_to_aggregates(cutoff)
    await hf.prune_expired(cutoff)
    agg = await _aggregate(fp)
    assert agg["total_occurrences"] == 2
    assert agg["first_seen_at"] == a
    assert agg["last_seen_at"] == b

    # Fold 2 (recurrence after prune): a fresh row, folded again.
    await _upsert(fp, count=5, seen_at=c)
    await _set_status(fp, "ignored", first_seen=c, last_seen=d)
    await hf.roll_up_to_aggregates(cutoff)
    await hf.prune_expired(cutoff)
    agg = await _aggregate(fp)
    assert agg["total_occurrences"] == 7  # 2 + 5 summed
    assert agg["first_seen_at"] == c  # LEAST(a, c) = c
    assert agg["last_seen_at"] == d  # GREATEST(b, d) = d


# ---------------------------------------------------------------------------
# service end-to-end
# ---------------------------------------------------------------------------


async def test_record_findings_end_to_end(postgres_pool):
    """The sole writer records a snapshot's findings through to Postgres,
    carrying session/snapshot ids, and dedupes a re-record (count delta-add +
    refreshed session/snapshot)."""
    fp = _fp("record-e2e")
    g1 = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    g2 = datetime.datetime(2026, 2, 1, tzinfo=datetime.timezone.utc)

    n = await svc.record_findings(
        _snapshot(_finding(fp, count=2), snapshot_id="snap-xyz", generated_at=g1),
        session_id="boot-123",
    )
    assert n == 1

    row = await _row(fp)
    assert row["status"] == "open"
    assert row["occurrence_count"] == 2
    assert row["source"] == "log_buffer"
    assert row["related_subsystem"] == "errors"
    assert row["last_session_id"] == "boot-123"
    assert row["last_snapshot_id"] == "snap-xyz"
    assert row["first_seen_at"] == g1
    assert row["last_seen_at"] == g1

    # Re-record the same fingerprint from a later snapshot -> dedupe + advance.
    await svc.record_findings(
        _snapshot(_finding(fp, count=3), snapshot_id="snap-2", generated_at=g2),
        session_id="boot-456",
    )
    row = await _row(fp)
    assert row["occurrence_count"] == 5  # 2 + 3
    assert row["last_session_id"] == "boot-456"
    assert row["last_snapshot_id"] == "snap-2"
    assert row["first_seen_at"] == g1  # preserved
    assert row["last_seen_at"] == g2  # advanced


async def test_run_retention_end_to_end_via_service(postgres_pool):
    """The service's run_retention rolls up then prunes resolved/ignored detail
    older than the TTL, leaving open findings in place."""
    open_fp = _fp("ret-open")
    old_fp = _fp("ret-old")
    old = _now() - timedelta(days=40)

    await _upsert(open_fp, count=1)  # recent + open -> survives
    await _upsert(old_fp, count=4, seen_at=old)
    await _set_status(old_fp, "resolved", last_seen=old)

    pruned = await svc.run_retention(ttl_days=30)
    assert pruned >= 1  # at least our old resolved row
    assert await _row(old_fp) is None  # pruned
    assert await _row(open_fp) is not None  # open survives

    agg = await _aggregate(old_fp)
    assert agg is not None and agg["total_occurrences"] == 4  # rolled up first
