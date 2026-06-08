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
        "btd6_list_roster",
        "btd6_capability_lookup",
        "btd6_superlative_lookup",
        "btd6_difficulty_cost",
        "btd6_round_composition",
        "btd6_map_lookup",
        "btd6_mode_lookup",
        "btd6_relic_lookup",
        "btd6_power_lookup",
        "btd6_monkey_knowledge_lookup",
        "btd6_geraldo_lookup",
        "btd6_boss_lookup",
        "btd6_bloon_filter",
        "btd6_cumulative_cost",
        "btd6_power_effect",
        "btd6_paragon_calculate",
        "btd6_paragon_requirements",
        "btd6_paragon_stats_at_degree",
        "btd6_ct_team_status",
    }
    assert set(registry.handlers) == spec_names
    assert isinstance(registry.specs, tuple)


def test_btd6_grounding_tool_allowlist_matches_registered_btd6_tools():
    """The faithfulness ledger allowlist must be exactly the registered
    ``btd6_*`` tools — no non-BTD6 tool may ground a BTD6 answer, and no BTD6
    tool may be silently dropped (drift guard for C1)."""
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    registered = {spec.name for spec in registry.specs}
    btd6_registered = {name for name in registered if name.startswith("btd6_")}

    assert ai_tools.BTD6_GROUNDING_TOOL_NAMES == btd6_registered
    assert all(name.startswith("btd6_") for name in ai_tools.BTD6_GROUNDING_TOOL_NAMES)


async def test_btd6_list_roster_returns_full_verified_rosters():
    """The enumeration tool returns the complete canonical roster + count so a
    'list all heroes / paragons' question is answered, not guessed."""
    heroes = await ai_tools._btd6_list_roster({"kind": "heroes"})
    assert heroes["found"] is True
    assert heroes["count"] == len(heroes["names"]) > 0
    assert "Quincy" in heroes["names"]

    paragons = await ai_tools._btd6_list_roster({"kind": "paragons"})
    assert paragons["count"] == 13
    assert "Apex Plasma Master" in paragons["names"]

    towers = await ai_tools._btd6_list_roster({"kind": "towers"})
    assert towers["found"] is True and towers["count"] > 0

    bad = await ai_tools._btd6_list_roster({"kind": "bloons"})
    assert bad["found"] is False


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

    # No member supplied → no Discord permission role. is_bot_owner is always
    # reported (False here — actor 20 is not the configured bot owner).
    assert result == {"level": 5, "is_new_user": False, "is_bot_owner": False}


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


async def test_btd6_capability_lookup_supports_color_popping_and_notes_coverage():
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)

    black = await registry.handlers["btd6_capability_lookup"](
        {"capability": "black_popping", "unupgraded": True},
    )
    assert black["found"] is True
    ids = {t["id"] for t in black["towers"]}
    # Sharp towers pop black; explosion towers (immune) do not.
    assert "dart_monkey" in ids
    assert "bomb_shooter" not in ids
    # The success result carries the shared coverage note so the model can
    # state its data limits.
    assert "note" in black
    assert "popping" in black["note"].lower()


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

    # Combat ranking — "which paragon has the highest DPS" in one call.
    dps = await registry.handlers["btd6_superlative_lookup"](
        {"metric": "paragon_dps", "limit": 1},
    )
    assert dps["found"] is True
    top = dps["results"][0]
    assert top["unit"] == "DPS (rough)"  # labelled rough, never exact
    assert top["value"] > 0 and "ROUGH" in top["detail"]
    assert "cost" not in top  # combat rows aren't dollar amounts


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


async def test_btd6_power_effect_applies_monkey_boost_to_attack_speed():
    # The bot previously could state what Monkey Boost does but not apply it to a
    # tower's attack stat; this tool grounds "Crossbow Master on a Monkey Boost".
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    assert "btd6_power_effect" in registry.handlers

    result = await registry.handlers["btd6_power_effect"](
        {"power": "Monkey Boost", "tower": "Crossbow Master"},
    )
    assert result["found"] is True
    assert result["power"] == "Monkey Boost"
    assert result["rate_scale"] == 0.5
    assert result["duration_seconds"] == 15
    # rate_scale 0.5 halves cooldown -> doubles attacks/sec (independent rounding
    # of each value leaves a sub-0.01 gap, so compare with tolerance).
    assert (
        abs(result["boosted_attacks_per_second"] - 2 * result["base_attacks_per_second"])
        < 0.01
    )


