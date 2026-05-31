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
    assert spec_names == {
        "get_user_standing",
        "get_server_time",
        "btd6_lookup",
        "btd6_capability_lookup",
        "btd6_superlative_lookup",
        "btd6_difficulty_cost",
        "btd6_paragon_calculate",
        "btd6_paragon_requirements",
    }
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

    # No member supplied → XP-only result (permission role omitted).
    assert result == {"level": 5, "is_new_user": False}


async def test_user_standing_includes_discord_role_for_owner(monkeypatch):
    """Regression: 'what are my permissions, use your tools' must return the
    asker's Discord permission role, not just XP.

    The tool previously returned only level/is_new_user, so when a server
    owner asked, the model inferred 'no admin status' from the tool's silence
    and told them they were a regular member — contradicting the (correct)
    bot_user_identity span. The tool now resolves the live permission tier
    with the same resolver the span uses, so the two always agree.
    """

    async def fake_snapshot(guild_id, user_id):
        return SimpleNamespace(level=39, is_fresh_user=False)

    monkeypatch.setattr(ai_tools.ai_permission_service, "snapshot", fake_snapshot)

    # member.id == guild.owner_id → resolve_user_tier returns "server_owner".
    owner = SimpleNamespace(
        id=777,
        guild=SimpleNamespace(owner_id=777),
        guild_permissions=SimpleNamespace(administrator=True, manage_guild=True),
    )
    registry = build_registry(
        scope=AIScope.USER,
        guild_id=1,
        actor_id=777,
        member=owner,
    )

    result = await registry.handlers["get_user_standing"]({})

    assert result["server_role"] == "server_owner"
    assert result["is_server_owner"] is True
    assert result["has_admin_access"] is True
    # XP fields are still present alongside the permission role.
    assert result["level"] == 39
    assert result["is_new_user"] is False


async def test_user_standing_regular_member_reports_no_admin(monkeypatch):
    async def fake_snapshot(guild_id, user_id):
        return SimpleNamespace(level=5, is_fresh_user=False)

    monkeypatch.setattr(ai_tools.ai_permission_service, "snapshot", fake_snapshot)

    member = SimpleNamespace(
        id=2,
        guild=SimpleNamespace(owner_id=999),
        guild_permissions=SimpleNamespace(administrator=False, manage_guild=False),
    )
    registry = build_registry(
        scope=AIScope.USER,
        guild_id=1,
        actor_id=2,
        member=member,
    )

    result = await registry.handlers["get_user_standing"]({})

    assert result["server_role"] == "user"
    assert result["is_server_owner"] is False
    assert result["has_admin_access"] is False


async def test_btd6_lookup_handler_grounds_named_entity_and_reports_misses():
    # Offered at USER scope so any user's BTD6 question can self-ground without
    # a keyword router gate. Wraps the real grounding pipeline (DB passes
    # degrade to no-ops here; the fixture pass still runs).
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    assert "btd6_lookup" in registry.handlers

    hit = await registry.handlers["btd6_lookup"](
        {"query": "can a dart monkey pop lead?"},
    )
    assert hit["found"] is True
    assert hit["facts"]
    assert any("Dart Monkey" in line for line in hit["facts"])

    miss = await registry.handlers["btd6_lookup"]({"query": "zzzqqq not a bloon"})
    assert miss["found"] is False
    assert miss["facts"] == []


async def test_btd6_lookup_handler_handles_empty_query():
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    result = await registry.handlers["btd6_lookup"]({"query": "  "})
    assert result["found"] is False


async def test_btd6_capability_lookup_answers_discovery_questions():
    # Offered at USER scope; backs "which tower …" questions the resolver
    # cannot answer. Verified against the real committed stats.
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    assert "btd6_capability_lookup" in registry.handlers

    camo = await registry.handlers["btd6_capability_lookup"](
        {"capability": "camo_detection", "unupgraded": True},
    )
    assert camo["found"] is True
    ids = {t["id"] for t in camo["towers"]}
    assert "ninja_monkey" in ids  # the canonical unupgraded camo-detector
    assert "dart_monkey" not in ids

    unsupported = await registry.handlers["btd6_capability_lookup"](
        {"capability": "flies"},
    )
    assert unsupported["found"] is False


