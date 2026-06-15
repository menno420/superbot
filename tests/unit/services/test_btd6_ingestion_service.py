"""Unit tests for btd6_ingestion_service — covers all status transitions.

All external I/O (registry, fetch, parser, fact store, DB) is mocked.
No real NK API or DB connections are used.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_ingestion_service  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_SOURCE = {
    "id": 1,
    "source_key": "nk_btd6_ct",
    "enabled": True,
    "base_url": "https://data.ninjakiwi.com",
}

_FAKE_FACT_RESULT = MagicMock(entity_key="ct_123")
_FAKE_FETCH_RESULT = MagicMock(
    status_code=200,
    raw_body=json.dumps({"body": [{"id": "ct_123"}]}),
    raw_body_hash="abc123",
)

_FAKE_PARSER = MagicMock()
_FAKE_PARSER.parse.return_value = [
    MagicMock(
        fact_type="ct_index",
        entity_kind="btd6_ct",
        entity_key="ct_123",
        body_json={},
        game_version=None,
        confidence=1.0,
    )
]


def _clear_locks():
    btd6_ingestion_service._locks.clear()


@pytest.fixture(autouse=True)
def reset_locks():
    _clear_locks()
    yield
    _clear_locks()


# ---------------------------------------------------------------------------
# ok path
# ---------------------------------------------------------------------------


async def test_ok_path(monkeypatch):
    monkeypatch.setattr(
        "services.btd6_source_registry.get_by_key", AsyncMock(return_value=_FAKE_SOURCE)
    )
    monkeypatch.setattr(
        "services.btd6_fetch_service.fetch", AsyncMock(return_value=_FAKE_FETCH_RESULT)
    )
    monkeypatch.setattr(
        "services.btd6_source_parser.get", MagicMock(return_value=_FAKE_PARSER)
    )
    monkeypatch.setattr(
        "services.btd6_fact_store.store_facts",
        AsyncMock(return_value=[_FAKE_FACT_RESULT]),
    )
    monkeypatch.setattr(
        "utils.db.btd6_sources.insert_ingestion_run", AsyncMock(return_value=7)
    )
    monkeypatch.setattr("utils.db.btd6_sources.update_ingestion_run", AsyncMock())
    monkeypatch.setattr("utils.db.btd6_sources.insert_source_snapshot", AsyncMock())

    result = await btd6_ingestion_service.refresh_source("nk_btd6_ct")

    assert result.status == "ok"
    assert result.fact_count == 1
    assert result.run_id == 7
    assert "ct_123" in result.written_entity_keys


# ---------------------------------------------------------------------------
# skipped — lock already held
# ---------------------------------------------------------------------------


async def test_skipped_when_lock_held(monkeypatch):
    monkeypatch.setattr(
        "services.btd6_source_registry.get_by_key", AsyncMock(return_value=_FAKE_SOURCE)
    )
    monkeypatch.setattr(
        "utils.db.btd6_sources.insert_ingestion_run", AsyncMock(return_value=8)
    )

    lock = await btd6_ingestion_service._lock_for("nk_btd6_ct", "")
    await lock.acquire()
    try:
        result = await btd6_ingestion_service.refresh_source("nk_btd6_ct")
        assert result.status == "skipped"
        assert result.run_id == 8
    finally:
        lock.release()


# ---------------------------------------------------------------------------
# disabled / source_not_registered
# ---------------------------------------------------------------------------


async def test_unknown_source_no_run_row(monkeypatch):
    monkeypatch.setattr(
        "services.btd6_source_registry.get_by_key", AsyncMock(return_value=None)
    )
    insert_mock = AsyncMock()
    monkeypatch.setattr("utils.db.btd6_sources.insert_ingestion_run", insert_mock)

    result = await btd6_ingestion_service.refresh_source("no_such_source")

    assert result.status == "disabled"
    assert result.error_code == "source_not_registered"
    assert result.run_id is None
    insert_mock.assert_not_called()


# ---------------------------------------------------------------------------
# fetch_error
# ---------------------------------------------------------------------------


async def test_fetch_http_error(monkeypatch):
    from services.btd6_fetch_service import BTD6FetchHTTPError

    monkeypatch.setattr(
        "services.btd6_source_registry.get_by_key", AsyncMock(return_value=_FAKE_SOURCE)
    )
    monkeypatch.setattr(
        "services.btd6_fetch_service.fetch",
        AsyncMock(
            side_effect=BTD6FetchHTTPError("nk_btd6_ct", 503, "service unavailable")
        ),
    )
    monkeypatch.setattr(
        "utils.db.btd6_sources.insert_ingestion_run", AsyncMock(return_value=9)
    )
    update_mock = AsyncMock()
    monkeypatch.setattr("utils.db.btd6_sources.update_ingestion_run", update_mock)

    result = await btd6_ingestion_service.refresh_source("nk_btd6_ct")

    assert result.status == "fetch_error"
    assert result.error_code == "503"
    update_mock.assert_called_once()
    call_kwargs = update_mock.call_args.kwargs
    assert call_kwargs["status"] == "fetch_error"


# ---------------------------------------------------------------------------
# disabled from fetch refused
# ---------------------------------------------------------------------------


async def test_fetch_refused_marks_disabled(monkeypatch):
    from services.btd6_fetch_service import BTD6FetchRefusedError

    monkeypatch.setattr(
        "services.btd6_source_registry.get_by_key", AsyncMock(return_value=_FAKE_SOURCE)
    )
    monkeypatch.setattr(
        "services.btd6_fetch_service.fetch",
        AsyncMock(side_effect=BTD6FetchRefusedError("nk_btd6_ct", "source_disabled")),
    )
    monkeypatch.setattr(
        "utils.db.btd6_sources.insert_ingestion_run", AsyncMock(return_value=10)
    )
    update_mock = AsyncMock()
    monkeypatch.setattr("utils.db.btd6_sources.update_ingestion_run", update_mock)

    result = await btd6_ingestion_service.refresh_source("nk_btd6_ct")

    assert result.status == "disabled"
    assert result.error_code == "source_disabled"


# ---------------------------------------------------------------------------
# parse_error — invalid JSON
# ---------------------------------------------------------------------------


async def test_invalid_json_body(monkeypatch):
    bad_fetch = MagicMock(
        status_code=200, raw_body="not json at all", raw_body_hash="x"
    )
    monkeypatch.setattr(
        "services.btd6_source_registry.get_by_key", AsyncMock(return_value=_FAKE_SOURCE)
    )
    monkeypatch.setattr(
        "services.btd6_fetch_service.fetch", AsyncMock(return_value=bad_fetch)
    )
    monkeypatch.setattr(
        "services.btd6_source_parser.get", MagicMock(return_value=_FAKE_PARSER)
    )
    monkeypatch.setattr(
        "utils.db.btd6_sources.insert_ingestion_run", AsyncMock(return_value=11)
    )
    monkeypatch.setattr("utils.db.btd6_sources.insert_source_snapshot", AsyncMock())
    update_mock = AsyncMock()
    monkeypatch.setattr("utils.db.btd6_sources.update_ingestion_run", update_mock)

    result = await btd6_ingestion_service.refresh_source("nk_btd6_ct")

    assert result.status == "parse_error"
    assert result.error_code == "invalid_json"


# ---------------------------------------------------------------------------
# parse_error — no parser registered
# ---------------------------------------------------------------------------


async def test_no_parser_registered(monkeypatch):
    monkeypatch.setattr(
        "services.btd6_source_registry.get_by_key", AsyncMock(return_value=_FAKE_SOURCE)
    )
    monkeypatch.setattr(
        "services.btd6_fetch_service.fetch", AsyncMock(return_value=_FAKE_FETCH_RESULT)
    )
    monkeypatch.setattr("services.btd6_source_parser.get", MagicMock(return_value=None))
    monkeypatch.setattr(
        "utils.db.btd6_sources.insert_ingestion_run", AsyncMock(return_value=12)
    )
    monkeypatch.setattr("utils.db.btd6_sources.insert_source_snapshot", AsyncMock())
    update_mock = AsyncMock()
    monkeypatch.setattr("utils.db.btd6_sources.update_ingestion_run", update_mock)

    result = await btd6_ingestion_service.refresh_source("nk_btd6_ct")

    assert result.status == "parse_error"
    assert result.error_code == "no_parser"


# ---------------------------------------------------------------------------
# snapshot written on successful fetch
# ---------------------------------------------------------------------------


async def test_snapshot_written_on_ok(monkeypatch):
    monkeypatch.setattr(
        "services.btd6_source_registry.get_by_key", AsyncMock(return_value=_FAKE_SOURCE)
    )
    monkeypatch.setattr(
        "services.btd6_fetch_service.fetch", AsyncMock(return_value=_FAKE_FETCH_RESULT)
    )
    monkeypatch.setattr(
        "services.btd6_source_parser.get", MagicMock(return_value=_FAKE_PARSER)
    )
    monkeypatch.setattr(
        "services.btd6_fact_store.store_facts",
        AsyncMock(return_value=[_FAKE_FACT_RESULT]),
    )
    monkeypatch.setattr(
        "utils.db.btd6_sources.insert_ingestion_run", AsyncMock(return_value=13)
    )
    monkeypatch.setattr("utils.db.btd6_sources.update_ingestion_run", AsyncMock())
    snapshot_mock = AsyncMock()
    monkeypatch.setattr("utils.db.btd6_sources.insert_source_snapshot", snapshot_mock)

    await btd6_ingestion_service.refresh_source("nk_btd6_ct")

    snapshot_mock.assert_called_once()
    call_kwargs = snapshot_mock.call_args.kwargs
    assert call_kwargs["source_id"] == 1
    assert call_kwargs["status_code"] == 200


# ---------------------------------------------------------------------------
# refresh_with_dependencies — child fetches driven by written_entity_keys
# ---------------------------------------------------------------------------


async def test_refresh_with_dependencies_triggers_child(monkeypatch):
    child_calls: list[tuple[str, dict | None]] = []

    async def _mock_refresh(
        source_key, *, path_params=None, reason="scheduled", started_by_user_id=None
    ):
        child_calls.append((source_key, path_params))
        if source_key == "nk_btd6_ct":
            return btd6_ingestion_service.IngestionResult(
                source_key=source_key,
                status="ok",
                fact_count=1,
                duration_ms=10,
                error_code=None,
                run_id=1,
                written_entity_keys=("ct_999",),
            )
        return btd6_ingestion_service.IngestionResult(
            source_key=source_key,
            status="ok",
            fact_count=2,
            duration_ms=10,
            error_code=None,
            run_id=2,
        )

    monkeypatch.setattr(btd6_ingestion_service, "refresh_source", _mock_refresh)

    results = await btd6_ingestion_service.refresh_with_dependencies("nk_btd6_ct")

    assert len(results) == 2
    assert results[0].source_key == "nk_btd6_ct"
    assert results[1].source_key == "nk_btd6_ct_tiles"
    assert results[1].status == "ok"
    assert child_calls[1] == ("nk_btd6_ct_tiles", {"ctID": "ct_999"})


async def test_refresh_with_dependencies_no_children_on_failure(monkeypatch):
    async def _mock_refresh(source_key, **kwargs):
        return btd6_ingestion_service.IngestionResult(
            source_key=source_key,
            status="fetch_error",
            fact_count=0,
            duration_ms=5,
            error_code="503",
            run_id=1,
        )

    monkeypatch.setattr(btd6_ingestion_service, "refresh_source", _mock_refresh)

    results = await btd6_ingestion_service.refresh_with_dependencies("nk_btd6_ct")

    assert len(results) == 1
    assert results[0].status == "fetch_error"
