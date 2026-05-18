"""Phase 1d unit tests — feature flag declaration registry.

Verifies the declaration-only surface of
:mod:`core.runtime.feature_flags`.  Phase 2d will add a separate set of
tests for the runtime evaluator (``is_enabled``, environment tier
resolution, rollout policy gating).
"""

from __future__ import annotations

import pytest

from core.runtime.feature_flags import (
    EnvironmentTier,
    FeatureFlag,
    RolloutPolicy,
    all_flags,
    declared_names,
    get,
    register,
)
from core.runtime.feature_flags import _reset_for_tests as _reset_flags
from core.runtime.feature_flags import _register_builtins as _register_builtins


@pytest.fixture
def _clean_flags():
    _reset_flags()
    try:
        yield
    finally:
        _reset_flags()
        _register_builtins()


def test_register_and_lookup(_clean_flags):
    flag = FeatureFlag(
        name="alpha.beta.enabled",
        description="Test",
        default_value=False,
    )
    register(flag)
    assert get("alpha.beta.enabled") is flag


def test_register_re_registration_replaces(_clean_flags):
    a = FeatureFlag(name="x", description="a", default_value=False)
    b = FeatureFlag(name="x", description="b", default_value=True)
    register(a)
    register(b)
    assert get("x").description == "b"
    assert get("x").default_value is True


def test_declared_names_sorted(_clean_flags):
    register(FeatureFlag(name="zulu", description="z", default_value=False))
    register(FeatureFlag(name="alpha", description="a", default_value=False))
    assert declared_names() == ["alpha", "zulu"]


def test_environment_overrides_field(_clean_flags):
    flag = FeatureFlag(
        name="x",
        description="x",
        default_value=False,
        environment_overrides={
            EnvironmentTier.CANARY: True,
            EnvironmentTier.BETA: True,
        },
    )
    register(flag)
    snap = all_flags()
    assert snap["x"].environment_overrides[EnvironmentTier.CANARY] is True


def test_rollout_policy_field(_clean_flags):
    flag = FeatureFlag(
        name="x",
        description="x",
        default_value=False,
        rollout_policy=RolloutPolicy(
            staged_guilds=(1, 2, 3),
            percentage_rollout=25,
            tier_gate=EnvironmentTier.BETA,
        ),
    )
    register(flag)
    fetched = get("x")
    assert fetched.rollout_policy.percentage_rollout == 25
    assert fetched.rollout_policy.tier_gate is EnvironmentTier.BETA


def test_builtin_phase1d_flags_registered():
    """The Phase 1d platform-level flags must register at import time."""
    declared = declared_names()
    expected = {
        "resources.unified",
        "bindings.primary",
        "participation.enabled",
        "feature_flag.primary",
    }
    missing = expected - set(declared)
    assert not missing, f"missing Phase 1d built-in flags: {missing}"


def test_diagnostics_provider_registered():
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("feature_flags")
    assert snap["declared_total"] >= 4
    assert "platform" in snap["by_owner"]