async def test_btd6_power_effect_rejects_non_attack_powers_and_bad_input():
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    handler = registry.handlers["btd6_power_effect"]

    # Thrive is an economy Power — it must NOT fabricate an attack-speed number.
    thrive = await handler({"power": "Thrive", "tower": "Crossbow Master"})
    assert thrive["found"] is False
    assert "btd6_power_lookup" in thrive["note"]

    # Missing args and unknown power both fail closed.
    assert (await handler({"power": "Monkey Boost", "tower": ""}))["found"] is False
    assert (await handler({"power": "nope", "tower": "Dart Monkey"}))["found"] is False


def test_admin_scope_offers_all_read_only_tools():
    registry = build_registry(scope=AIScope.ADMIN, guild_id=1, actor_id=2)

    names = {spec.name for spec in registry.specs}
    assert names == {
        "get_user_standing",
        "get_server_time",
        "btd6_lookup",
        "btd6_list_roster",
        "btd6_capability_lookup",
        "btd6_superlative_lookup",
        "btd6_difficulty_cost",
        "btd6_round_composition",
        "btd6_map_lookup",
        "btd6_mode_lookup",
        "btd6_relic_lookup",
        "btd6_power_lookup",
        "btd6_monkey_knowledge_lookup",
        "btd6_geraldo_lookup",
        "btd6_boss_lookup",
        "btd6_bloon_filter",
        "btd6_cumulative_cost",
        "btd6_power_effect",
        "btd6_paragon_calculate",
        "btd6_paragon_requirements",
        "btd6_paragon_stats_at_degree",
        "btd6_ct_team_status",
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
    # Credit travels with the result so the model can append the attribution.
    assert out["attribution"]["calculator_url"] == "https://paragon-calc.vercel.app/"
    assert out["attribution"]["author"] == "notausgang0341"


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


async def test_btd6_paragon_stats_at_degree_returns_nonlinear_breakdown():
    registry = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    assert "btd6_paragon_stats_at_degree" in registry.handlers
    h = registry.handlers["btd6_paragon_stats_at_degree"]
    r = await h({"paragon": "Goliath Doomship", "degree": 65})
    assert r["found"] is True
    assert len(r["attacks"]) == 3
    main = r["attacks"][0]
    # Cooldown is the sqrt curve (not linear ~0.49s); the bomb's two projectiles
    # are exposed rather than collapsed to one number.
    assert abs(main["cooldown_seconds"] - 0.4215) < 0.001
    assert {p["name"] for p in main["projectiles"]} >= {"Projectile", "Explosion"}
    # DPS is present but explicitly a rough estimate, never asserted as exact.
    assert r["rough_dps"] > 0
    assert "ROUGH" in r["rough_dps_note"]
    # Degree defaults to 1 when omitted; unknown paragon degrades cleanly.
    assert (await h({"paragon": "Ace"}))["degree"] == 1
    assert (await h({"paragon": "zzz"}))["found"] is False


async def test_btd6_capability_lookup_paragon_camo_split():
    h = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).handlers[
        "btd6_capability_lookup"
    ]
    r = await h({"capability": "camo_detection", "entity": "paragon"})
    assert r["found"] is True and r["entity"] == "paragon"
    cannot = {x["paragon"] for x in r["without_capability"]}
    assert "Herald of Everfrost" in cannot
    assert "Glaive Dominus" in {x["paragon"] for x in r["with_capability"]}
    assert "Heroes do NOT have paragons" in r["note"]
    # Only camo is verified per-paragon.
    bad = await h({"capability": "lead_popping", "entity": "paragon"})
    assert bad["found"] is False


# --- btd6_round_composition / map / mode (committed-data query tools) --------


async def test_btd6_round_composition_aggregates_a_bloon_over_a_range():
    # The live-refused question: "how many purples in rounds 35-70".
    h = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).handlers
    r = await h["btd6_round_composition"](
        {"round_start": 35, "round_end": 70, "bloon": "purples"}
    )
    assert r["found"] is True
    assert r["bloon"] == "Purple Bloon"
    assert r["total"] == 290
    assert r["rounds_with_bloon"] >= 1
    assert all({"round", "count"} <= set(pr) for pr in r["per_round"])


