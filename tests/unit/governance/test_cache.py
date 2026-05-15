"""Tests for the governance cache layer.

Covers:
- _cache_key composition (with and without role override flag)
- _cache_get / _cache_set (hit, miss, TTL expiry)
- invalidate_guild_cache (version bump makes old keys unreachable)
- Role override flag: when _guild_has_role_overrides is set, role_ids enter the key
- Cache bypass after invalidation: next resolve_visibility re-queries DB
"""

from __future__ import annotations

import time

import pytest
import services.governance_service as gs
from services.governance_service import (
    _cache_get,
    _cache_key,
    _cache_set,
    invalidate_guild_cache,
    resolve_visibility,
)

from .conftest import make_ctx, make_visibility_row

# ---------------------------------------------------------------------------
# Pure unit tests — key construction
# ---------------------------------------------------------------------------


def test_cache_key_without_role_overrides():
    gs._guild_has_role_overrides[1] = False
    k1 = _cache_key(1, 10, "user", frozenset({100, 200}))
    k2 = _cache_key(1, 10, "user", frozenset({999}))
    # role_ids must NOT appear when no role overrides are configured
    assert k1 == k2


def test_cache_key_with_role_overrides_includes_roles():
    gs._guild_has_role_overrides[1] = True
    k1 = _cache_key(1, 10, "user", frozenset({100, 200}))
    k2 = _cache_key(1, 10, "user", frozenset({999}))
    # role_ids MUST differ the keys when role overrides are configured
    assert k1 != k2


def test_cache_key_different_tiers_differ():
    k_user = _cache_key(1, 10, "user")
    k_mod = _cache_key(1, 10, "moderator")
    assert k_user != k_mod


def test_cache_key_different_channels_differ():
    k1 = _cache_key(1, 10, "user")
    k2 = _cache_key(1, 20, "user")
    assert k1 != k2


def test_cache_key_different_guilds_differ():
    k1 = _cache_key(1, 10, "user")
    k2 = _cache_key(2, 10, "user")
    assert k1 != k2


def test_cache_key_changes_after_invalidation():
    k_before = _cache_key(1, 10, "user")
    invalidate_guild_cache(1)
    k_after = _cache_key(1, 10, "user")
    assert k_before != k_after


# ---------------------------------------------------------------------------
# Cache get/set/expiry
# ---------------------------------------------------------------------------


def test_cache_miss_returns_none():
    assert _cache_get(("non", "existent", "key")) is None


def test_cache_set_then_get_returns_value():
    k = ("test", "key")
    _cache_set(k, {"data": 42})
    result = _cache_get(k)
    assert result == {"data": 42}


def test_cache_entry_expires_after_ttl(monkeypatch):
    """An entry beyond _CACHE_TTL age returns None."""
    k = ("expiry", "test")
    _cache_set(k, "stale")
    # Advance the stored timestamp so it looks old.
    ts, val = gs._CACHE[k]
    gs._CACHE[k] = (ts - gs._CACHE_TTL - 1, val)
    assert _cache_get(k) is None


def test_cache_hit_does_not_expire_fresh_entry():
    k = ("fresh", "entry")
    _cache_set(k, "fresh_value")
    assert _cache_get(k) == "fresh_value"


# ---------------------------------------------------------------------------
# invalidate_guild_cache
# ---------------------------------------------------------------------------


def test_invalidate_increments_version():
    assert gs._CACHE_VERSION.get(5, 0) == 0
    invalidate_guild_cache(5)
    assert gs._CACHE_VERSION[5] == 1
    invalidate_guild_cache(5)
    assert gs._CACHE_VERSION[5] == 2


def test_invalidate_does_not_affect_other_guilds():
    invalidate_guild_cache(1)
    assert gs._CACHE_VERSION.get(2, 0) == 0


# ---------------------------------------------------------------------------
# Integration: cache prevents extra DB calls
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_second_call_uses_cache(mock_db):
    ctx = make_ctx(guild_id=50, channel_id=51, category_id=52)
    await resolve_visibility(ctx)
    first_count = mock_db.fetch.call_count

    # Identical context → cache hit
    await resolve_visibility(ctx)
    assert mock_db.fetch.call_count == first_count


@pytest.mark.asyncio
async def test_invalidation_forces_db_re_query(mock_db):
    ctx = make_ctx(guild_id=50, channel_id=51, category_id=52)
    await resolve_visibility(ctx)
    first_count = mock_db.fetch.call_count

    invalidate_guild_cache(ctx.guild_id)

    await resolve_visibility(ctx)
    assert mock_db.fetch.call_count > first_count


@pytest.mark.asyncio
async def test_role_override_flag_differentiates_cached_results(mock_db):
    """Two members with different roles must NOT share a cache entry when
    role overrides exist — regression test for ISSUE-001."""
    guild_id = 77
    gs._guild_has_role_overrides[guild_id] = True

    ctx_a = make_ctx(guild_id=guild_id, channel_id=100)
    ctx_b = make_ctx(guild_id=guild_id, channel_id=100)
    # Simulate different role_ids
    ctx_a.role_ids = {10}
    ctx_b.role_ids = {20}

    # Resolve both — they must each call fetch (not share a cache entry)
    await resolve_visibility(ctx_a)
    count_after_a = mock_db.fetch.call_count
    await resolve_visibility(ctx_b)
    count_after_b = mock_db.fetch.call_count

    assert count_after_b > count_after_a
