"""Phase 2d PR-2 — is_enabled evaluator + cache + bootstrap policy.

Covers:

* Bootstrap policy: emergency env override beats everything; the
  ``feature_flag.primary`` meta-gate bypasses DB on its own evaluation
  and forces declared-default for other flags when OFF.
* DB-backed resolution order: per-guild override → global override →
  rollout policy → declared default.
* Deterministic rollout hash: same ``(flag, guild)`` → same bucket.
* Cache behaviour: TTL eviction, manual clear, per-guild clear.
* DB-unreachable fallback: returns declared default + emits bootstrap
  metric, never raises.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

from core.runtime import feature_flags
from core.runtime.feature_flags import (
    BINDINGS_PRIMARY,
    FEATURE_FLAG_PRIMARY,
    EnvironmentTier,
    FeatureFlag,
    RolloutPolicy,
    _register_builtins,
)


@pytest.fixture(autouse=True)
def _reset_module_state():
    """Each test starts with a clean registry, cache, and metric counter."""
    feature_flags._reset_for_tests()
    _register_builtins()
    # Ensure no test runs under a leaked env override.
    for key in list(os.environ):
        if key.startswith("SUPERBOT_FF_"):
            del os.environ[key]
    yield
    feature_flags._reset_for_tests()
    for key in list(os.environ):
        if key.startswith("SUPERBOT_FF_"):
            del os.environ[key]


# ---------------------------------------------------------------------------
# Bootstrap policy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_env_override_wins_for_arbitrary_flag(monkeypatch):
    """SUPERBOT_FF_<FLAG>=on/off always wins, regardless of DB state."""
    monkeypatch.setenv("SUPERBOT_FF_BINDINGS_PRIMARY", "on")
    decision = await feature_flags.resolve_with_provenance(
        "bindings.primary",
        guild_id=42,
    )
    assert decision.value is True
    assert decision.source == "env"


@pytest.mark.asyncio
async def test_env_override_recognized_boolean_literals(monkeypatch):
    for raw in ("true", "yes", "ON", "1"):
        monkeypatch.setenv("SUPERBOT_FF_BINDINGS_PRIMARY", raw)
        assert await feature_flags.is_enabled("bindings.primary", 42) is True
    for raw in ("false", "no", "off", "0"):
        monkeypatch.setenv("SUPERBOT_FF_BINDINGS_PRIMARY", raw)
        feature_flags.clear_cache()
        assert await feature_flags.is_enabled("bindings.primary", 42) is False


@pytest.mark.asyncio
async def test_unknown_env_value_is_ignored(monkeypatch):
    """An unrecognized env value falls through to the bootstrap path."""
    monkeypatch.setenv("SUPERBOT_FF_BINDINGS_PRIMARY", "maybe?")
    # feature_flag.primary defaults OFF → declared default returned.
    decision = await feature_flags.resolve_with_provenance(
        "bindings.primary",
        guild_id=42,
    )
    assert decision.source == "default"
    assert decision.value == BINDINGS_PRIMARY.default_value


@pytest.mark.asyncio
async def test_feature_flag_primary_off_returns_declared_default():
    """With feature_flag.primary OFF (declared default), DB is bypassed."""
    decision = await feature_flags.resolve_with_provenance(
        "bindings.primary",
        guild_id=42,
    )
    assert decision.source == "default"
    assert decision.value == BINDINGS_PRIMARY.default_value


@pytest.mark.asyncio
async def test_feature_flag_primary_resolves_via_env_only(monkeypatch):
    """The meta-flag's value never comes from the DB."""
    monkeypatch.setenv("SUPERBOT_FF_FEATURE_FLAG_PRIMARY", "on")
    decision = await feature_flags.resolve_with_provenance(
        FEATURE_FLAG_PRIMARY.name,
        guild_id=42,
    )
    assert decision.value is True
    assert decision.source == "env"


@pytest.mark.asyncio
async def test_undeclared_flag_returns_false_with_default_source():
    decision = await feature_flags.resolve_with_provenance(
        "does.not.exist",
        guild_id=42,
    )
    assert decision.value is False
    assert decision.source == "default"