async def test_btd6_round_composition_single_round_full_list_and_errors():
    h = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).handlers
    one = await h["btd6_round_composition"]({"round_start": 63})
    assert one["found"] is True and one["rounds"][0]["round"] == 63
    assert one["rounds"][0]["groups"]
    assert (await h["btd6_round_composition"]({"round_start": 999}))["found"] is False
    assert (await h["btd6_round_composition"]({"round_start": 35, "bloon": "flarp"}))[
        "found"
    ] is False
    assert (await h["btd6_round_composition"]({"round_start": "x"}))["found"] is False


async def test_btd6_map_lookup_single_and_roster():
    h = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).handlers
    logs = await h["btd6_map_lookup"]({"map": "Logs"})
    assert logs["found"] is True and logs["map"]["difficulty"] == "Beginner"
    roster = await h["btd6_map_lookup"]({})
    assert roster["found"] is True and roster["count"] == len(roster["maps"]) >= 3
    assert (await h["btd6_map_lookup"]({"map": "nope"}))["found"] is False


async def test_btd6_mode_lookup_single_and_roster():
    h = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).handlers
    chimps = await h["btd6_mode_lookup"]({"mode": "CHIMPS"})
    assert chimps["found"] is True
    assert chimps["mode"]["starting_lives"] == 1
    assert chimps["mode"]["restrictions"]
    roster = await h["btd6_mode_lookup"]({})
    assert roster["found"] is True and roster["count"] == len(roster["modes"]) >= 2


async def test_btd6_round_composition_ranks_heaviest_rounds():
    # Live bug: the model named r55/r50 the "heaviest" ceramic waves and skipped
    # the larger r76/r78/r74. The tool now ranks them so the model never re-sorts.
    h = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).handlers
    r = await h["btd6_round_composition"](
        {"round_start": 30, "round_end": 80, "bloon": "ceramic"},
    )
    counts = [e["count"] for e in r["heaviest"]]
    assert counts == sorted(counts, reverse=True)  # genuinely ranked, not round order
    assert [(e["round"], e["count"]) for e in r["heaviest"][:3]] == [
        (78, 147),
        (74, 135),
        (63, 122),
    ]
    ranked = [e["round"] for e in r["heaviest"]]
    assert ranked.index(76) < ranked.index(55)  # the exact miss from the live run
    # Without a bloon, the heaviest rounds are ranked by RBE.
    full = await h["btd6_round_composition"]({"round_start": 30, "round_end": 80})
    rbes = [e["rbe"] for e in full["heaviest_by_rbe"]]
    assert rbes == sorted(rbes, reverse=True)


async def test_btd6_relic_lookup_single_category_and_roster():
    h = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).handlers
    sms = await h["btd6_relic_lookup"]({"relic": "Super Monkey Storm"})
    assert sms["found"] is True and sms["relic"]["effect"]
    offense = await h["btd6_relic_lookup"]({"category": "offense"})
    assert offense["found"] is True
    assert offense["count"] == len(offense["relics"]) >= 1
    assert all(r["category"] == "offense" for r in offense["relics"])
    roster = await h["btd6_relic_lookup"]({})
    assert roster["found"] is True and roster["count"] == len(roster["relics"]) >= 24
    assert (await h["btd6_relic_lookup"]({"relic": "nope-not-a-relic"}))[
        "found"
    ] is False
    assert (await h["btd6_relic_lookup"]({"category": "bogus"}))["found"] is False


async def test_btd6_power_lookup_single_and_roster():
    h = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).handlers
    boost = await h["btd6_power_lookup"]({"power": "monkey boost"})
    assert boost["found"] is True
    assert boost["power"]["name"] == "Monkey Boost"
    assert boost["power"]["monkey_money_cost"] == 100
    roster = await h["btd6_power_lookup"]({})
    assert roster["found"] is True and roster["count"] == len(roster["powers"]) >= 20
    assert (await h["btd6_power_lookup"]({"power": "nope-not-a-power"}))["found"] is False


