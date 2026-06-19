"""Tests for ``dashboard/submissions_db.py`` — the read/moderate submissions side.

No live Postgres: status validation, the command-tag row-count parse, and the
dormant guards are tested directly, and the SELECT/UPDATE I/O paths run against a
tiny fake ``asyncpg`` connection injected via ``sys.modules``. Loaded by file path
(the module is a plain file under ``dashboard/``).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MODULE = _REPO_ROOT / "dashboard" / "submissions_db.py"


@pytest.fixture(scope="module")
def sdb():
    spec = importlib.util.spec_from_file_location("dashboard_submissions_db_ut", _MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# pure helpers
# ---------------------------------------------------------------------------


def test_rows_affected_parses_command_tag(sdb):
    assert sdb._rows_affected("UPDATE 1") == 1
    assert sdb._rows_affected("UPDATE 0") == 0
    assert sdb._rows_affected("INSERT 0 5") == 5
    assert sdb._rows_affected("weird") == 0


def test_is_configured_reflects_dsn_env(sdb, monkeypatch):
    monkeypatch.delenv("SUBMISSIONS_DB_DSN", raising=False)
    assert sdb.is_configured() is False
    monkeypatch.setenv("SUBMISSIONS_DB_DSN", "postgres://x")
    assert sdb.is_configured() is True


async def test_set_status_rejects_bad_status(sdb, monkeypatch):
    monkeypatch.setenv("SUBMISSIONS_DB_DSN", "postgres://x")
    # 'pending' is NOT a moderation decision — only approved/rejected are allowed.
    # The status check runs before any connection, so no DB/fake is needed.
    with pytest.raises(ValueError, match="status"):
        await sdb.set_status(1, "pending")


# ---------------------------------------------------------------------------
# dormant-by-default
# ---------------------------------------------------------------------------


async def test_list_pending_raises_when_dormant(sdb, monkeypatch):
    monkeypatch.delenv("SUBMISSIONS_DB_DSN", raising=False)
    with pytest.raises(sdb.SubmissionsNotConfigured):
        await sdb.list_pending()


async def test_set_status_raises_when_dormant(sdb, monkeypatch):
    monkeypatch.delenv("SUBMISSIONS_DB_DSN", raising=False)
    with pytest.raises(sdb.SubmissionsNotConfigured):
        await sdb.set_status(1, "approved")


# ---------------------------------------------------------------------------
# I/O paths against a fake asyncpg connection
# ---------------------------------------------------------------------------


class _FakeConn:
    def __init__(self, record, *, fetch_rows=None, execute_tag="UPDATE 1"):
        self.record = record
        self._fetch_rows = fetch_rows or []
        self._execute_tag = execute_tag
        self.closed = False

    async def fetch(self, sql, *params):
        self.record["sql"] = sql
        self.record["params"] = params
        return self._fetch_rows

    async def execute(self, sql, *params):
        self.record["sql"] = sql
        self.record["params"] = params
        return self._execute_tag

    async def close(self):
        self.closed = True


def _install_fake(monkeypatch, conn):
    class _FakeAsyncpg:
        async def connect(self, target):
            conn.record["dsn"] = target
            return conn

    monkeypatch.setenv("SUBMISSIONS_DB_DSN", "postgres://test")
    monkeypatch.setitem(sys.modules, "asyncpg", _FakeAsyncpg())


async def test_list_pending_queries_pending_oldest_first(sdb, monkeypatch):
    record: dict = {}
    rows = [{"id": 1, "kind": "bug", "title": "a", "status": "pending"}]
    conn = _FakeConn(record, fetch_rows=rows)
    _install_fake(monkeypatch, conn)

    result = await sdb.list_pending(limit=50)
    assert result == rows
    assert "WHERE status = 'pending'" in record["sql"]
    assert "ORDER BY submitted_at ASC" in record["sql"]
    assert "SELECT *" not in record["sql"]  # explicit columns, never SELECT *
    assert record["params"] == (50,)
    assert conn.closed is True


async def test_set_status_approves_pending_row(sdb, monkeypatch):
    record: dict = {}
    conn = _FakeConn(record, execute_tag="UPDATE 1")
    _install_fake(monkeypatch, conn)

    changed = await sdb.set_status(7, "approved", moderated_by="999")
    assert changed is True
    # The WHERE clause guards on status='pending' → idempotent double-click.
    assert "WHERE id = $1 AND status = 'pending'" in record["sql"]
    assert record["params"] == (7, "approved", "999")


async def test_set_status_noop_on_already_moderated(sdb, monkeypatch):
    record: dict = {}
    conn = _FakeConn(record, execute_tag="UPDATE 0")  # no row matched
    _install_fake(monkeypatch, conn)

    changed = await sdb.set_status(7, "rejected")
    assert changed is False


async def test_attach_issue_url_only_when_null(sdb, monkeypatch):
    record: dict = {}
    conn = _FakeConn(record, execute_tag="UPDATE 1")
    _install_fake(monkeypatch, conn)

    changed = await sdb.attach_issue_url(7, "https://github.com/menno420/superbot/issues/1")
    assert changed is True
    # Idempotent mirror: only sets when github_issue_url IS NULL (double-file guard).
    assert "WHERE id = $1 AND github_issue_url IS NULL" in record["sql"]
    assert record["params"] == (7, "https://github.com/menno420/superbot/issues/1")
