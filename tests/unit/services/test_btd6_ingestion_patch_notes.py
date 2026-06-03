"""Ingestion routing: ``patch_notes`` sources store via btd6_patch_service.

The generic fact store (``store_facts``) is the default sink, but
``source_kind='patch_notes'`` rows (e.g. ``steam_btd6_news``) own the
dedicated ``btd6_patch_notes`` table read by ``btd6_knowledge_api``. This
pins that the ingestion service routes them to
``btd6_patch_service.store_parsed_notes`` and never to the fact store.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_ingestion_service  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_locks():
    btd6_ingestion_service._locks.clear()
    yield
    btd6_ingestion_service._locks.clear()


_PATCH_SOURCE = {
    "id": 42,
    "source_key": "steam_btd6_news",
    "enabled": True,
    "base_url": "https://api.steampowered.com",
    "source_kind": "patch_notes",
}

_FETCH = MagicMock(
    status_code=200,
    raw_body=json.dumps({"appnews": {"newsitems": []}}),
    raw_body_hash="hash",
)

_PARSER = MagicMock()
_PARSER.parse.return_value = [
    {"version": "54.0", "body": "tower changes", "published_at": None},
]


async def test_patch_notes_source_routes_to_patch_service(monkeypatch):
    monkeypatch.setattr(
        "services.btd6_source_registry.get_by_key",
        AsyncMock(return_value=_PATCH_SOURCE),
    )
    monkeypatch.setattr(
        "services.btd6_fetch_service.fetch",
        AsyncMock(return_value=_FETCH),
    )
    monkeypatch.setattr(
        "services.btd6_source_parser.get",
        MagicMock(return_value=_PARSER),
    )
    store_notes = AsyncMock(return_value=["54.0"])
    monkeypatch.setattr(
        "services.btd6_patch_service.store_parsed_notes",
        store_notes,
    )
    store_facts = AsyncMock()
    monkeypatch.setattr("services.btd6_fact_store.store_facts", store_facts)
    monkeypatch.setattr(
        "utils.db.btd6_sources.insert_ingestion_run",
        AsyncMock(return_value=1),
    )
    monkeypatch.setattr("utils.db.btd6_sources.update_ingestion_run", AsyncMock())
    monkeypatch.setattr("utils.db.btd6_sources.insert_source_snapshot", AsyncMock())

    result = await btd6_ingestion_service.refresh_source("steam_btd6_news")

    assert result.status == "ok"
    assert result.fact_count == 1
    assert result.written_entity_keys == ("54.0",)
    store_notes.assert_awaited_once()
    # patch_notes routing must bypass the generic fact store entirely.
    store_facts.assert_not_called()
    # source_id from the registry row is threaded to the patch service.
    assert store_notes.await_args.kwargs["source_id"] == 42
