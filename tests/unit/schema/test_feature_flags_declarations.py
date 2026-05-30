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
)
from core.runtime.feature_flags import _register_builtins as _register_builtins
from core.runtime.feature_flags import _reset_for_tests as _reset_flags
from core.runtime.feature_flags import (
    all_flags,
    declared_names,
    get,
    register,
)


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


# ---------------------------------------------------------------------------
# PR2 — audience / db_editable / label
# ---------------------------------------------------------------------------


def test_audience_and_db_editable_defaults(_clean_flags):
    """A flag is internal + DB-editable + label-less unless told otherwise."""
    register(FeatureFlag(name="x", description="x", default_value=False))
    fetched = get("x")
    assert fetched.audience == "internal"
    assert fetched.db_editable is True
    assert fetched.label == ""


def test_only_operator_flags_carry_operator_audience():
    """Exactly the two operator-facing flags are tagged audience=operator."""
    operator = {
        name for name, flag in all_flags().items() if flag.audience == "operator"
    }
    assert operator == {
        "settings.manager_cog.enabled",
        "youtube.context.enabled",
    }


def test_meta_flag_is_not_db_editable():
    """feature_flag.primary is env-only — its DB override is ignored, so the
    editor must treat it as non-editable. The rollout gates stay editable.
    """
    assert get("feature_flag.primary").db_editable is False
    assert get("bindings.primary").db_editable is True


def test_snapshot_exposes_audience_editable_label():
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("feature_flags")
    assert "by_audience" in snap
    assert snap["by_audience"].get("operator", 0) >= 2
    info = snap["by_name"]["settings.manager_cog.enabled"]
    assert info["audience"] == "operator"
    assert info["db_editable"] is True
    assert info["label"]  # non-empty operator-facing label
    assert snap["by_name"]["feature_flag.primary"]["db_editable"] is False
