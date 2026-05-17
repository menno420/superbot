"""Tests for core.runtime.guild_config — F-1 cached-config primitive."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

import pytest

from core.runtime import guild_config

T = TypeVar("T")


@pytest.fixture(autouse=True)
def _reset():
    guild_config._reset_for_tests()
    yield
    guild_config._reset_for_tests()


# ---------------------------------------------------------------------------
# Loader helpers
# ---------------------------------------------------------------------------


def _const_loader(value: T) -> Callable[[], Awaitable[T]]:
    """Return an async loader that yields ``value`` and counts invocations."""

    async def _loader() -> T:
        return value

    return _loader


def _counting_loader(value: T) -> tuple[Callable[[], Awaitable[T]], list[int]]:
    """Return ``(loader, calls)`` where ``calls[0]`` tracks invocations."""
    calls = [0]

    async def _loader() -> T:
        calls[0] += 1
        return value

    return _loader, calls


# ---------------------------------------------------------------------------
# get / get_many
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_loads_on_miss():
    loader, calls = _counting_loader("v1")
    result = await guild_config.get(1, "k", loader=loader)
    assert result == "v1"
    assert calls[0] == 1


@pytest.mark.asyncio
async def test_get_hits_cache_on_repeat():
    loader, calls = _counting_loader("v1")
    for _ in range(5):
        result = await guild_config.get(1, "k", loader=loader)
        assert result == "v1"
    assert calls[0] == 1  # loader invoked exactly once


@pytest.mark.asyncio
async def test_get_isolates_per_guild():
    loader_a, calls_a = _counting_loader("A")
    loader_b, calls_b = _counting_loader("B")
    assert await guild_config.get(1, "k", loader=loader_a) == "A"
    assert await guild_config.get(2, "k", loader=loader_b) == "B"
    assert calls_a[0] == 1 and calls_b[0] == 1
    # Re-read each — both still served from cache
    assert await guild_config.get(1, "k", loader=loader_a) == "A"
    assert await guild_config.get(2, "k", loader=loader_b) == "B"
    assert calls_a[0] == 1 and calls_b[0] == 1


@pytest.mark.asyncio
async def test_get_isolates_per_key():
    loader_a, calls_a = _counting_loader("A")
    loader_b, calls_b = _counting_loader("B")
    assert await guild_config.get(1, "a", loader=loader_a) == "A"
    assert await guild_config.get(1, "b", loader=loader_b) == "B"
    assert calls_a[0] == 1 and calls_b[0] == 1


@pytest.mark.asyncio
async def test_get_many_partial_hit_invokes_loader_only_for_missing_keys():
    # Pre-warm one key.
    await guild_config.get(1, "a", loader=_const_loader("A"))

    received_keys: list[list[str]] = []

    async def batch_loader(keys: list[str]) -> dict[str, str]:
        received_keys.append(list(keys))
        return {k: k.upper() for k in keys}

    result = await guild_config.get_many(1, ["a", "b", "c"], loader=batch_loader)
    assert result == {"a": "A", "b": "B", "c": "C"}
    # Loader called once, only with the missed keys (in order).
    assert received_keys == [["b", "c"]]


@pytest.mark.asyncio
async def test_get_many_all_hits_skips_loader():
    await guild_config.get(1, "a", loader=_const_loader("A"))
    await guild_config.get(1, "b", loader=_const_loader("B"))

    async def must_not_call(_: list[str]) -> dict[str, str]:
        raise AssertionError("loader called despite full hit")

    result = await guild_config.get_many(1, ["a", "b"], loader=must_not_call)
    assert result == {"a": "A", "b": "B"}


# ---------------------------------------------------------------------------
# invalidate / forget_guild
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalidate_specific_key_forces_reload():
    loader, calls = _counting_loader("v")
    await guild_config.get(1, "k", loader=loader)  # calls=1
    guild_config.invalidate(1, "k")
    await guild_config.get(1, "k", loader=loader)  # calls=2
    assert calls[0] == 2


@pytest.mark.asyncio
async def test_invalidate_specific_key_does_not_disturb_others():
    loader_a, calls_a = _counting_loader("A")
    loader_b, calls_b = _counting_loader("B")
    await guild_config.get(1, "a", loader=loader_a)
    await guild_config.get(1, "b", loader=loader_b)
    guild_config.invalidate(1, "a")
    # Key 'a' reloads, key 'b' still cached
    await guild_config.get(1, "a", loader=loader_a)
    await guild_config.get(1, "b", loader=loader_b)
    assert calls_a[0] == 2
    assert calls_b[0] == 1


@pytest.mark.asyncio
async def test_invalidate_guild_bumps_version_for_all_keys():
    loader_a, calls_a = _counting_loader("A")
    loader_b, calls_b = _counting_loader("B")
    await guild_config.get(1, "a", loader=loader_a)
    await guild_config.get(1, "b", loader=loader_b)
    guild_config.invalidate(1)  # full-guild
    await guild_config.get(1, "a", loader=loader_a)
    await guild_config.get(1, "b", loader=loader_b)
    assert calls_a[0] == 2
    assert calls_b[0] == 2


@pytest.mark.asyncio
async def test_invalidate_guild_does_not_disturb_other_guild():
    loader_g1, calls_g1 = _counting_loader("g1")
    loader_g2, calls_g2 = _counting_loader("g2")
    await guild_config.get(1, "k", loader=loader_g1)
    await guild_config.get(2, "k", loader=loader_g2)
    guild_config.invalidate(1)
    await guild_config.get(1, "k", loader=loader_g1)  # reload
    await guild_config.get(2, "k", loader=loader_g2)  # cached
    assert calls_g1[0] == 2
    assert calls_g2[0] == 1


@pytest.mark.asyncio
async def test_forget_guild_clears_entries_and_version():
    await guild_config.get(1, "k", loader=_const_loader("v"))
    await guild_config.get(2, "k", loader=_const_loader("v"))
    assert guild_config.stats().size == 2
    assert guild_config.stats().versions_tracked == 2

    guild_config.forget_guild(1)

    stats = guild_config.stats()
    assert stats.size == 1
    assert stats.versions_tracked == 1  # only guild 2 retained


# ---------------------------------------------------------------------------
# TTL + lazy cleanup
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ttl_expiry_treats_entry_as_miss():
    loader, calls = _counting_loader("v")
    await guild_config.get(1, "k", loader=loader)
    # Backdate the cache entry past the TTL window.
    for composite, (ts, value) in list(guild_config._CACHE.items()):
        guild_config._CACHE[composite] = (
            ts - guild_config.DEFAULT_TTL_SECONDS - 1.0,
            value,
        )
    await guild_config.get(1, "k", loader=loader)
    assert calls[0] == 2


@pytest.mark.asyncio
async def test_cleanup_threshold_evicts_stale_entries(monkeypatch):
    monkeypatch.setattr(guild_config, "CACHE_CLEANUP_THRESHOLD", 5)
    for i in range(5):
        await guild_config.get(1, f"k{i}", loader=_const_loader(i))
    # Backdate everything past TTL.
    for composite, (ts, value) in list(guild_config._CACHE.items()):
        guild_config._CACHE[composite] = (
            ts - guild_config.DEFAULT_TTL_SECONDS - 1.0,
            value,
        )
    # Next write crosses threshold and triggers _evict_stale().
    await guild_config.get(2, "fresh", loader=_const_loader("F"))
    assert guild_config.stats().size == 1  # only the fresh entry survives


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------


def test_stats_empty_after_reset():
    s = guild_config.stats()
    assert s.size == 0
    assert s.versions_tracked == 0


@pytest.mark.asyncio
async def test_stats_tracks_size_and_versions():
    await guild_config.get(1, "a", loader=_const_loader("A"))
    await guild_config.get(1, "b", loader=_const_loader("B"))
    await guild_config.get(2, "a", loader=_const_loader("A"))
    s = guild_config.stats()
    assert s.size == 3
    assert s.versions_tracked == 2
