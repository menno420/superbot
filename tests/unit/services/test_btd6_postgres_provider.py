"""Tests for the BTD6 Postgres raw-fixture provider + backend selection.

The DB layer is mocked via an injected ``fetch_all``, so these run offline —
no real Postgres — mirroring how the rest of the codebase tests DB-touching
code. Drives ``get_dataset`` end-to-end through the warmed blob cache.
"""

from __future__ import annotations

import json

import pytest

from services.btd6_data_provider import (
    DATA_ROOT,
    FileRawProvider,
    PostgresRawProvider,
)
from services.btd6_data_service import (
    _OPTIONAL_FIXTURES,
    _REQUIRED_FIXTURES,
    _select_provider,
    data_available,
    get_dataset,
    get_provider,
    reset_cache,
    set_provider,
    warm_provider,
)


def _blobs_from_disk(*, skip=()):
    """``(name, body-dict)`` rows mimicking ``btd6_data_blobs`` (jsonb codec)."""
    rows = []
    for name in (*_REQUIRED_FIXTURES, *_OPTIONAL_FIXTURES):
        if name in skip:
            continue
        path = DATA_ROOT / name
        if path.exists():
            rows.append((name, json.loads(path.read_text(encoding="utf-8"))))
    return rows


def _fetch_all(rows):
    async def fetch():
        return list(rows)

    return fetch


@pytest.fixture(autouse=True)
def _restore_provider():
    original = get_provider()
    reset_cache()
    yield
    set_provider(original)
    reset_cache()


@pytest.mark.asyncio
async def test_warm_populates_and_drives_get_dataset():
    provider = PostgresRawProvider(fetch_all=_fetch_all(_blobs_from_disk()))
    ok = await provider.warm_cache(
        required=_REQUIRED_FIXTURES,
        optional=_OPTIONAL_FIXTURES,
    )
    assert ok is True
    assert provider.is_available() is True
    assert "blobs" in provider.source_label()
    towers = provider.load("towers.json")
    assert towers is not None and "towers" in towers

    set_provider(provider)
    reset_cache()
    assert get_dataset().towers  # end-to-end through the warmed cache


@pytest.mark.asyncio
async def test_unseeded_table_is_unavailable():
    provider = PostgresRawProvider(fetch_all=_fetch_all([]))
    ok = await provider.warm_cache(required=_REQUIRED_FIXTURES)
    assert ok is False
    assert provider.is_available() is False
    assert "unavailable" in provider.source_label()


@pytest.mark.asyncio
async def test_coerces_text_bodies():
    # A row that round-trips as JSON *text* (no codec) must still parse.
    rows = [
        (n, json.dumps(json.loads((DATA_ROOT / n).read_text(encoding="utf-8"))))
        for n in _REQUIRED_FIXTURES
    ]
    provider = PostgresRawProvider(fetch_all=_fetch_all(rows))
    assert await provider.warm_cache(required=_REQUIRED_FIXTURES) is True
    towers = provider.load("towers.json")
    assert towers is not None and towers["towers"]


@pytest.mark.asyncio
async def test_list_names_prefix():
    rows = [
        ("towers.json", {}),
        ("stats/dart_monkey.json", {}),
        ("stats/heroes/quincy.json", {}),
    ]
    provider = PostgresRawProvider(fetch_all=_fetch_all(rows))
    await provider.warm_cache()
    assert provider.list_names("stats/") == (
        "stats/dart_monkey.json",
        "stats/heroes/quincy.json",
    )
    assert provider.list_names("stats/heroes/") == ("stats/heroes/quincy.json",)


@pytest.mark.asyncio
async def test_warm_provider_integrates_postgres():
    set_provider(PostgresRawProvider(fetch_all=_fetch_all(_blobs_from_disk())))
    assert await warm_provider() is True
    assert data_available() is True
    assert get_dataset().heroes


def test_select_provider_postgres(monkeypatch):
    import config

    monkeypatch.setattr(config, "BTD6_DATA_BACKEND", "postgres", raising=False)
    assert isinstance(_select_provider(), PostgresRawProvider)


def test_select_provider_file_default(monkeypatch):
    import config

    monkeypatch.setattr(config, "BTD6_DATA_BACKEND", "", raising=False)
    monkeypatch.setattr(config, "BTD6_DATA_BASE_URL", "", raising=False)
    assert isinstance(_select_provider(), FileRawProvider)
