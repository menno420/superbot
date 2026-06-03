"""btd6_patch_service — patch_notes ingestion seam + new-version detection."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_patch_service  # noqa: E402


@pytest.fixture()
def _mock_bus(monkeypatch):
    """Replace the module's EventBus with a capture mock."""
    bus = MagicMock()
    bus.emit = AsyncMock()
    monkeypatch.setattr("services.btd6_patch_service.bus", bus)
    return bus


def _patch_db(monkeypatch, *, latest, upsert=None):
    monkeypatch.setattr(
        "utils.db.btd6_sources.latest_patch_note",
        AsyncMock(return_value=latest),
    )
    monkeypatch.setattr(
        "utils.db.btd6_sources.upsert_patch_note",
        upsert or AsyncMock(return_value=1),
    )


# ---------------------------------------------------------------------------
# _version_key
# ---------------------------------------------------------------------------


def test_version_key_orders_numerically():
    key = btd6_patch_service._version_key
    assert key("9.0") < key("10.0")  # not a string compare
    assert key("54.0") > key("53.9")
    assert key("54.1") > key("54.0")
    assert key("garbage") == ()  # unparseable sorts below every real version


# ---------------------------------------------------------------------------
# store_parsed_notes — storage
# ---------------------------------------------------------------------------


async def test_store_parsed_notes_upserts_each_valid_record(monkeypatch, _mock_bus):
    upsert = AsyncMock(return_value=1)
    _patch_db(monkeypatch, latest=None, upsert=upsert)

    records = [
        {"version": "54.0", "body": "tower changes", "published_at": None},
        {"version": "46.0", "body": "new hero", "published_at": None},
    ]
    written = await btd6_patch_service.store_parsed_notes(records, source_id=7)

    assert written == ["54.0", "46.0"]
    assert upsert.await_count == 2
    assert upsert.await_args_list[0].kwargs["source_id"] == 7
    assert upsert.await_args_list[1].kwargs["version"] == "46.0"


async def test_store_parsed_notes_skips_empty_version_or_body(monkeypatch, _mock_bus):
    upsert = AsyncMock(return_value=1)
    _patch_db(monkeypatch, latest=None, upsert=upsert)

    records = [
        {"version": "", "body": "no version"},
        {"version": "54.0", "body": "   "},
        {"version": "54.0", "body": "real notes"},
        {},
    ]
    written = await btd6_patch_service.store_parsed_notes(records, source_id=1)

    assert written == ["54.0"]
    assert upsert.await_count == 1


async def test_store_parsed_notes_empty_input(monkeypatch, _mock_bus):
    upsert = AsyncMock(return_value=1)
    _patch_db(monkeypatch, latest=None, upsert=upsert)

    written = await btd6_patch_service.store_parsed_notes([], source_id=1)

    assert written == []
    upsert.assert_not_called()
    _mock_bus.emit.assert_not_called()


# ---------------------------------------------------------------------------
# store_parsed_notes — new-version detection / emit
# ---------------------------------------------------------------------------


async def test_emits_on_strictly_newer_version(monkeypatch, _mock_bus):
    _patch_db(monkeypatch, latest={"version": "53.0"})

    records = [
        {"version": "54.0", "body": "notes", "title": "Update 54.0", "url": "u"},
        {"version": "46.0", "body": "old"},
    ]
    await btd6_patch_service.store_parsed_notes(records, source_id=1)

    _mock_bus.emit.assert_awaited_once()
    args, kwargs = _mock_bus.emit.await_args
    assert args[0] == btd6_patch_service.EVT_BTD6_VERSION_DETECTED
    assert kwargs["version"] == "54.0"
    assert kwargs["previous_version"] == "53.0"
    assert kwargs["title"] == "Update 54.0"
    assert kwargs["url"] == "u"


async def test_no_emit_when_not_newer(monkeypatch, _mock_bus):
    _patch_db(monkeypatch, latest={"version": "54.0"})

    records = [{"version": "54.0", "body": "same version re-ingested"}]
    await btd6_patch_service.store_parsed_notes(records, source_id=1)

    _mock_bus.emit.assert_not_called()


async def test_no_emit_on_baseline_first_ingest(monkeypatch, _mock_bus):
    # No previously-stored latest: establish the baseline silently.
    _patch_db(monkeypatch, latest=None)

    records = [{"version": "54.0", "body": "first ever ingest"}]
    await btd6_patch_service.store_parsed_notes(records, source_id=1)

    _mock_bus.emit.assert_not_called()


async def test_emit_uses_newest_version_when_multiple_new(monkeypatch, _mock_bus):
    # 9.0 vs 10.0 must compare numerically — the newest is 10.0, not "9.0".
    _patch_db(monkeypatch, latest={"version": "8.0"})

    records = [
        {"version": "9.0", "body": "a"},
        {"version": "10.0", "body": "b", "title": "Update 10.0"},
    ]
    await btd6_patch_service.store_parsed_notes(records, source_id=1)

    _mock_bus.emit.assert_awaited_once()
    assert _mock_bus.emit.await_args.kwargs["version"] == "10.0"


async def test_detection_read_failure_is_swallowed(monkeypatch, _mock_bus):
    # A failing previous-latest read degrades to baseline (no emit), and
    # must not raise out of store (rows still wrote).
    monkeypatch.setattr(
        "utils.db.btd6_sources.latest_patch_note",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    monkeypatch.setattr(
        "utils.db.btd6_sources.upsert_patch_note",
        AsyncMock(return_value=1),
    )

    written = await btd6_patch_service.store_parsed_notes(
        [{"version": "54.0", "body": "notes"}],
        source_id=1,
    )

    assert written == ["54.0"]
    _mock_bus.emit.assert_not_called()
