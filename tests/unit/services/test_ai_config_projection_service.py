"""AIConfigSnapshot — defaults, drift detection, raw scalars.

Covers the three PR-1 acceptance points for
:mod:`services.ai_config_projection_service`:

1. All-defaults guild (no typed row, empty cache, empty audit) returns
   a populated snapshot without raising; every sub-namespace defaults
   to safe ``None`` / ``0`` values.
2. Drift detection: when the legacy KV value disagrees with the typed
   policy column, ``projection.drift_count`` is positive and the
   offending field carries ``drift=True``.
3. The three explicitly-deferred scalars (memory window, memory scan,
   guild instruction profile body) appear under
   ``projection.raw_scalars`` and NOT under ``projection.fields``.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services import (
    ai_config_projection_service,
    ai_conversation_service,
    ai_decision_audit_service,
    ai_diagnostics_service,
    ai_memory_service,
)
from utils.db import ai as ai_db

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_setting_returning(values: dict[str, object]):
    """Build a fake ``settings_resolution.resolve_setting`` from a dict.

    Returns ``None`` for unknown names (mirroring the production
    behavior when a SettingSpec is missing).
    """

    async def _resolve(_guild_id, _subsystem, name):
        if name not in values:
            return None
        return SimpleNamespace(value=values[name], valid=True, diagnostics=())

    return _resolve


def _seed_diagnostics(monkeypatch, **overrides):
    """Patch ``ai_diagnostics_service.snapshot_for_cog`` with a stub."""
    base = {
        "enabled": False,
        "default_provider": "deterministic",
        "setup_advisor_provider": "deterministic",
        "provider_active": None,
        "degraded": False,
        "last_error_type": None,
        "last_fallback_reason": None,
        "requests_observed": 0,
        "failures_observed": 0,
        "redaction_enabled": True,
    }
    base.update(overrides)
    monkeypatch.setattr(
        ai_diagnostics_service,
        "snapshot_for_cog",
        lambda: dict(base),
    )


@pytest.fixture(autouse=True)
def _reset_conv_cache():
    """Drop the in-process cache between tests so stats() is predictable."""
    ai_conversation_service._reset_for_tests()


# ---------------------------------------------------------------------------
# Test 1 — all-defaults guild returns a safe snapshot
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_defaults_guild_returns_populated_snapshot(monkeypatch):
    """A guild with no typed row, no overrides, no audit, no cache."""
    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))
    monkeypatch.setattr(ai_db, "list_channel_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_category_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_role_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        ai_memory_service,
        "read_memory_settings",
        AsyncMock(return_value=(0, False)),
    )
    monkeypatch.setattr(
        ai_decision_audit_service,
        "query",
        AsyncMock(return_value=[]),
    )
    from services import settings_resolution

    monkeypatch.setattr(
        settings_resolution,
        "resolve_setting",
        _resolve_setting_returning({}),
    )
    _seed_diagnostics(monkeypatch)

    snap = await ai_config_projection_service.build_snapshot(1234)

    # Identity + every sub-namespace present.
    assert snap.guild_id == 1234
    assert snap.policy.guild_id == 1234
    assert snap.policy.enabled is None
    assert snap.policy.channel_override_count == 0
    assert snap.memory.window_minutes == 0
    assert snap.memory.min_floor_turns == ai_conversation_service.MIN_FLOOR_TURNS
    assert snap.memory.cached_channel_count == 0
    assert snap.provider.default_provider == "deterministic"
    assert snap.provider.requests_observed == 0
    # No typed row → no projected fields show drift; raw_scalars present.
    assert snap.projection.drift_count == 0
    assert snap.projection.drift is False
    assert set(snap.projection.raw_scalars.keys()) == {
        "ai_memory_window_minutes",
        "ai_memory_channel_scan_enabled",
        "ai_guild_instruction_profile",
    }
    assert snap.instruction.profile_id is None
    assert snap.audit.latest is None
    assert snap.audit.by_decision == {}
    assert snap.readiness_summary is None


@pytest.mark.asyncio
async def test_db_failures_degrade_gracefully(monkeypatch):
    """Each sub-builder must default safely if its source raises."""

    async def _boom(*_args, **_kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(ai_db, "get_guild_policy", _boom)
    monkeypatch.setattr(ai_memory_service, "read_memory_settings", _boom)
    monkeypatch.setattr(ai_decision_audit_service, "query", _boom)
    from services import settings_resolution

    monkeypatch.setattr(
        settings_resolution,
        "resolve_setting",
        _resolve_setting_returning({}),
    )
    _seed_diagnostics(monkeypatch)

    snap = await ai_config_projection_service.build_snapshot(99)
    assert snap.guild_id == 99
    assert snap.policy.enabled is None
    assert snap.memory.window_minutes == 0
    assert snap.audit.latest is None


# ---------------------------------------------------------------------------
# Test 2 — drift detection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_projection_drift_when_legacy_disagrees_with_typed(monkeypatch):
    """``cooldown_seconds`` differs between KV (legacy) and typed row."""
    typed_row = {
        "guild_id": 1,
        "enabled": True,
        "natural_language_enabled": True,
        "default_provider": "openai",
        "default_model": "gpt-4o-mini",
        "minimum_level_default": 2,
        "cooldown_seconds": 30,
        "fresh_user_mention_allowance": 1,
        "guild_instruction_profile_id": None,
        "generation": 4,
    }
    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(return_value=typed_row),
    )
    monkeypatch.setattr(ai_db, "list_channel_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_category_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_role_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        ai_memory_service,
        "read_memory_settings",
        AsyncMock(return_value=(15, True)),
    )
    monkeypatch.setattr(
        ai_decision_audit_service,
        "query",
        AsyncMock(return_value=[]),
    )
    from services import settings_resolution

    monkeypatch.setattr(
        settings_resolution,
        "resolve_setting",
        _resolve_setting_returning(
            {
                "ai_enabled": True,
                "ai_natural_language_enabled": True,
                "ai_default_provider": "openai",
                "ai_default_model": "gpt-4o-mini",
                "ai_minimum_level_default": 2,
                # Drift: KV says 99, typed says 30
                "ai_cooldown_seconds": 99,
                "ai_fresh_user_mention_allowance": 1,
            },
        ),
    )
    _seed_diagnostics(monkeypatch, default_provider="openai")

    snap = await ai_config_projection_service.build_snapshot(1)

    assert snap.projection.drift is True
    assert snap.projection.drift_count == 1
    cooldown_field = next(
        f for f in snap.projection.fields if f.legacy_key == "ai_cooldown_seconds"
    )
    assert cooldown_field.drift is True
    assert cooldown_field.legacy_value == 99
    assert cooldown_field.typed_value == 30
    # Other fields agree → drift=False
    other_drifts = [
        f for f in snap.projection.fields if f.legacy_key != "ai_cooldown_seconds"
    ]
    assert all(not f.drift for f in other_drifts)


@pytest.mark.asyncio
async def test_missing_typed_row_is_not_drift(monkeypatch):
    """A KV value with no typed row counterpart is NOT drift."""
    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))
    monkeypatch.setattr(ai_db, "list_channel_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_category_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_role_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        ai_memory_service,
        "read_memory_settings",
        AsyncMock(return_value=(0, False)),
    )
    monkeypatch.setattr(
        ai_decision_audit_service,
        "query",
        AsyncMock(return_value=[]),
    )
    from services import settings_resolution

    monkeypatch.setattr(
        settings_resolution,
        "resolve_setting",
        _resolve_setting_returning({"ai_enabled": True}),
    )
    _seed_diagnostics(monkeypatch)

    snap = await ai_config_projection_service.build_snapshot(1)
    # The legacy KV reports True, but no typed row exists yet.
    # Drift is only reported when BOTH sides are populated and disagree.
    assert snap.projection.drift_count == 0


# ---------------------------------------------------------------------------
# Test 3 — deferred scalars under raw_scalars, never under projected fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deferred_scalars_only_in_raw_scalars(monkeypatch):
    """Memory window/scan and the instruction-profile body are not projected."""
    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))
    monkeypatch.setattr(ai_db, "list_channel_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_category_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_role_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        ai_memory_service,
        "read_memory_settings",
        AsyncMock(return_value=(60, True)),
    )
    monkeypatch.setattr(
        ai_decision_audit_service,
        "query",
        AsyncMock(return_value=[]),
    )
    from services import settings_resolution

    monkeypatch.setattr(
        settings_resolution,
        "resolve_setting",
        _resolve_setting_returning(
            {
                "ai_memory_window_minutes": 60,
                "ai_memory_channel_scan_enabled": True,
                "ai_guild_instruction_profile": "Be terse.",
            },
        ),
    )
    _seed_diagnostics(monkeypatch)

    snap = await ai_config_projection_service.build_snapshot(1)
    projected_keys = {f.legacy_key for f in snap.projection.fields}
    assert "ai_memory_window_minutes" not in projected_keys
    assert "ai_memory_channel_scan_enabled" not in projected_keys
    assert "ai_guild_instruction_profile" not in projected_keys
    assert snap.projection.raw_scalars["ai_memory_window_minutes"] == 60
    assert snap.projection.raw_scalars["ai_memory_channel_scan_enabled"] is True
    assert snap.projection.raw_scalars["ai_guild_instruction_profile"] == "Be terse."


# ---------------------------------------------------------------------------
# Test 4 — audit counts populated when rows exist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_snapshot_aggregates_decisions(monkeypatch):
    rows = [
        {"decision": "replied"},
        {"decision": "replied"},
        {"decision": "denied"},
        {"decision": "degraded"},
        {"decision": "denied"},
    ]
    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))
    monkeypatch.setattr(ai_db, "list_channel_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_category_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_role_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        ai_memory_service,
        "read_memory_settings",
        AsyncMock(return_value=(0, False)),
    )
    monkeypatch.setattr(
        ai_decision_audit_service,
        "query",
        AsyncMock(return_value=rows),
    )
    from services import settings_resolution

    monkeypatch.setattr(
        settings_resolution,
        "resolve_setting",
        _resolve_setting_returning({}),
    )
    _seed_diagnostics(monkeypatch)

    snap = await ai_config_projection_service.build_snapshot(1)
    assert snap.audit.recent_total == 5
    assert snap.audit.by_decision == {"replied": 2, "denied": 2, "degraded": 1}
    assert snap.audit.latest == {"decision": "replied"}


# ---------------------------------------------------------------------------
# Test 5 — readiness_summary passes through opaquely
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_readiness_summary_passthrough(monkeypatch):
    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))
    monkeypatch.setattr(ai_db, "list_channel_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_category_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_role_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        ai_memory_service,
        "read_memory_settings",
        AsyncMock(return_value=(0, False)),
    )
    monkeypatch.setattr(
        ai_decision_audit_service,
        "query",
        AsyncMock(return_value=[]),
    )
    from services import settings_resolution

    monkeypatch.setattr(
        settings_resolution,
        "resolve_setting",
        _resolve_setting_returning({}),
    )
    _seed_diagnostics(monkeypatch)

    snap = await ai_config_projection_service.build_snapshot(
        1,
        readiness_summary="Ready",
    )
    assert snap.readiness_summary == "Ready"
