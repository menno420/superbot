"""Stage-2 walk bug #1 — the AI typed-policy projection retries, then surfaces.

The projection is a separate write from the (already committed) legacy-KV
settings write, so a transient failure would become durable silent drift (the
audit says "changed" but the runtime resolver's typed row keeps the old value).
``project_from_legacy_settings`` now retries transient failures and returns
``None`` only after exhausting them — the settings pipeline surfaces that
``None`` as ``projection_committed=False`` instead of swallowing it.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services import ai_policy_mutation

# ruff: noqa: S101

_SCALARS = {
    "ai_enabled": True,
    "ai_natural_language_enabled": True,
    "ai_default_provider": "openai",
    "ai_default_model": "gpt-4o-mini",
    "ai_minimum_level_default": 3,
    "ai_cooldown_seconds": 15,
    "ai_fresh_user_mention_allowance": 2,
}


def _resolve(values):
    async def _r(_guild_id, _subsystem, name):
        if name not in values:
            return None
        return SimpleNamespace(value=values[name])

    return _r


def _ok_result(guild_id):
    return ai_policy_mutation.AIPolicyMutationResult(
        mutation_id="mid",
        table="ai_guild_policy",
        guild_id=guild_id,
        target_id=None,
        generation=7,
        event_emitted=True,
    )


def _common_patches(monkeypatch):
    from services import settings_resolution
    from utils.db import ai as ai_db

    monkeypatch.setattr(settings_resolution, "resolve_setting", _resolve(_SCALARS))
    monkeypatch.setattr(
        ai_db, "get_guild_policy",
        AsyncMock(return_value={"guild_instruction_profile_id": 88}),
    )
    # make the retry backoff instant
    monkeypatch.setattr(ai_policy_mutation.asyncio, "sleep", AsyncMock())


@pytest.mark.asyncio
async def test_projection_retries_transient_failure(monkeypatch):
    _common_patches(monkeypatch)
    calls = {"n": 0}

    async def _flaky(guild_id, **_kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient DB blip")
        return _ok_result(guild_id)

    monkeypatch.setattr(ai_policy_mutation, "set_guild_policy", _flaky)

    result = await ai_policy_mutation.project_from_legacy_settings(
        42, SimpleNamespace(id=7), mutation_id="mid",
    )
    assert result is not None  # self-healed on the retry
    assert calls["n"] == 2  # first raised, second succeeded


@pytest.mark.asyncio
async def test_projection_returns_none_after_exhausting_retries(monkeypatch):
    _common_patches(monkeypatch)
    log_spy = AsyncMock()
    monkeypatch.setattr(ai_policy_mutation, "_log_projection_failure", log_spy)
    monkeypatch.setattr(
        ai_policy_mutation, "set_guild_policy",
        AsyncMock(side_effect=RuntimeError("persistent failure")),
    )

    result = await ai_policy_mutation.project_from_legacy_settings(
        42, SimpleNamespace(id=7), mutation_id="mid",
    )
    assert result is None  # surfaced, not silently swallowed
    log_spy.assert_awaited_once()