# ---------------------------------------------------------------------------
# DB-backed resolution order
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_per_guild_override_beats_global(monkeypatch):
    """When feature_flag.primary is ON, per-guild row beats the global row."""
    monkeypatch.setenv("SUPERBOT_FF_FEATURE_FLAG_PRIMARY", "on")

    with (
        patch(
            "utils.db.feature_flag_state.get_guild_override",
            new_callable=AsyncMock,
            return_value={"state": "on"},
        ),
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value={"state": "off", "rollout_percent": None},
        ),
        patch(
            "utils.db.environment_tiers.get_tier",
            new_callable=AsyncMock,
            return_value="production",
        ),
    ):
        decision = await feature_flags.resolve_with_provenance(
            "bindings.primary",
            guild_id=42,
        )
    assert decision.value is True
    assert decision.source == "db_guild"


@pytest.mark.asyncio
async def test_global_override_used_when_no_guild_row(monkeypatch):
    monkeypatch.setenv("SUPERBOT_FF_FEATURE_FLAG_PRIMARY", "on")

    with (
        patch(
            "utils.db.feature_flag_state.get_guild_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value={"state": "on", "rollout_percent": None},
        ),
        patch(
            "utils.db.environment_tiers.get_tier",
            new_callable=AsyncMock,
            return_value="production",
        ),
    ):
        decision = await feature_flags.resolve_with_provenance(
            "bindings.primary",
            guild_id=42,
        )
    assert decision.value is True
    assert decision.source == "db_global"


@pytest.mark.asyncio
async def test_global_override_off_is_hard_disable(monkeypatch):
    """state='off' on the global row hard-disables the flag for every guild.

    This is the rollback contract: flipping the global row to 'off'
    must immediately turn the flag off without falling through to the
    rollout policy.  Without this guarantee, an in-flight canary
    rollout could keep granting access after rollback.
    """
    monkeypatch.setenv("SUPERBOT_FF_FEATURE_FLAG_PRIMARY", "on")

    rollout_flag = FeatureFlag(
        name="test.rollout_active",
        description="flag with rollout policy that would grant access",
        default_value=False,
        rollout_policy=RolloutPolicy(
            staged_guilds=(42,),
            percentage_rollout=100,
            tier_gate=EnvironmentTier.PRODUCTION,
        ),
    )
    feature_flags.register(rollout_flag)

    with (
        patch(
            "utils.db.feature_flag_state.get_guild_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value={"state": "off", "rollout_percent": None},
        ),
        patch(
            "utils.db.environment_tiers.get_tier",
            new_callable=AsyncMock,
            return_value="production",
        ),
    ):
        decision = await feature_flags.resolve_with_provenance(
            "test.rollout_active",
            guild_id=42,
        )
    # Global 'off' must win even when staged_guilds + 100% rollout
    # would otherwise grant access.
    assert decision.value is False
    assert decision.source == "db_global"


@pytest.mark.asyncio
async def test_global_tier_state_falls_through_to_rollout_when_unmatched(monkeypatch):
    """A tier-named global state that doesn't match the guild's tier falls through.

    Example: global state='canary', guild tier='production'.  The
    global row is non-binding for this guild — the declared rollout
    policy may still grant access via staged_guilds.
    """
    monkeypatch.setenv("SUPERBOT_FF_FEATURE_FLAG_PRIMARY", "on")

    staged_flag = FeatureFlag(
        name="test.tier_fallthrough",
        description="tier-named global state, staged_guilds rollout",
        default_value=False,
        rollout_policy=RolloutPolicy(
            staged_guilds=(42,),
            percentage_rollout=0,
            tier_gate=EnvironmentTier.PRODUCTION,
        ),
    )
    feature_flags.register(staged_flag)

    with (
        patch(
            "utils.db.feature_flag_state.get_guild_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value={"state": "canary", "rollout_percent": None},
        ),
        patch(
            "utils.db.environment_tiers.get_tier",
            new_callable=AsyncMock,
            return_value="production",
        ),
    ):
        decision = await feature_flags.resolve_with_provenance(
            "test.tier_fallthrough",
            guild_id=42,
        )
    # Guild is 'production' < 'canary'; the global row does not bind.
    # The rollout policy still grants because guild 42 is staged.
    assert decision.value is True
    assert decision.source == "tier"