async def test_btd6_monkey_knowledge_lookup_single_category_and_roster():
    h = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).handlers
    one = await h["btd6_monkey_knowledge_lookup"]({"knowledge": "Supa-Thrive"})
    assert one["found"] is True and one["knowledge"]["description"]
    # The dump-native structured magnitude is surfaced on the lookup payload.
    cash = await h["btd6_monkey_knowledge_lookup"]({"knowledge": "More Cash"})
    assert cash["knowledge"]["effect"] == {
        "factors": [{"kind": "starting_cash", "addition": 200, "multiplier": 1}],
    }
    magic = await h["btd6_monkey_knowledge_lookup"]({"category": "Magic"})
    assert magic["found"] is True and magic["count"] >= 1
    assert all(k["category"] == "Magic" for k in magic["knowledge"])
    roster = await h["btd6_monkey_knowledge_lookup"]({})
    assert roster["count"] == len(roster["knowledge"]) >= 100
    assert (await h["btd6_monkey_knowledge_lookup"]({"knowledge": "nope"}))[
        "found"
    ] is False
    assert (await h["btd6_monkey_knowledge_lookup"]({"category": "Bogus"}))[
        "found"
    ] is False


async def test_btd6_geraldo_lookup_single_and_roster():
    h = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).handlers
    one = await h["btd6_geraldo_lookup"]({"item": "Genie Bottle"})
    assert one["found"] is True
    item = one["item"]
    assert item["name"] == "Genie Bottle"
    assert item["cost"] == 2500 and item["unlock_level"] == 12
    assert item["description"]
    # Partial-name match resolves a single item.
    assert (await h["btd6_geraldo_lookup"]({"item": "pickle"}))["item"]["name"] == (
        "Jar of Pickles"
    )
    roster = await h["btd6_geraldo_lookup"]({})
    assert roster["count"] == len(roster["items"]) == 16
    assert (await h["btd6_geraldo_lookup"]({"item": "nope"}))["found"] is False


async def test_btd6_boss_lookup_single_and_roster():
    h = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).handlers
    one = await h["btd6_boss_lookup"]({"boss": "Bloonarius"})
    assert one["found"] is True
    boss = one["boss"]
    assert boss["name"] == "Bloonarius" and boss["description"]
    # Per-tier health is surfaced — tier 3 Bloonarius = 350,000.
    t3 = next(t for t in boss["tiers"] if t["tier"] == 3)
    assert t3["health"] == 350_000
    # Derived immunity surfaces; partial-name match resolves a single boss.
    assert set((await h["btd6_boss_lookup"]({"boss": "dread"}))["boss"]["immune_to"]) == {
        "Cold",
        "Energy",
        "Sharp",
        "Shatter",
    }
    roster = await h["btd6_boss_lookup"]({})
    assert roster["count"] == len(roster["bosses"]) == 7
    assert (await h["btd6_boss_lookup"]({"boss": "nope"}))["found"] is False


async def test_btd6_bloon_filter_traits_and_modifier_note():
    h = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).handlers
    camo = await h["btd6_bloon_filter"]({"property": "camo"})
    assert camo["found"] is True
    assert "DDT" in {b["name"] for b in camo["bloons"]}  # inherently camo
    # The Camo *modifier* is surfaced separately so the answer isn't a closed set.
    assert camo.get("modifiers") and all(
        m["applies_broadly"] for m in camo["modifiers"]
    )
    lead = await h["btd6_bloon_filter"]({"property": "lead"})
    assert {"Lead Bloon", "DDT"} <= {b["name"] for b in lead["bloons"]}
    moab = await h["btd6_bloon_filter"]({"property": "moab"})  # synonym -> moab-class
    assert moab["count"] == 5
    immune = await h["btd6_bloon_filter"]({"immune": "Explosion"})
    assert {"Black Bloon", "DDT"} <= {b["name"] for b in immune["bloons"]}
    assert (await h["btd6_bloon_filter"]({"property": "nonsense-tag"}))[
        "found"
    ] is False
    roster = await h["btd6_bloon_filter"]({})
    assert roster["count"] >= 1 and roster["bloons"]