async def test_btd6_superlative_lookup_answers_cost_rankings():
    # "most expensive tier-4 upgrade" and friends — verified vs real data.
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    assert "btd6_superlative_lookup" in registry.handlers

    tier4 = await registry.handlers["btd6_superlative_lookup"](
        {"metric": "upgrade_cost", "tier": 4},
    )
    assert tier4["found"] is True
    assert tier4["results"][0]["tower_id"] == "super_monkey"  # Sun Temple, $100k
    assert tier4["results"][0]["cost"] == 100000

    cheapest = await registry.handlers["btd6_superlative_lookup"](
        {"metric": "tower_cost", "cheapest": True},
    )
    assert cheapest["results"][0]["tower_id"] == "dart_monkey"

    # limit lets the model list them all (incl. the Dart Monkey paragon).
    default_n = await registry.handlers["btd6_superlative_lookup"](
        {"metric": "paragon_cost", "cheapest": True},
    )
    assert len(default_n["results"]) == 3  # default top-3
    full = await registry.handlers["btd6_superlative_lookup"](
        {"metric": "paragon_cost", "cheapest": True, "limit": 25},
    )
    assert len(full["results"]) > 3
    assert any(
        r["tower_id"] == "dart_monkey" and r["cost"] == 150000 for r in full["results"]
    )

    bad = await registry.handlers["btd6_superlative_lookup"]({"metric": "nope"})
    assert bad["found"] is False


async def test_btd6_difficulty_cost_converts_medium_to_all_difficulties():
    # The bot previously claimed BTD6 costs don't change by difficulty; this
    # tool gives the exact per-difficulty figures so it can't make that claim.
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    assert "btd6_difficulty_cost" in registry.handlers

    result = await registry.handlers["btd6_difficulty_cost"]({"medium_cost": 200})
    assert result["found"] is True
    costs = result["costs_by_difficulty"]
    assert costs == {"easy": 170, "medium": 200, "hard": 215, "impoppable": 240}

    assert (await registry.handlers["btd6_difficulty_cost"]({"medium_cost": 0}))[
        "found"
    ] is False
    assert (await registry.handlers["btd6_difficulty_cost"]({"medium_cost": "x"}))[
        "found"
    ] is False


