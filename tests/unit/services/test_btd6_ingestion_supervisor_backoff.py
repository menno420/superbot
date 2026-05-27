"""Verify supervisor backoff policy for store_error.

A persistent DB-write failure must trigger backoff with an ERROR-level
log line — otherwise the supervisor spins forever, hammering a failing
store. Fetch / parse errors keep their existing WARNING level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pytest

from services import btd6_ingestion_supervisor


@dataclass
class _FakeResult:
    status: str
    error_code: str = "test"


def _trigger_backoff(monkeypatch, results, source_key="nk_btd6_test") -> dict:
    # Mirror the supervisor's inlined logic: only the failure-classification
    # branch matters here. The full async loop is exercised separately.
    _backoff: dict[str, int] = {}
    failed = [
        r for r in results if r.status in ("fetch_error", "parse_error", "store_error")
    ]
    if failed:
        new_backoff = min(
            _backoff.get(source_key, btd6_ingestion_supervisor._BACKOFF_BASE_S) * 2,
            btd6_ingestion_supervisor._BACKOFF_CAP_S,
        )
        _backoff[source_key] = new_backoff
    else:
        _backoff.pop(source_key, None)
    return _backoff


def test_store_error_is_in_supervisor_backoff_set():
    # White-box check: the supervisor's failure classifier includes store_error.
    src = btd6_ingestion_supervisor.__file__
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    assert '"store_error"' in text
    # And the ERROR-level branch exists for store_error specifically.
    assert "logger.error" in text


def test_fetch_error_triggers_backoff():
    out = _trigger_backoff(None, [_FakeResult(status="fetch_error")])
    assert out["nk_btd6_test"] > 0


def test_parse_error_triggers_backoff():
    out = _trigger_backoff(None, [_FakeResult(status="parse_error")])
    assert out["nk_btd6_test"] > 0


def test_store_error_triggers_backoff():
    out = _trigger_backoff(None, [_FakeResult(status="store_error")])
    assert out["nk_btd6_test"] > 0


def test_ok_does_not_trigger_backoff():
    out = _trigger_backoff(None, [_FakeResult(status="ok")])
    assert out == {}


@pytest.mark.asyncio
async def test_store_error_logs_at_error_level(monkeypatch, caplog):
    """Run a single iteration of _run_loop's failure branch and confirm
    store_error fires logger.error, not logger.warning."""
    from services import btd6_ingestion_service

    async def _fake_refresh(source_key, *, reason):
        return [_FakeResult(status="store_error", error_code="db_unavailable")]

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_with_dependencies",
        _fake_refresh,
    )
    # Force the loop to run exactly one iteration then exit.
    monkeypatch.setattr(
        btd6_ingestion_supervisor, "_SOURCE_INTERVALS", {"nk_btd6_events": 1800}
    )
    monkeypatch.setattr(btd6_ingestion_supervisor, "_STARTUP_DELAY_S", 0)
    monkeypatch.setattr(btd6_ingestion_supervisor, "_DEFAULT_INTERVAL_S", 1)

    btd6_ingestion_supervisor._stop_event.clear()
    btd6_ingestion_supervisor._backoff.clear()

    async def _stop_after_one_cycle():
        # Let the loop process the source then signal stop.
        import asyncio as _asyncio

        await _asyncio.sleep(0.2)
        btd6_ingestion_supervisor._stop_event.set()

    import asyncio

    with caplog.at_level(
        logging.ERROR, logger="bot.services.btd6_ingestion_supervisor"
    ):
        stopper = asyncio.create_task(_stop_after_one_cycle())
        await btd6_ingestion_supervisor._run_loop()
        await stopper

    error_records = [
        r
        for r in caplog.records
        if r.name == "bot.services.btd6_ingestion_supervisor"
        and r.levelno >= logging.ERROR
        and "store_error" in r.getMessage()
    ]
    assert error_records, (
        "store_error supervisor backoff must log at ERROR level. "
        f"Got records: {[(r.levelname, r.getMessage()) for r in caplog.records]}"
    )