async def test_btd6_cumulative_cost_sums_base_plus_priors_per_difficulty():
    # Live `grounding_failed` case: "total cost to reach every upgrade, base +
    # all earlier costs". The model couldn't ground the derived sum; the tool
    # makes the total a grounded output. Pinned to the published Tack Shooter
    # table (top path -> Inferno Ring): Medium 50,310; Easy 42,760 (the per-item
    # rounding makes sum-then-scale give the wrong 42,765).
    h = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).handlers
    med = await h["btd6_cumulative_cost"]({"tower": "Tack Shooter", "path": "top"})
    assert med["found"] is True and med["difficulty"] == "medium"
    top = med["paths"]["top"]
    assert top[0]["cumulative_cost"] == 410  # 260 base + 150
    assert top[-1]["name"] == "Inferno Ring"
    assert top[-1]["cumulative_cost"] == 50310
    easy = await h["btd6_cumulative_cost"](
        {"tower": "Tack Shooter", "difficulty": "easy", "path": "top"},
    )
    assert easy["base_cost"] == 220
    assert easy["paths"]["top"][-1]["cumulative_cost"] == 42760  # not 42765
    # Whole-tower (all three paths) + error paths.
    full = await h["btd6_cumulative_cost"]({"tower": "Tack Shooter"})
    assert set(full["paths"]) == {"top", "mid", "bot"}
    assert (await h["btd6_cumulative_cost"]({"tower": "nope"}))["found"] is False
    assert (
        await h["btd6_cumulative_cost"]({"tower": "Tack Shooter", "difficulty": "x"})
    )["found"] is False


# --- diagnostics_health_snapshot (platform owner, PR5) ------------------


def test_diagnostics_tool_absent_below_platform_owner():
    for scope in (AIScope.USER, AIScope.MODERATOR, AIScope.ADMIN, AIScope.SERVER_OWNER):
        registry = build_registry(scope=scope, guild_id=1, actor_id=2)
        assert "diagnostics_health_snapshot" not in {s.name for s in registry.specs}
        assert "diagnostics_health_snapshot" not in registry.handlers


def test_diagnostics_tool_present_at_platform_owner():
    registry = build_registry(scope=AIScope.PLATFORM_OWNER, guild_id=1, actor_id=2)
    assert "diagnostics_health_snapshot" in {s.name for s in registry.specs}
    assert "diagnostics_health_snapshot" in registry.handlers


def test_audience_for_scope_mapping():
    from services.health_contracts import HealthAudience

    assert (
        ai_tools._audience_for_scope(AIScope.PLATFORM_OWNER)
        is HealthAudience.PLATFORM_OWNER
    )
    assert (
        ai_tools._audience_for_scope(AIScope.SERVER_OWNER) is HealthAudience.GUILD_ADMIN
    )
    assert ai_tools._audience_for_scope(AIScope.ADMIN) is HealthAudience.GUILD_ADMIN
    assert ai_tools._audience_for_scope(AIScope.USER) is HealthAudience.PUBLIC


async def test_diagnostics_tool_returns_bounded_json_payload():
    import json

    registry = build_registry(scope=AIScope.PLATFORM_OWNER, guild_id=1, actor_id=2)
    payload = await registry.handlers["diagnostics_health_snapshot"]({})
    json.dumps(payload)  # must be JSON-serializable (no datetimes / enums)
    assert payload["schema_version"] == 1
    assert payload["audience"] == "platform_owner"
    assert isinstance(payload["status"], str)
    assert isinstance(payload["generated_at"], str)  # ISO string, not datetime
    assert len(payload["subsystems"]) <= 16
    assert len(payload["findings"]) <= 12


async def test_diagnostics_tool_fresh_selects_async_lane(monkeypatch):
    import datetime as _dt

    from services import health_snapshot_service as hss
    from services.health_contracts import (
        HealthAudience,
        HealthSnapshot,
        SnapshotStatus,
    )

    def _bare() -> HealthSnapshot:
        return HealthSnapshot(
            snapshot_id="x",
            generated_at=_dt.datetime.now(tz=_dt.timezone.utc),
            purpose="ai_context",
            status=SnapshotStatus.HEALTHY,
            summary="ok",
            subsystems=(),
            findings=(),
            redaction_audience=HealthAudience.PLATFORM_OWNER,
        )

    calls = {"cached": 0, "async": 0}

    def _cached(request, *, bot=None):
        calls["cached"] += 1
        return _bare()

    async def _fresh(request, *, bot=None):
        calls["async"] += 1
        return _bare()

    monkeypatch.setattr(hss, "collect_cached_snapshot", _cached)
    monkeypatch.setattr(hss, "collect_snapshot", _fresh)

    handler = build_registry(
        scope=AIScope.PLATFORM_OWNER, guild_id=1, actor_id=2
    ).handlers["diagnostics_health_snapshot"]
    await handler({})
    await handler({"fresh": True})
    assert calls == {"cached": 1, "async": 1}
