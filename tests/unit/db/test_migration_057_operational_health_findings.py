"""Static SQL-shape pins for migration 057 + its writer (bot-awareness PR6).

Mirrors ``test_migration_051_main_server_backfill.py``: we cannot run Postgres
in unit CI (``tests/conftest.py`` has no DB fixture, ``code-quality.yml`` runs no
Postgres service), but we CAN pin the *shape* of the schema and the dedupe SQL so
a drive-by edit that — say — drops the ``ON CONFLICT`` delta-add, loosens a CHECK
constraint set, removes the reopen ``CASE``, or changes the prune predicate fails
here instead of silently in production.

The live behaviour these shapes encode is exercised against a real database in
``test_health_findings_integration.py`` (skipped when no Postgres is reachable).

Two sources are pinned:

* ``disbot/migrations/057_operational_health_findings.sql`` — the two tables,
  their fingerprint primary keys, the status/severity CHECK sets, the
  status+last_seen index, and ``CREATE … IF NOT EXISTS`` idempotency.
* ``disbot/utils/db/health_findings.py`` — the writer's ON CONFLICT occurrence
  delta-add, the reopen-but-keep-ignored ``CASE``, the roll-up ``GREATEST`` /
  ``LEAST`` / summed ``total_occurrences``, and the prune ``WHERE status IN``.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MIGRATION = (
    _REPO_ROOT / "disbot" / "migrations" / "057_operational_health_findings.sql"
)
_WRITER = _REPO_ROOT / "disbot" / "utils" / "db" / "health_findings.py"


def _collapse(text: str) -> str:
    """Collapse all runs of whitespace to a single space.

    Lets the assertions match the SQL regardless of how it is wrapped across
    lines, so a purely cosmetic reflow does not produce a false failure.
    """
    return re.sub(r"\s+", " ", text).strip()


def _migration_sql() -> str:
    """Migration text with ``-- …`` line comments stripped, then collapsed.

    Stripping comments keeps the occurrence counts (e.g. the two
    ``fingerprint TEXT PRIMARY KEY`` declarations) honest — the file's header
    prose mentions the tables and columns but must not be mistaken for the
    executable DDL.
    """
    no_comments = "\n".join(
        line.split("--", 1)[0] for line in _MIGRATION.read_text().splitlines()
    )
    return _collapse(no_comments)


def _writer_src() -> str:
    return _collapse(_WRITER.read_text())


# ---------------------------------------------------------------------------
# Migration 057 — schema shape
# ---------------------------------------------------------------------------


def test_migration_file_exists():
    assert _MIGRATION.is_file(), f"{_MIGRATION} missing"


def test_creates_both_findings_tables():
    """The detail table and its retention-survivor aggregates table must both
    be created — losing either breaks recording or long-run history."""
    sql = _migration_sql()
    assert "CREATE TABLE IF NOT EXISTS operational_health_findings" in sql
    assert "CREATE TABLE IF NOT EXISTS operational_health_finding_aggregates" in sql


def test_tables_are_idempotent_create_if_not_exists():
    """Both tables and the index use ``IF NOT EXISTS`` so the forward-only,
    re-runnable migration never aborts on an already-provisioned database.

    A bare ``CREATE TABLE``/``CREATE INDEX`` (no guard) would raise on the
    second apply and take boot down — pin against that regression.
    """
    sql = _migration_sql()
    assert (
        re.search(r"CREATE TABLE(?! IF NOT EXISTS)", sql) is None
    ), "every CREATE TABLE in migration 057 must use IF NOT EXISTS"
    assert (
        re.search(r"CREATE INDEX(?! IF NOT EXISTS)", sql) is None
    ), "the findings index must use CREATE INDEX IF NOT EXISTS"


def test_fingerprint_is_primary_key_on_both_tables():
    """Fingerprint is the natural dedupe key on the detail table and the
    roll-up key on the aggregates table — both make it the PRIMARY KEY, which
    is what the writer's ``ON CONFLICT (fingerprint)`` upserts depend on."""
    sql = _migration_sql()
    assert (
        sql.count("fingerprint TEXT PRIMARY KEY") == 2
    ), "both findings tables must key on `fingerprint TEXT PRIMARY KEY`"


