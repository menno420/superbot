"""PR4B — resolve(dry_run=True) populates precedence_trace, no side effects."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import PolicyDenialReason  # noqa: E402
from services import ai_natural_language_policy as nlp  # noqa: E402
from utils.db import ai as ai_db  # noqa: E402


def _ctx(
    *,
    guild_id: int = 1,
    channel_id: int = 100,
    category_id: int | None = 200,
    user_level: int = 5,
    user_role_ids: tuple[int, ...] = (),
    is_mention: bool = False,
    is_fresh_user: bool = False,
) -> nlp.MessageContext:
    return nlp.MessageContext(
        guild_id=guild_id,
        channel_id=channel_id,
        category_id=category_id,
        user_id=99,
        user_level=user_level,
        user_role_ids=user_role_ids,
        is_mention=is_mention,
        is_fresh_user=is_fresh_user,
    )


def _enabled_policy(**overrides) -> dict:
    base = {
        "guild_id": 1,
        "enabled": True,
        "natural_language_enabled": True,
        "default_provider": "openai",
        "default_model": "gpt-4o-mini",
        "minimum_level_default": 2,
        "cooldown_seconds": 30,
        "fresh_user_mention_allowance": 0,
        "guild_instruction_profile_id": None,
        "generation": 1,
    }
    base.update(overrides)
    return base


@pytest.fixture(autouse=True)
def _reset_cache():
    nlp._reset_for_tests()
    yield
    nlp._reset_for_tests()


async def _stub_bundle(monkeypatch, *, policy, channel=None, category=None, role=None):
    async def _get_policy(gid):
        return policy

    async def _list_ch(gid):
        return channel or []

    async def _list_cat(gid):
        return category or []

    async def _list_role(gid):
        return role or []

    monkeypatch.setattr(ai_db, "get_guild_policy", _get_policy)
    monkeypatch.setattr(ai_db, "list_channel_policies", _list_ch)
    monkeypatch.setattr(ai_db, "list_category_policies", _list_cat)
    monkeypatch.setattr(ai_db, "list_role_policies", _list_role)


# ---------------------------------------------------------------------------
# Backwards-compat: live calls leave precedence_trace empty.
# ---------------------------------------------------------------------------


async def test_live_resolve_has_empty_trace(monkeypatch):
    await _stub_bundle(monkeypatch, policy=_enabled_policy())
    decision = await nlp.resolve(_ctx())
    assert decision.allowed is True
    assert decision.precedence_trace == ()


# ---------------------------------------------------------------------------
# dry_run=True populates the trace on every code path.
# ---------------------------------------------------------------------------


async def test_dry_run_allowed_path_traces_each_level(monkeypatch):
    await _stub_bundle(monkeypatch, policy=_enabled_policy())
    decision = await nlp.resolve(_ctx(), dry_run=True)
    assert decision.allowed is True
    trace = decision.precedence_trace
    assert any("guild: baseline" in step for step in trace)
    # Category 200 isn't configured → "no override (inherit)" line.
    assert any("category 200: no override" in step for step in trace)
    # Channel 100 isn't configured → "no override (inherit)" line.
    assert any("channel 100: no override" in step for step in trace)
    # Final "allowed" line.
    assert any(step.startswith("user:") for step in trace)
    assert trace[-1].startswith("final: allowed")


async def test_dry_run_guild_not_configured_traces_root_cause(monkeypatch):
    await _stub_bundle(monkeypatch, policy=None)
    decision = await nlp.resolve(_ctx(), dry_run=True)
    assert decision.allowed is False
    assert decision.reason_code == PolicyDenialReason.GUILD_NOT_CONFIGURED
    assert any("GUILD_NOT_CONFIGURED" in step for step in decision.precedence_trace)


async def test_dry_run_globally_disabled_traces_step(monkeypatch):
    await _stub_bundle(
        monkeypatch,
        policy=_enabled_policy(enabled=False),
    )
    decision = await nlp.resolve(_ctx(), dry_run=True)
    assert decision.allowed is False
    assert decision.reason_code == PolicyDenialReason.AI_GLOBALLY_DISABLED
    assert any("AI_GLOBALLY_DISABLED" in step for step in decision.precedence_trace)


async def test_dry_run_channel_disabled_traces_channel_id(monkeypatch):
    channel = [{
        "channel_id": 100,
        "mode": "disabled",
        "min_level": None,
        "cooldown_seconds": None,
        "instruction_profile_id": None,
    }]
    await _stub_bundle(monkeypatch, policy=_enabled_policy(), channel=channel)
    decision = await nlp.resolve(_ctx(), dry_run=True)
    assert decision.allowed is False
    assert decision.reason_code == PolicyDenialReason.CHANNEL_DISABLED
    assert any(
        "channel 100" in step and "CHANNEL_DISABLED" in step
        for step in decision.precedence_trace
    )


async def test_dry_run_mention_only_without_mention_traces(monkeypatch):
    channel = [{
        "channel_id": 100,
        "mode": "mention_only",
        "min_level": None,
        "cooldown_seconds": None,
        "instruction_profile_id": None,
    }]
    await _stub_bundle(monkeypatch, policy=_enabled_policy(), channel=channel)
    decision = await nlp.resolve(_ctx(is_mention=False), dry_run=True)
    assert decision.reason_code == PolicyDenialReason.NO_MENTION_REQUIRED
    assert any(
        "mention_only" in step and "NO_MENTION_REQUIRED" in step
        for step in decision.precedence_trace
    )


async def test_dry_run_role_deny_traces_step(monkeypatch):
    role = [{
        "role_id": 42,
        "decision": "deny",
        "min_level_override": None,
        "bypass_cooldown": False,
    }]
    await _stub_bundle(monkeypatch, policy=_enabled_policy(), role=role)
    decision = await nlp.resolve(
        _ctx(user_role_ids=(42,)),
        dry_run=True,
    )
    assert decision.reason_code == PolicyDenialReason.ROLE_DENIED
    assert any("ROLE_DENIED" in step for step in decision.precedence_trace)


async def test_dry_run_role_min_level_override_appears_in_trace(monkeypatch):
    """A permissive role override should lower min_level and the trace
    must explain that."""
    role = [{
        "role_id": 42,
        "decision": "allow",
        "min_level_override": 0,
        "bypass_cooldown": True,
    }]
    await _stub_bundle(
        monkeypatch,
        policy=_enabled_policy(minimum_level_default=10),
        role=role,
    )
    decision = await nlp.resolve(
        _ctx(user_level=1, user_role_ids=(42,)),
        dry_run=True,
    )
    assert decision.allowed is True
    trace = decision.precedence_trace
    assert any("role" in step and "min_level=0" in step for step in trace)
    assert any("bypass_cooldown=true" in step for step in trace)
    assert decision.effective_cooldown == 0


async def test_dry_run_below_min_level_traces_user_step(monkeypatch):
    await _stub_bundle(
        monkeypatch,
        policy=_enabled_policy(minimum_level_default=5),
    )
    decision = await nlp.resolve(_ctx(user_level=1), dry_run=True)
    assert decision.reason_code == PolicyDenialReason.BELOW_MIN_LEVEL
    assert any(
        "level=1 < min=5" in step and "BELOW_MIN_LEVEL" in step
        for step in decision.precedence_trace
    )


async def test_dry_run_fresh_user_mention_allowance_traces_pardon(monkeypatch):
    await _stub_bundle(
        monkeypatch,
        policy=_enabled_policy(minimum_level_default=5, fresh_user_mention_allowance=1),
    )
    decision = await nlp.resolve(
        _ctx(user_level=0, is_mention=True, is_fresh_user=True),
        dry_run=True,
    )
    assert decision.allowed is True
    assert any(
        "fresh-user mention allowance" in step
        for step in decision.precedence_trace
    )


# ---------------------------------------------------------------------------
# dry_run does not destabilise the cache or production decisions.
# ---------------------------------------------------------------------------


async def test_dry_run_does_not_disturb_cache_between_live_calls(monkeypatch):
    await _stub_bundle(monkeypatch, policy=_enabled_policy())
    # First, a live call to warm the cache.
    live_1 = await nlp.resolve(_ctx())
    assert live_1.allowed is True
    cached_after_live = nlp._CACHE.get(1)
    assert cached_after_live is not None
    # Then several dry-run calls — the cache must remain identical.
    for is_mention in (False, True, False):
        dry = await nlp.resolve(_ctx(is_mention=is_mention), dry_run=True)
        assert dry.allowed is True
    assert nlp._CACHE.get(1) is cached_after_live
    # And the next live call is byte-for-byte the same decision.
    live_2 = await nlp.resolve(_ctx())
    assert live_2.policy_snapshot_hash == live_1.policy_snapshot_hash
    assert live_2.precedence_trace == ()


async def test_dry_run_and_live_decisions_match_for_same_context(monkeypatch):
    """The toggle must not change the decision — only the bookkeeping."""
    channel = [{
        "channel_id": 100,
        "mode": "mention_only",
        "min_level": 3,
        "cooldown_seconds": 10,
        "instruction_profile_id": None,
    }]
    await _stub_bundle(monkeypatch, policy=_enabled_policy(), channel=channel)

    ctx = _ctx(user_level=3, is_mention=True)
    live = await nlp.resolve(ctx)
    dry = await nlp.resolve(ctx, dry_run=True)
    assert live.allowed == dry.allowed
    assert live.reason_code == dry.reason_code
    assert live.effective_min_level == dry.effective_min_level
    assert live.effective_cooldown == dry.effective_cooldown
    # The live decision still has no trace; the dry one has many.
    assert live.precedence_trace == ()
    assert len(dry.precedence_trace) >= 3
