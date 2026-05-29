"""Tests for the read-only AI tool registry — PR-1 foundation.

Pins:

* ``build_registry`` returns provider-neutral specs plus a matching
  handler map.
* Scope gating (``_scope_allows``) is least-privilege: a caller is only
  offered tools at or below their scope.
* The shipped handlers are read-only and return small JSON-serialisable
  dicts.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from core.runtime.ai.contracts import AIScope
from services import ai_tools
from services.ai_tools import _scope_allows, build_registry


def test_build_registry_returns_specs_and_matching_handlers():
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)

    spec_names = {spec.name for spec in registry.specs}
    assert spec_names == {"get_user_standing", "get_server_time"}
    assert set(registry.handlers) == spec_names
    assert isinstance(registry.specs, tuple)


def test_scope_gating_is_least_privilege():
    assert _scope_allows(AIScope.USER, AIScope.USER) is True
    assert _scope_allows(AIScope.USER, AIScope.ADMIN) is False
    assert _scope_allows(AIScope.ADMIN, AIScope.USER) is True
    assert _scope_allows(AIScope.ADMIN, AIScope.ADMIN) is True
    assert _scope_allows(AIScope.PLATFORM_OWNER, AIScope.ADMIN) is True


async def test_server_time_handler_returns_parseable_utc():
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)

    result = await registry.handlers["get_server_time"]({})

    assert "utc" in result
    # Parses as an ISO-8601 timestamp.
    datetime.fromisoformat(result["utc"])


async def test_user_standing_handler_reads_permission_snapshot(monkeypatch):
    async def fake_snapshot(guild_id, user_id):
        assert (guild_id, user_id) == (10, 20)
        return SimpleNamespace(level=5, is_fresh_user=False)

    monkeypatch.setattr(ai_tools.ai_permission_service, "snapshot", fake_snapshot)
    registry = build_registry(scope=AIScope.USER, guild_id=10, actor_id=20)

    result = await registry.handlers["get_user_standing"]({})

    assert result == {"level": 5, "is_new_user": False}


def test_admin_scope_offers_all_read_only_tools():
    registry = build_registry(scope=AIScope.ADMIN, guild_id=1, actor_id=2)

    names = {spec.name for spec in registry.specs}
    assert names == {
        "get_user_standing",
        "get_server_time",
        "get_guild_ai_config",
        "recent_audit",
    }
    assert set(registry.handlers) == names


def test_user_scope_excludes_admin_tools():
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)

    names = {spec.name for spec in registry.specs}
    assert "get_guild_ai_config" not in names
    assert "recent_audit" not in names


async def test_guild_ai_config_handler_reads_snapshot(monkeypatch):
    fake = SimpleNamespace(
        policy=SimpleNamespace(
            enabled=True,
            natural_language_enabled=True,
            default_provider="openai",
            default_model="gpt-4o-mini",
            minimum_level_default=5,
            cooldown_seconds=30,
        ),
        provider=SimpleNamespace(provider_active="openai"),
        memory=SimpleNamespace(window_minutes=60),
    )

    async def fake_build(guild_id, **_kwargs):
        assert guild_id == 99
        return fake

    monkeypatch.setattr(
        ai_tools.ai_config_projection_service,
        "build_snapshot",
        fake_build,
    )
    registry = build_registry(scope=AIScope.ADMIN, guild_id=99, actor_id=1)

    result = await registry.handlers["get_guild_ai_config"]({})

    assert result["ai_enabled"] is True
    assert result["provider"] == "openai"
    assert result["model"] == "gpt-4o-mini"
    assert result["memory_window_minutes"] == 60


async def test_recent_audit_handler_summarises_and_clamps_limit(monkeypatch):
    captured: dict = {}

    async def fake_query(guild_id, *, limit=50, **_kwargs):
        captured["guild_id"] = guild_id
        captured["limit"] = limit
        return [
            {
                "decision": "replied",
                "reason_code": "none",
                "task": "general.nl_answer",
                "created_at": "2026-05-29T12:00:00+00:00",
            },
            {
                "decision": "skipped",
                "reason_code": "not_a_question",
                "task": None,
                "created_at": None,
            },
        ]

    monkeypatch.setattr(ai_tools.ai_decision_audit_service, "query", fake_query)
    registry = build_registry(scope=AIScope.ADMIN, guild_id=7, actor_id=1)

    # A limit above the cap is clamped to 20.
    result = await registry.handlers["recent_audit"]({"limit": 999})

    assert captured["guild_id"] == 7
    assert captured["limit"] == 20
    assert result["rows"][0]["decision"] == "replied"
    assert result["rows"][0]["reason"] == "none"
    assert result["rows"][1]["task"] is None