@pytest.mark.asyncio
async def test_rollout_policy_grants_via_tier_for_staged_guild(monkeypatch):
    """An explicit staged_guild + matching tier returns True via tier."""
    monkeypatch.setenv("SUPERBOT_FF_FEATURE_FLAG_PRIMARY", "on")

    staged_flag = FeatureFlag(
        name="test.staged",
        description="staged guild check",
        default_value=False,
        rollout_policy=RolloutPolicy(
            staged_guilds=(42,),
            percentage_rollout=0,
            tier_gate=EnvironmentTier.CANARY,
        ),
    )
    feature_flags.register(staged_flag)

    with (
        patch(
            "utils.db.feature_flag_state.get_guild_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.environment_tiers.get_tier",
            new_callable=AsyncMock,
            return_value="canary",
        ),
    ):
        decision = await feature_flags.resolve_with_provenance(
            "test.staged",
            guild_id=42,
        )
    assert decision.value is True
    assert decision.source == "tier"


@pytest.mark.asyncio
async def test_falls_back_to_declared_default(monkeypatch):
    monkeypatch.setenv("SUPERBOT_FF_FEATURE_FLAG_PRIMARY", "on")

    with (
        patch(
            "utils.db.feature_flag_state.get_guild_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.environment_tiers.get_tier",
            new_callable=AsyncMock,
            return_value="production",
        ),
    ):
        decision = await feature_flags.resolve_with_provenance(
            "bindings.primary",
            guild_id=42,
        )
    assert decision.value == BINDINGS_PRIMARY.default_value
    assert decision.source == "default"


# ---------------------------------------------------------------------------
# Deterministic rollout hash
# ---------------------------------------------------------------------------


def test_rollout_bucket_deterministic():
    """Same (flag, guild) always produces the same bucket."""
    bucket_a = feature_flags._rollout_bucket("bindings.primary", 12345)
    bucket_b = feature_flags._rollout_bucket("bindings.primary", 12345)
    assert bucket_a == bucket_b
    assert 0 <= bucket_a < 100


def test_rollout_bucket_varies_per_flag_and_guild():
    """Different flags / guilds usually land in different buckets."""
    base = feature_flags._rollout_bucket("bindings.primary", 1)
    other_guild = feature_flags._rollout_bucket("bindings.primary", 2)
    other_flag = feature_flags._rollout_bucket("participation.enabled", 1)
    # Not asserting strict inequality (collisions exist) but at least
    # one of these should differ from base in any reasonable sample.
    assert (other_guild != base) or (other_flag != base)


@pytest.mark.asyncio
async def test_rollout_percentage_includes_some_guilds(monkeypatch):
    """At 50% rollout, roughly half a wide range of guilds is enabled."""
    monkeypatch.setenv("SUPERBOT_FF_FEATURE_FLAG_PRIMARY", "on")

    flag = FeatureFlag(
        name="test.rollout",
        description="50% rollout",
        default_value=False,
        rollout_policy=RolloutPolicy(
            staged_guilds=(),
            percentage_rollout=50,
            tier_gate=EnvironmentTier.PRODUCTION,
        ),
    )
    feature_flags.register(flag)

    enabled = 0
    with (
        patch(
            "utils.db.feature_flag_state.get_guild_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.environment_tiers.get_tier",
            new_callable=AsyncMock,
            return_value="production",
        ),
    ):
        for guild_id in range(1, 201):
            feature_flags.clear_cache()
            if await feature_flags.is_enabled("test.rollout", guild_id):
                enabled += 1
    # sha256 with 200 samples should land somewhere in 30..70% of true
    # enablement at 50% rollout.  Wide tolerance keeps the test
    # deterministic across runs without being trivially loose.
    assert (
        60 <= enabled <= 140
    ), f"expected ~100/200 enabled at 50% rollout, got {enabled}"


