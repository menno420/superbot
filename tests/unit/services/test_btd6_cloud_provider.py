"""Tests for the BTD6 cloud (object-store) raw-fixture provider.

Covers warm-cache success, the three resilience scenarios that also need
live confirmation (blackhole + no cache, blackhole + warm cache, manifest
checksum mismatch), optional-fixture tolerance, and config-driven provider
selection. All network is mocked via an injected ``fetcher`` — no aiohttp,
no real I/O.
"""

from __future__ import annotations

import json

import pytest

from services.btd6_data_provider import (
    DATA_ROOT,
    CloudRawProvider,
    FileRawProvider,
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

_BASE = "https://cdn.example/btd6"


def _real_fetcher(*, fail=(), manifest=None):
    """Async fetcher serving the committed fixtures (so get_dataset parses).

    ``fail`` names raise (simulate 404/network error); ``manifest`` (a dict)
    is served for manifest.json, else manifest.json raises (absent).
    """
    fail_set = set(fail)

    async def fetch(url: str) -> bytes:
        name = url.rsplit("/", 1)[-1]
        if name in fail_set:
            raise RuntimeError(f"simulated failure for {name}")
        if name == "manifest.json":
            if manifest is None:
                raise RuntimeError("no manifest")
            return json.dumps(manifest).encode("utf-8")
        path = DATA_ROOT / name
        if not path.exists():
            raise RuntimeError(f"404 {name}")
        return path.read_bytes()

    return fetch


async def _blackhole(url: str) -> bytes:
    raise RuntimeError("network down")


@pytest.fixture(autouse=True)
def _restore_provider():
    original = get_provider()
    reset_cache()
    yield
    set_provider(original)
    reset_cache()


@pytest.mark.asyncio
async def test_warm_success_populates_cache_and_drives_get_dataset(tmp_path):
    provider = CloudRawProvider(_BASE, tmp_path, fetcher=_real_fetcher())
    ok = await provider.warm_cache(
        required=_REQUIRED_FIXTURES,
        optional=_OPTIONAL_FIXTURES,
    )
    assert ok is True
    assert provider.is_available() is True
    assert "cached" in provider.source_label()
    raw = provider.load("towers.json")
    assert raw is not None and "towers" in raw

    set_provider(provider)
    reset_cache()
    assert get_dataset().towers  # end-to-end through the cache


@pytest.mark.asyncio
async def test_blackhole_no_cache_is_unavailable(tmp_path):
    provider = CloudRawProvider(_BASE, tmp_path, fetcher=_blackhole)
    ok = await provider.warm_cache(required=_REQUIRED_FIXTURES)
    assert ok is False
    assert provider.is_available() is False
    assert "unavailable" in provider.source_label()


@pytest.mark.asyncio
async def test_blackhole_with_warm_cache_serves_cache(tmp_path):
    # Pre-populate the cache (simulating a prior successful warm).
    for name in _REQUIRED_FIXTURES:
        (tmp_path / name).write_bytes((DATA_ROOT / name).read_bytes())
    provider = CloudRawProvider(_BASE, tmp_path, fetcher=_blackhole)
    ok = await provider.warm_cache(required=_REQUIRED_FIXTURES)
    assert ok is True  # cached copies satisfy availability
    assert provider.load("towers.json") is not None


@pytest.mark.asyncio
async def test_manifest_checksum_mismatch_flags_stale(tmp_path):
    manifest = {"files": {"towers.json": {"sha256": "deadbeef"}}}
    provider = CloudRawProvider(
        _BASE,
        tmp_path,
        fetcher=_real_fetcher(manifest=manifest),
    )
    ok = await provider.warm_cache(required=_REQUIRED_FIXTURES)
    assert ok is True  # still available, just flagged
    assert "towers.json" in provider.stale
    assert "stale" in provider.source_label()


@pytest.mark.asyncio
async def test_optional_fixture_absent_is_tolerated(tmp_path):
    provider = CloudRawProvider(
        _BASE,
        tmp_path,
        fetcher=_real_fetcher(fail=("bloons.json", "ct_relics.json")),
    )
    ok = await provider.warm_cache(
        required=_REQUIRED_FIXTURES,
        optional=_OPTIONAL_FIXTURES,
    )
    assert ok is True


def test_select_provider_file_when_url_unset(monkeypatch):
    import config

    monkeypatch.setattr(config, "BTD6_DATA_BASE_URL", "", raising=False)
    assert isinstance(_select_provider(), FileRawProvider)


def test_select_provider_cloud_when_url_set(monkeypatch):
    import config

    monkeypatch.setattr(config, "BTD6_DATA_BASE_URL", _BASE, raising=False)
    monkeypatch.setattr(config, "BTD6_DATA_CACHE_DIR", "", raising=False)
    provider = _select_provider()
    assert isinstance(provider, CloudRawProvider)
    assert provider.base_url == _BASE


@pytest.mark.asyncio
async def test_warm_provider_is_noop_for_file_provider():
    set_provider(FileRawProvider())
    assert await warm_provider() is True
    assert data_available() is True


@pytest.mark.asyncio
async def test_warm_provider_integrates_cloud_into_get_dataset(tmp_path):
    set_provider(CloudRawProvider(_BASE, tmp_path, fetcher=_real_fetcher()))
    assert await warm_provider() is True
    assert data_available() is True
    assert get_dataset().heroes
