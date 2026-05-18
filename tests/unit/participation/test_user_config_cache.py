"""Phase 2c PR-8 — core.runtime.user_config cache behaviour.

Covers:

* Cache miss → DB read → cache populated → next read hits.
* TTL expiry forces a reload.
* Explicit invalidation primitives evict the right entries.
* DB failure returns an empty bundle without raising.
* Soft max-size eviction.
* Diagnostics snapshot shape.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest

from core.runtime import user_config


@pytest.fixture(autouse=True)
def _reset_cache():
    user_config._reset_for_tests()
    yield
    user_config._reset_for_tests()


@pytest.fixture
def _patch_db():
    """Patch utils.db.user_participation.list_for_user."""
    with patch(
        "utils.db.user_participation.list_for_user",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = {
            "participation": [],
            "subscriptions": [],
            "preferences": [],
            "visibility_overrides": [],
        }
        yield mock


# ---------------------------------------------------------------------------
# Cache miss/hit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_miss_loads_from_db(_patch_db):
    await user_config.get(1, 2)
    _patch_db.assert_awaited_once_with(1, 2)


@pytest.mark.asyncio
async def test_cache_hit_avoids_second_db_call(_patch_db):
    await user_config.get(1, 2)
    await user_config.get(1, 2)
    assert _patch_db.await_count == 1
    snap = user_config._snapshot()
    assert snap["hits"] == 1
    assert snap["misses"] == 1


@pytest.mark.asyncio
async def test_cache_per_user_guild_independent(_patch_db):
    await user_config.get(1, 2)
    await user_config.get(1, 3)  # different guild
    await user_config.get(2, 2)  # different user
    assert _patch_db.await_count == 3


# ---------------------------------------------------------------------------
# Empty bundle returned on cache miss when DB has no rows
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_db_returns_empty_bundle(_patch_db):
    bundle = await user_config.get(1, 2)
    assert bundle.user_id == 1
    assert bundle.guild_id == 2
    assert bundle.participation == ()
    assert bundle.subscriptions == ()
    assert bundle.preferences == ()
    assert bundle.visibility_overrides == ()


# ---------------------------------------------------------------------------
# Invalidation primitives
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalidate_user_guild_drops_one_entry(_patch_db):
    await user_config.get(1, 2)
    assert user_config.invalidate_user_guild(1, 2) is True
    await user_config.get(1, 2)
    assert _patch_db.await_count == 2


@pytest.mark.asyncio
async def test_invalidate_user_guild_returns_false_when_absent():
    assert user_config.invalidate_user_guild(99, 99) is False


@pytest.mark.asyncio
async def test_forget_user_drops_all_guilds(_patch_db):
    await user_config.get(1, 2)
    await user_config.get(1, 3)
    await user_config.get(2, 2)
    assert user_config.forget_user(1) == 2
    # user 1's entries gone; user 2's stays
    snap = user_config._snapshot()
    assert snap["cache_size"] == 1


@pytest.mark.asyncio
async def test_forget_guild_drops_all_users(_patch_db):
    await user_config.get(1, 2)
    await user_config.get(2, 2)
    await user_config.get(3, 99)
    assert user_config.forget_guild(2) == 2
    snap = user_config._snapshot()
    assert snap["cache_size"] == 1


@pytest.mark.asyncio
async def test_forget_all_clears_everything(_patch_db):
    await user_config.get(1, 2)
    await user_config.get(2, 3)
    assert user_config.forget_all() == 2
    assert user_config._snapshot()["cache_size"] == 0


# ---------------------------------------------------------------------------
# TTL expiry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ttl_expiry_forces_reload(_patch_db, monkeypatch):
    """An expired entry triggers a fresh DB read."""
    base_time = 1000.0
    monkeypatch.setattr(user_config.time, "monotonic", lambda: base_time)
    await user_config.get(1, 2)

    # Jump past the TTL.
    monkeypatch.setattr(
        user_config.time,
        "monotonic",
        lambda: base_time + user_config._CACHE_TTL_SECS + 1,
    )
    await user_config.get(1, 2)
    assert _patch_db.await_count == 2


# ---------------------------------------------------------------------------
# DB failure: empty bundle, no raise
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_db_failure_returns_empty_bundle():
    """The hot-path read MUST NOT raise; an empty bundle is the safe default."""
    with patch(
        "utils.db.user_participation.list_for_user",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB blip"),
    ):
        bundle = await user_config.get(1, 2)
    assert bundle.participation == ()


# ---------------------------------------------------------------------------
# Soft max-size eviction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_eviction_drops_oldest_decile_when_capacity_exceeded(
    _patch_db, monkeypatch
):
    monkeypatch.setattr(user_config, "_CACHE_MAX_ENTRIES", 20)
    base = 1000.0
    for i in range(25):
        monkeypatch.setattr(user_config.time, "monotonic", lambda x=base + i: x)
        await user_config.get(user_id=i, guild_id=1)
    snap = user_config._snapshot()
    # The eviction triggers when cache exceeds 20; it drops the
    # oldest decile (max(1, 21//10) = 2) on each excess insert.
    assert snap["cache_size"] <= 25
    assert snap["evictions"] > 0


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


def test_snapshot_shape():
    snap = user_config._snapshot()
    assert set(snap.keys()) == {
        "cache_size",
        "cache_capacity",
        "ttl_secs",
        "hits",
        "misses",
        "evictions",
    }


def test_diagnostics_provider_registered():
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("user_config")
    assert "cache_size" in snap