def test_admin_scope_offers_all_read_only_tools():
    registry = build_registry(scope=AIScope.ADMIN, guild_id=1, actor_id=2)

    names = {spec.name for spec in registry.specs}
    assert names == {
        "get_user_standing",
        "get_server_time",
        "btd6_lookup",
        "btd6_capability_lookup",
        "btd6_superlative_lookup",
        "btd6_difficulty_cost",
        "btd6_paragon_calculate",
        "btd6_paragon_requirements",
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


# --- paragon tools (forward + reverse, structured envelopes) ----------------


def _canned_paragon_success(degree: int = 74) -> tuple[int, dict]:
    return (
        200,
        {
            "success": True,
            "api_version": "1.1",
            "result": {
                "degree": degree,
                "total_power": 147800,
                "power_for_next_degree": 2053,
                "next_degree": min(100, degree + 1),
                "breakdown": {
                    "pops": {
                        "power": 44444,
                        "max_power": 90000,
                        "capped": False,
                        "fill_pct": 49.38,
                    },
                    "upgrades": {
                        "power": 6000,
                        "max_power": 10000,
                        "capped": False,
                        "fill_pct": 60.0,
                    },
                    "cash": {
                        "power": 20000,
                        "max_power": 60000,
                        "capped": False,
                        "fill_pct": 33.33,
                    },
                    "extra_t5s": {
                        "power": 6000,
                        "max_power": 50000,
                        "capped": False,
                        "fill_pct": 12.0,
                    },
                    "totems": {
                        "power": 10000,
                        "max_power": None,
                        "capped": False,
                        "fill_pct": None,
                    },
                },
                "warnings": [],
                "wasted_cash": 0,
                "paragon": {
                    "id": "apex_plasma_master",
                    "name": "Apex Plasma Master",
                    "tower": "Dart Monkey",
                    "base_price": 150000,
                    "difficulty": "medium",
                    "game_mode": "solo",
                },
            },
            "rate_limit": {
                "limit": 60,
                "remaining": 59,
                "reset_in_seconds": 60,
                "window": "60s",
            },
        },
    )


async def test_paragon_calculate_tool_returns_degree(monkeypatch):
    from services import paragon_service

    async def fake_post(_payload):
        return _canned_paragon_success(74)

    monkeypatch.setattr(paragon_service, "_http_post", fake_post)
    paragon_service._reset_for_tests()

    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    out = await registry.handlers["btd6_paragon_calculate"](
        {"tower": "Dart Monkey", "pops": 8_000_000},
    )

    assert out["success"] is True
    assert out["error"] is None
    assert out["estimated"] is False
    assert out["result"]["degree"] == 74
    assert set(out["result"]["breakdown"]) == {
        "pops",
        "upgrades",
        "cash",
        "extra_t5s",
        "totems",
    }
    assert out["result"]["paragon"]["id"] == "apex_plasma_master"


async def test_paragon_calculate_tool_missing_tower_is_structured():
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    out = await registry.handlers["btd6_paragon_calculate"]({})
    assert out["success"] is False
    assert out["error"]["code"] == "missing_field"


async def test_paragon_calculate_tool_unknown_tower_is_structured(monkeypatch):
    from services import paragon_service

    async def fake_post(_payload):
        return (
            400,
            {
                "success": False,
                "error": {"code": "UNKNOWN_TOWER", "message": "no match"},
                "valid_towers": ["Dart Monkey"],
            },
        )

    monkeypatch.setattr(paragon_service, "_http_post", fake_post)
    paragon_service._reset_for_tests()

    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    out = await registry.handlers["btd6_paragon_calculate"]({"tower": "zzzqqq"})

    assert out["success"] is False
    assert out["error"]["code"] == "unknown_tower"
    assert out["error"]["valid_towers"] == ["Dart Monkey"]


async def test_paragon_calculate_tool_rate_limited_is_structured(monkeypatch):
    from services import paragon_service

    async def fake_post(_payload):
        return (
            429,
            {
                "success": False,
                "error": {"code": "RATE_LIMITED", "message": "slow", "retry_after": 12},
            },
        )

    monkeypatch.setattr(paragon_service, "_http_post", fake_post)
    paragon_service._reset_for_tests()

    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    out = await registry.handlers["btd6_paragon_calculate"]({"tower": "Dart Monkey"})

    assert out["success"] is False
    assert out["error"]["code"] == "rate_limited"
    assert out["error"]["retry_after"] == 12


async def test_paragon_requirements_tool_returns_build(monkeypatch):
    from services import paragon_service

    async def fake_post(_payload):
        return _canned_paragon_success(90)

    monkeypatch.setattr(paragon_service, "_http_post", fake_post)
    paragon_service._reset_for_tests()

    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    out = await registry.handlers["btd6_paragon_requirements"](
        {"tower": "Dart Monkey", "target_degree": 90, "strategy": "least_cash"},
    )

    assert out["success"] is True
    result = out["result"]
    assert result["target_degree"] == 90
    assert result["strategy"] == "least_cash"
    assert result["paragon"]["id"] == "apex_plasma_master"
    assert {
        "pops",
        "cash_spent",
        "upgrade_count",
        "tier5_count",
        "geraldo_totems",
    } <= set(result["recommended_inputs"])


async def test_paragon_requirements_tool_validates_target():
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    out = await registry.handlers["btd6_paragon_requirements"](
        {"tower": "Dart Monkey", "target_degree": 250},
    )
    assert out["success"] is False
    assert out["error"]["code"] == "invalid_target"
