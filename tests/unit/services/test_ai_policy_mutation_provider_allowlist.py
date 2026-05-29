"""AI provider unblock — set_guild_policy must accept 'anthropic'.

The runtime already supports Anthropic (routing has per-task claude
defaults; the gateway registers AnthropicProvider). The policy/settings
layer was the only thing blocking it: the mutation chokepoint rejected
any provider other than deterministic/openai, so a guild could never be
switched to Claude. These tests pin that anthropic is now a first-class
provider and that genuinely-unknown providers are still rejected.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services import ai_policy_mutation
from services.ai_policy_mutation import InvalidAIPolicyValueError
from utils.db import ai as ai_db


def _admin_actor(actor_id: int = 555):
    return SimpleNamespace(
        id=actor_id,
        guild_permissions=SimpleNamespace(administrator=True),
    )


def _patch_db(monkeypatch):
    monkeypatch.setattr(ai_db, "upsert_guild_policy", AsyncMock(return_value=1))
    monkeypatch.setattr(ai_db, "bump_generation", AsyncMock(return_value=1))
    monkeypatch.setattr(ai_policy_mutation, "_emit", AsyncMock(return_value=True))
    monkeypatch.setattr(
        "services.ai_natural_language_policy.invalidate", lambda _gid: None,
    )


async def _set(monkeypatch, provider: str, model: str = ""):
    _patch_db(monkeypatch)
    return await ai_policy_mutation.set_guild_policy(
        guild_id=11,
        enabled=True,
        natural_language_enabled=True,
        default_provider=provider,
        default_model=model,
        minimum_level_default=2,
        cooldown_seconds=30,
        fresh_user_mention_allowance=1,
        guild_instruction_profile_id=None,
        actor=_admin_actor(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["deterministic", "openai", "anthropic"])
async def test_set_guild_policy_accepts_supported_providers(monkeypatch, provider):
    result = await _set(monkeypatch, provider)
    assert result.table == "ai_guild_policy"
    # The provider value was forwarded to the DB write unchanged.
    ai_db.upsert_guild_policy.assert_awaited_once()
    assert ai_db.upsert_guild_policy.await_args.kwargs["default_provider"] == provider


@pytest.mark.asyncio
async def test_set_guild_policy_rejects_unknown_provider(monkeypatch):
    _patch_db(monkeypatch)
    with pytest.raises(InvalidAIPolicyValueError, match="anthropic"):
        await _set(monkeypatch, "gemini")


@pytest.mark.asyncio
async def test_set_guild_policy_anthropic_with_empty_model_is_allowed(monkeypatch):
    """The recommended path — provider=anthropic, model empty (the gateway
    auto-picks the per-task claude model) — must be accepted.
    """
    result = await _set(monkeypatch, "anthropic", model="")
    assert result.table == "ai_guild_policy"
    assert ai_db.upsert_guild_policy.await_args.kwargs["default_model"] == ""
