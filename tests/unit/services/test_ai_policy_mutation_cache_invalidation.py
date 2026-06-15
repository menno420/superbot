"""Regression: every typed AI policy mutation invalidates the resolver cache.

The resolver caches the per-guild bundle keyed by ``ai_guild_policy.generation``
(see :mod:`services.ai_natural_language_policy`). The mutation helpers must
both bump the generation AND call ``ai_natural_language_policy.invalidate``
so the next ``resolve`` sees the new state without waiting for a
generation-driven read.

These tests pin the invalidate call directly so refactors of the mutation
helpers can't silently regress the cache safety net.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services import ai_policy_mutation
from utils.db import ai as ai_db


def _admin_actor(actor_id: int = 555):
    return SimpleNamespace(
        id=actor_id,
        guild_permissions=SimpleNamespace(administrator=True),
    )


def _patch_db(monkeypatch):
    async def _noop_async(*_a, **_kw):
        return None

    async def _bump(_gid):
        return 42

    monkeypatch.setattr(ai_db, "upsert_guild_policy", AsyncMock(return_value=42))
    monkeypatch.setattr(ai_db, "upsert_channel_policy", _noop_async)
    monkeypatch.setattr(ai_db, "upsert_category_policy", _noop_async)
    monkeypatch.setattr(ai_db, "upsert_role_policy", _noop_async)
    monkeypatch.setattr(ai_db, "bump_generation", _bump)
    monkeypatch.setattr(
        ai_policy_mutation,
        "_emit",
        AsyncMock(return_value=True),
    )


@pytest.fixture
def _capture_invalidate(monkeypatch):
    seen: list[int] = []

    def _record(guild_id: int) -> None:
        seen.append(guild_id)

    monkeypatch.setattr(
        "services.ai_natural_language_policy.invalidate",
        _record,
    )
    return seen


@pytest.mark.asyncio
async def test_set_guild_policy_invalidates_resolver_cache(
    monkeypatch,
    _capture_invalidate,
):
    _patch_db(monkeypatch)
    await ai_policy_mutation.set_guild_policy(
        guild_id=11,
        enabled=True,
        natural_language_enabled=True,
        default_provider="deterministic",
        default_model="",
        minimum_level_default=2,
        cooldown_seconds=30,
        fresh_user_mention_allowance=1,
        guild_instruction_profile_id=None,
        actor=_admin_actor(),
    )
    assert _capture_invalidate == [11]


@pytest.mark.asyncio
async def test_set_channel_policy_invalidates_resolver_cache(
    monkeypatch,
    _capture_invalidate,
):
    _patch_db(monkeypatch)
    await ai_policy_mutation.set_channel_policy(
        guild_id=22,
        channel_id=200,
        mode="always_reply",
        actor=_admin_actor(),
    )
    assert _capture_invalidate == [22]


@pytest.mark.asyncio
async def test_set_category_policy_invalidates_resolver_cache(
    monkeypatch,
    _capture_invalidate,
):
    _patch_db(monkeypatch)
    await ai_policy_mutation.set_category_policy(
        guild_id=33,
        category_id=300,
        mode="mention_only",
        actor=_admin_actor(),
    )
    assert _capture_invalidate == [33]


@pytest.mark.asyncio
async def test_set_role_policy_invalidates_resolver_cache(
    monkeypatch,
    _capture_invalidate,
):
    _patch_db(monkeypatch)
    await ai_policy_mutation.set_role_policy(
        guild_id=44,
        role_id=400,
        decision="allow",
        actor=_admin_actor(),
    )
    assert _capture_invalidate == [44]