def test_status_check_constraint_set():
    """The lifecycle states are exactly open/resolved/ignored — the writer's
    reopen CASE and the retention predicate both assume this closed set."""
    assert "CHECK (status IN ('open', 'resolved', 'ignored'))" in _migration_sql()


def test_severity_check_constraint_set():
    """Severity mirrors ``FindingSeverity`` (info/warning/error/critical);
    a drift here would let an out-of-vocabulary severity reach the store."""
    assert (
        "CHECK (severity IN ('info', 'warning', 'error', 'critical'))"
        in _migration_sql()
    )


def test_status_last_seen_index_present():
    """The ``(status, last_seen_at)`` index backs both the status-filtered
    listing (``WHERE status = $1 ORDER BY last_seen_at DESC``) and the
    retention sweep (``WHERE status IN (…) AND last_seen_at < $1``)."""
    assert (
        "CREATE INDEX IF NOT EXISTS ix_health_findings_status_last_seen "
        "ON operational_health_findings (status, last_seen_at)" in _migration_sql()
    )


# ---------------------------------------------------------------------------
# utils/db/health_findings.py — dedupe / reopen / roll-up / prune SQL
# ---------------------------------------------------------------------------


def test_writer_file_exists():
    assert _WRITER.is_file(), f"{_WRITER} missing"


def test_upsert_delta_adds_occurrence_count():
    """A recurrence must ADD to the existing count, not overwrite it — losing
    the ``+ EXCLUDED.occurrence_count`` would silently reset cross-boot totals."""
    assert (
        "occurrence_count = operational_health_findings.occurrence_count "
        "+ EXCLUDED.occurrence_count" in _writer_src()
    )


def test_upsert_advances_last_seen():
    """Each recurrence advances ``last_seen_at`` to the new sighting."""
    assert "last_seen_at = EXCLUDED.last_seen_at" in _writer_src()


def test_upsert_reopens_resolved_but_keeps_ignored():
    """A recurrence reopens a previously-resolved finding (it is news again)
    while leaving an operator-``ignored`` finding ignored. Dropping the CASE
    would either resurface muted noise or bury real recurrences."""
    assert (
        "status = CASE "
        "WHEN operational_health_findings.status = 'ignored' THEN 'ignored' "
        "ELSE 'open' END" in _writer_src()
    )


def test_rollup_sums_and_uses_least_greatest():
    """Roll-up accumulates ``total_occurrences`` and widens the seen-window
    with LEAST(first_seen)/GREATEST(last_seen) so pruned detail folds into the
    aggregates without losing the running totals or the historical span."""
    src = _writer_src()
    assert (
        "total_occurrences = operational_health_finding_aggregates.total_occurrences "
        "+ EXCLUDED.total_occurrences" in src
    )
    assert "first_seen_at = LEAST(" in src
    assert "last_seen_at = GREATEST(" in src


def test_rollup_and_prune_target_resolved_and_ignored_only():
    """Both the roll-up SELECT and the prune DELETE are scoped to
    resolved/ignored rows past the cutoff — open findings are never folded or
    pruned. A predicate change that swept open rows would erase live state."""
    src = _writer_src()
    assert (
        "FROM operational_health_findings "
        "WHERE status IN ('resolved', 'ignored') AND last_seen_at < $1" in src
    ), "roll-up must SELECT only resolved/ignored rows past the cutoff"
    assert (
        "DELETE FROM operational_health_findings "
        "WHERE status IN ('resolved', 'ignored') AND last_seen_at < $1" in src
    ), "prune must DELETE only resolved/ignored rows past the cutoff"