# ---------------------------------------------------------------------------
# Cache behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_avoids_second_db_call(monkeypatch):
    monkeypatch.setenv("SUPERBOT_FF_FEATURE_FLAG_PRIMARY", "on")

    with (
        patch(
            "utils.db.feature_flag_state.get_guild_override",
            new_callable=AsyncMock,
            return_value={"state": "on"},
        ) as mock_guild,
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.environment_tiers.get_tier",
            new_callable=AsyncMock,
            return_value="production",
        ),
    ):
        await feature_flags.is_enabled("bindings.primary", 42)
        await feature_flags.is_enabled("bindings.primary", 42)
    assert mock_guild.await_count == 1


@pytest.mark.asyncio
async def test_clear_cache_evicts_specific_guild(monkeypatch):
    monkeypatch.setenv("SUPERBOT_FF_FEATURE_FLAG_PRIMARY", "on")

    with (
        patch(
            "utils.db.feature_flag_state.get_guild_override",
            new_callable=AsyncMock,
            return_value={"state": "on"},
        ),
        patch(
            "utils.db.feature_flag_state.get_global_override",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "utils.db.environment_tiers.get_tier",
            new_callable=AsyncMock,
            return_value="production",
        ),
    ):
        await feature_flags.is_enabled("bindings.primary", 42)
        await feature_flags.is_enabled("bindings.primary", 99)
        # 3 entries in cache: (bindings.primary, 42), (bindings.primary, 99),
        # plus any recursive (feature_flag.primary) lookups would normally
        # be cached too — but feature_flag.primary bypasses cache because
        # it's the meta-flag.  We assert specifically by drop count below.
        removed = feature_flags.clear_cache(guild_id=42)
    assert removed == 1


def test_clear_cache_no_args_drops_everything():
    feature_flags._CACHE[("a", 1)] = (True, "default", 1e18)
    feature_flags._CACHE[("b", 2)] = (False, "default", 1e18)
    assert feature_flags.clear_cache() == 2
    assert not feature_flags._CACHE


def test_clear_cache_by_flag_only():
    feature_flags._CACHE[("a", 1)] = (True, "default", 1e18)
    feature_flags._CACHE[("a", 2)] = (True, "default", 1e18)
    feature_flags._CACHE[("b", 1)] = (False, "default", 1e18)
    assert feature_flags.clear_cache(flag_name="a") == 2
    assert ("a", 1) not in feature_flags._CACHE
    assert ("a", 2) not in feature_flags._CACHE
    assert ("b", 1) in feature_flags._CACHE


# ---------------------------------------------------------------------------
# DB-unreachable bootstrap fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_db_failure_returns_default_and_increments_metric(monkeypatch):
    """The evaluator must never raise; declared default returned + metric fires."""
    monkeypatch.setenv("SUPERBOT_FF_FEATURE_FLAG_PRIMARY", "on")
    feature_flags._reset_metrics_for_tests()

    with patch(
        "utils.db.feature_flag_state.get_guild_override",
        new_callable=AsyncMock,
        side_effect=RuntimeError("connection refused"),
    ):
        decision = await feature_flags.resolve_with_provenance(
            "bindings.primary",
            guild_id=42,
        )
    assert decision.value == BINDINGS_PRIMARY.default_value
    assert decision.source == "bootstrap_fallback"
    assert feature_flags.bootstrap_fallback_count() >= 1


@pytest.mark.asyncio
async def test_db_failure_does_not_raise_into_caller(monkeypatch):
    """is_enabled (the public hot-path) NEVER raises."""
    monkeypatch.setenv("SUPERBOT_FF_FEATURE_FLAG_PRIMARY", "on")

    with patch(
        "utils.db.feature_flag_state.get_guild_override",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB blip"),
    ):
        # Should not raise; we assert by simply awaiting and reading.
        result = await feature_flags.is_enabled("bindings.primary", 42)
    assert isinstance(result, bool)
