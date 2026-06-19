"""Tests for ``botsite/submissions_db.py`` — the INSERT-only submissions writer.

No live Postgres: the pure validation/sanitation contract (``build_insert`` /
``hash_ip``) is tested directly, and the one I/O path (``insert_pending``) is
exercised against a tiny fake ``asyncpg`` connection injected via ``sys.modules``.
Loaded by file path (the module is a plain file under ``botsite/``).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MODULE = _REPO_ROOT / "botsite" / "submissions_db.py"


@pytest.fixture(scope="module")
def sdb():
    spec = importlib.util.spec_from_file_location("botsite_submissions_db_ut", _MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# build_insert — validation + sanitation (pure, no DB)
# ---------------------------------------------------------------------------


def test_build_insert_always_inserts_pending(sdb):
    sql, params = sdb.build_insert(kind="bug", title="t", body="b")
    # The status literal is hard-coded 'pending' in the SQL — this module cannot
    # insert any other status (plan §2.3).
    assert "'pending'" in sql
    assert "status" not in sql.split("VALUES")[1] or "'pending'" in sql
    assert params[0] == "bug"
    assert params[1] == "t"
    assert params[2] == "b"


def test_build_insert_rejects_unknown_kind(sdb):
    with pytest.raises(sdb.SubmissionValidationError, match="kind"):
        sdb.build_insert(kind="malware", title="t", body="b")


def test_build_insert_requires_title_and_body(sdb):
    with pytest.raises(sdb.SubmissionValidationError, match="title"):
        sdb.build_insert(kind="bug", title="   ", body="b")
    with pytest.raises(sdb.SubmissionValidationError, match="body"):
        sdb.build_insert(kind="suggestion", title="t", body="")


def test_build_insert_length_caps(sdb):
    long_title = "x" * (sdb.MAX_TITLE_LEN + 50)
    long_body = "y" * (sdb.MAX_BODY_LEN + 50)
    _, params = sdb.build_insert(kind="bug", title=long_title, body=long_body)
    assert len(params[1]) == sdb.MAX_TITLE_LEN
    assert len(params[2]) == sdb.MAX_BODY_LEN


def test_build_insert_strips_control_chars(sdb):
    # A crafted payload with an escape sequence must be neutralised, newlines kept.
    _, params = sdb.build_insert(
        kind="bug",
        title="ok\x1b[31mevil",
        body="line1\nline2\x07",
    )
    assert "\x1b" not in params[1]
    assert params[1] == "ok[31mevil"
    assert "\n" in params[2]  # newline preserved
    assert "\x07" not in params[2]  # bell stripped


def test_build_insert_optional_fields_null_when_blank(sdb):
    _, params = sdb.build_insert(
        kind="suggestion",
        title="t",
        body="b",
        surface="   ",
        contact="",
    )
    # surface (params[3]) + contact (params[4]) → None when blank.
    assert params[3] is None
    assert params[4] is None


def test_build_insert_keeps_surface_and_contact_when_present(sdb):
    _, params = sdb.build_insert(
        kind="bug",
        title="t",
        body="b",
        surface="Discord bot",
        contact="me@example.com",
    )
    assert params[3] == "Discord bot"
    assert params[4] == "me@example.com"


# ---------------------------------------------------------------------------
# hash_ip — salted, never the raw IP
# ---------------------------------------------------------------------------


def test_hash_ip_is_salted_and_not_raw(sdb):
    raw = "203.0.113.7"
    hashed = sdb.hash_ip(raw)
    assert hashed is not None
    assert raw not in hashed  # never store the raw IP
    assert len(hashed) == 64  # sha256 hexdigest
    # Deterministic within a process (same salt) → forensic dedup works.
    assert sdb.hash_ip(raw) == hashed
    # Different IPs hash differently.
    assert sdb.hash_ip("198.51.100.1") != hashed


def test_hash_ip_none_for_empty(sdb):
    assert sdb.hash_ip(None) is None
    assert sdb.hash_ip("") is None


# ---------------------------------------------------------------------------
# dormant-by-default
# ---------------------------------------------------------------------------


def test_is_configured_reflects_dsn_env(sdb, monkeypatch):
    monkeypatch.delenv("SUBMISSIONS_DB_DSN", raising=False)
    assert sdb.is_configured() is False
    assert sdb.dsn() is None
    monkeypatch.setenv("SUBMISSIONS_DB_DSN", "postgres://x")
    assert sdb.is_configured() is True


async def test_insert_pending_raises_when_dormant(sdb, monkeypatch):
    monkeypatch.delenv("SUBMISSIONS_DB_DSN", raising=False)
    with pytest.raises(sdb.SubmissionsNotConfiguredError):
        await sdb.insert_pending(kind="bug", title="t", body="b")


# ---------------------------------------------------------------------------
# insert_pending — the I/O path against a fake asyncpg connection
# ---------------------------------------------------------------------------


class _FakeConn:
    def __init__(self, record):
        self.record = record
        self.closed = False

    async def fetchval(self, sql, *params):
        self.record["sql"] = sql
        self.record["params"] = params
        return 4242

    async def close(self):
        self.closed = True


async def test_insert_pending_executes_and_returns_id(sdb, monkeypatch):
    monkeypatch.setenv("SUBMISSIONS_DB_DSN", "postgres://test")
    record: dict = {}
    fake_conn = _FakeConn(record)

    class _FakeAsyncpg:
        async def connect(self, target):  # noqa: ARG002 - signature parity
            record["dsn"] = target
            return fake_conn

    monkeypatch.setitem(sys.modules, "asyncpg", _FakeAsyncpg())

    new_id = await sdb.insert_pending(
        kind="bug",
        title="It broke",
        body="steps",
        surface="Discord bot",
        source_ip="203.0.113.9",
    )
    assert new_id == 4242
    assert record["dsn"] == "postgres://test"
    assert record["sql"].startswith("INSERT INTO submissions")
    assert "'pending'" in record["sql"]
    # Params carry the salted IP hash (last positional), never the raw IP.
    assert record["params"][-1] != "203.0.113.9"
    assert record["params"][-1] is not None
    assert fake_conn.closed is True  # connection always closed
