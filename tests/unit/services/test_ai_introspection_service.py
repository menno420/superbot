"""Read-only AI introspection read model (answerability Phase 2).

Pins the composition + audience-filtering contract of
``services.ai_introspection_service``: the service composes existing AI owners (the tool
catalogue, BTD6 data, AI config projection, the policy resolver, and decision audit) into
bounded, typed read models, and redacts by :class:`AIScope` at construction — sensitive
settings / precedence traces / cross-user audit never leak to a lower audience. Every
builder is read-only and deterministic; nothing here writes.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from core.runtime.ai.contracts import AIScope, PolicyDenialReason
from services import ai_config_projection_service as proj
from services import ai_decision_audit_service
from services import ai_introspection_service as svc
from services import ai_natural_language_policy as nlp
from services import ai_tools, btd6_data_service

# Tools that require more than USER scope today (the authority floor the audience
# filter must respect). Kept here so a test reads as the behaviour it pins.
_ADMIN_TOOLS = {"get_guild_ai_config", "recent_audit"}
_PLATFORM_TOOLS = {"diagnostics_health_snapshot"}


# ---------------------------------------------------------------------------
# 1. Tool catalogue snapshot — audience filtering by min_scope
# ---------------------------------------------------------------------------


def test_tool_catalog_user_sees_only_user_tools():
    snap = svc.build_tool_catalog(AIScope.USER)
    names = {t.name for t in snap.tools}

    assert "btd6_round_cash" in names  # a USER tool is offered
    assert names.isdisjoint(_ADMIN_TOOLS)  # admin tools withheld
    assert names.isdisjoint(_PLATFORM_TOOLS)  # platform tools withheld
    # Every visible tool is genuinely USER-scoped — the filter never leaks a higher floor.
    assert all(t.min_scope == "user" for t in snap.tools)
    assert all(t.read_only for t in snap.tools)
    # Names above scope are counted, never enumerated.
    assert snap.hidden_above_scope >= len(_ADMIN_TOOLS) + len(_PLATFORM_TOOLS)
    assert snap.total_visible + snap.hidden_above_scope == len(
        ai_tools.all_tool_specs()
    )


def test_tool_catalog_admin_gains_admin_tools_not_platform():
    snap = svc.build_tool_catalog(AIScope.ADMIN)
    names = {t.name for t in snap.tools}

    assert _ADMIN_TOOLS <= names  # admin tools now visible
    assert names.isdisjoint(_PLATFORM_TOOLS)  # platform-owner tool still hidden
    assert snap.hidden_above_scope == len(_PLATFORM_TOOLS)


def test_tool_catalog_platform_owner_sees_everything():
    snap = svc.build_tool_catalog(AIScope.PLATFORM_OWNER)
    names = {t.name for t in snap.tools}

    assert _PLATFORM_TOOLS <= names
    assert snap.hidden_above_scope == 0
    assert snap.total_visible == len(ai_tools.all_tool_specs())


def test_tool_catalog_joins_catalogue_metadata():
    snap = svc.build_tool_catalog(AIScope.USER)
    by_name = {t.name: t for t in snap.tools}

    cash = by_name["btd6_round_cash"]
    assert cash.grounds_btd6 is True
    assert "btd6_rounds" in cash.toolsets and "btd6_costs" in cash.toolsets
    assert cash.purpose  # the spec description flows through as the tool's purpose

    clock = by_name["get_server_time"]
    assert clock.grounds_btd6 is False  # a server tool never grounds a BTD6 answer
    assert clock.toolsets == ("server_context_basic",)

    # toolsets_present is the union actually offered to this audience.
    assert "btd6_rounds" in snap.toolsets_present
    assert "server_context_basic" in snap.toolsets_present


def test_tool_catalog_is_deterministic():
    a = svc.build_tool_catalog(AIScope.ADMIN)
    b = svc.build_tool_catalog(AIScope.ADMIN)
    assert a == b  # pure read — repeatable, no side effects


# ---------------------------------------------------------------------------
# 2. BTD6 answerability snapshot
# ---------------------------------------------------------------------------


def test_btd6_answerability_inventories_fixture_domains():
    snap = svc.build_btd6_answerability()
    assert snap.available is True
    assert snap.data_version  # populated from the loaded dataset
    by_name = {d.name: d for d in snap.domains}

    # Real fixtures ship in the repo — counts are positive and reflect the dataset.
    for domain in ("towers", "heroes", "rounds", "abr_rounds", "bloons", "bosses"):
        assert by_name[domain].kind == "deterministic_fixture"
        assert (by_name[domain].item_count or 0) > 0


def test_btd6_answerability_distinguishes_calculation_live_unsupported():
    snap = svc.build_btd6_answerability()
    by_name = {d.name: d for d in snap.domains}

    assert by_name["round_cash"].kind == "calculation"
    assert by_name["ct_team_status"].kind == "live"
    # ABR graduated from the unsupported list to a fixture (abr_rounds.json);
    # the remaining round-set gap names the quest/Rogue/Frontier sets.
    assert by_name["abr_rounds"].kind == "deterministic_fixture"
    assert "alternate_round_sets" not in by_name
    # Known gaps are named explicitly so an answer never overclaims them.
    assert by_name["other_round_sets"].kind == "unsupported"
    assert by_name["achievements"].kind == "unsupported"
    # Non-fixture domains carry no item_count (no false "we have N rows" implication).
    assert by_name["round_cash"].item_count is None
    assert by_name["other_round_sets"].item_count is None


def test_btd6_answerability_degrades_when_data_unavailable(monkeypatch):
    monkeypatch.setattr(btd6_data_service, "data_available", lambda: False)
    snap = svc.build_btd6_answerability()
    assert snap.available is False
    assert snap.domains == ()
    assert snap.data_version == ""


# ---------------------------------------------------------------------------
# 3. AI settings view — audience redaction
# ---------------------------------------------------------------------------


def _config_snapshot(**overrides) -> proj.AIConfigSnapshot:
    """A fully-populated synthetic config snapshot; overrides tune individual fields."""
    o = {
        "guild_id": 7,
        "enabled": True,
        "nl_enabled": True,
        "provider": "openai",
        "model": "gpt-x",
        "min_level": 2,
        "cooldown": 30,
        "channel_overrides": 4,
        "category_overrides": 1,
        "role_overrides": 2,
        "drift_count": 3,
        "profile_name": "Helpful",
        "window_minutes": 120,
        "degraded": True,
        "last_error_type": "TimeoutError",
        "requests": 11,
        "failures": 2,
        "provider_active": "anthropic",
        **overrides,
    }
    return proj.AIConfigSnapshot(
        guild_id=o["guild_id"],
        policy=proj.PolicySnapshot(
            guild_id=o["guild_id"],
            enabled=o["enabled"],
            natural_language_enabled=o["nl_enabled"],
            default_provider=o["provider"],
            default_model=o["model"],
            minimum_level_default=o["min_level"],
            cooldown_seconds=o["cooldown"],
            channel_override_count=o["channel_overrides"],
            category_override_count=o["category_overrides"],
            role_override_count=o["role_overrides"],
        ),
        memory=proj.MemorySnapshot(
            window_minutes=o["window_minutes"],
            scan_enabled=True,
            cached_channel_count=0,
            cached_total_turns=0,
            per_channel_cap=50,
            channel_lru_cap=100,
            min_floor_turns=4,
        ),
        provider=proj.ProviderSnapshot(
            enabled=o["enabled"],
            default_provider=o["provider"],
            setup_advisor_provider=o["provider"],
            provider_active=o["provider_active"],
            degraded=o["degraded"],
            last_error_type=o["last_error_type"],
            last_fallback_reason=None,
            requests_observed=o["requests"],
            failures_observed=o["failures"],
            redaction_enabled=True,
        ),
        projection=proj.ProjectionSnapshot(drift_count=o["drift_count"]),
        instruction=proj.InstructionSnapshot(profile_name=o["profile_name"]),
        audit=proj.AuditSnapshot(),
    )


async def test_settings_view_user_sees_only_enabled_flags(monkeypatch):
    monkeypatch.setattr(
        proj, "build_snapshot", AsyncMock(return_value=_config_snapshot())
    )
    view = await svc.build_ai_settings_view(7, scope=AIScope.USER)

    assert view.ai_enabled is True
    assert view.natural_language_enabled is True
    # Everything else is withheld below admin.
    assert view.provider is None
    assert view.model is None
    assert view.minimum_level_default is None
    assert view.channel_override_count is None
    assert view.provider_degraded is None


async def test_settings_view_admin_sees_effective_config_not_diagnostics(monkeypatch):
    monkeypatch.setattr(
        proj, "build_snapshot", AsyncMock(return_value=_config_snapshot())
    )
    view = await svc.build_ai_settings_view(7, scope=AIScope.ADMIN)

    assert view.provider == "openai"
    assert view.model == "gpt-x"
    assert view.minimum_level_default == 2
    assert view.cooldown_seconds == 30
    assert view.memory_window_minutes == 120
    assert view.channel_override_count == 4
    assert view.projection_drift_count == 3
    assert view.instruction_profile_name == "Helpful"
    # Provider runtime diagnostics stay platform-owner-only.
    assert view.provider_degraded is None
    assert view.provider_last_error_type is None
    assert view.requests_observed is None


async def test_settings_view_platform_owner_sees_provider_diagnostics(monkeypatch):
    monkeypatch.setattr(
        proj, "build_snapshot", AsyncMock(return_value=_config_snapshot())
    )
    view = await svc.build_ai_settings_view(7, scope=AIScope.PLATFORM_OWNER)

    assert view.provider == "openai"  # still sees admin tier
    assert view.provider_degraded is True
    assert view.provider_last_error_type == "TimeoutError"
    assert view.requests_observed == 11
    assert view.failures_observed == 2


async def test_settings_view_provider_falls_back_to_active(monkeypatch):
    # No default_provider configured → admin sees the live active provider, not None.
    snap = _config_snapshot(provider=None, provider_active="anthropic")
    monkeypatch.setattr(proj, "build_snapshot", AsyncMock(return_value=snap))
    view = await svc.build_ai_settings_view(7, scope=AIScope.ADMIN)
    assert view.provider == "anthropic"


# ---------------------------------------------------------------------------
# 4. Policy / recent-decision explanation
# ---------------------------------------------------------------------------


_CTX = nlp.MessageContext(
    guild_id=1,
    channel_id=2,
    category_id=None,
    user_id=3,
    user_level=5,
    user_role_ids=(),
    is_mention=True,
    is_fresh_user=False,
)


def _decision(**overrides) -> nlp.PolicyDecision:
    o = {
        "allowed": True,
        "reason": PolicyDenialReason.NONE,
        "mode": "always_reply",
        "source": "channel",
        "trace": (
            "guild_ai_gate: AI enabled=true",
            "channel_policy: mode=always_reply",
        ),
        **overrides,
    }
    return nlp.PolicyDecision(
        allowed=o["allowed"],
        reason_code=o["reason"],
        effective_min_level=2,
        effective_cooldown=30,
        effective_mode=o["mode"],
        effective_source=o["source"],
        precedence_trace=o["trace"],
    )


async def test_policy_explanation_user_hides_trace_and_history(monkeypatch):
    resolve = AsyncMock(return_value=_decision())
    query = AsyncMock(return_value=[{"decision": "replied", "reason_code": "none"}])
    monkeypatch.setattr(nlp, "resolve", resolve)
    monkeypatch.setattr(ai_decision_audit_service, "query", query)

    out = await svc.build_policy_explanation(_CTX, scope=AIScope.USER)

    assert out.allowed is True
    assert out.reason_code == "none"
    assert out.effective_mode == "always_reply"
    assert out.effective_source == "channel"
    # Server policy internals are admin+ only.
    assert out.precedence_trace == ()
    assert out.recent_decisions == ()
    # A user explanation never builds the trace and never reads cross-user audit.
    resolve.assert_awaited_once_with(_CTX, dry_run=False)
    query.assert_not_awaited()


async def test_policy_explanation_admin_includes_trace_and_recent(monkeypatch):
    resolve = AsyncMock(return_value=_decision())
    query = AsyncMock(
        return_value=[
            {
                "decision": "denied",
                "reason_code": "cooldown_active",
                "task": "btd6.answer",
                "created_at": "2026-06-09T12:00:00",
            },
        ],
    )
    monkeypatch.setattr(nlp, "resolve", resolve)
    monkeypatch.setattr(ai_decision_audit_service, "query", query)

    out = await svc.build_policy_explanation(_CTX, scope=AIScope.ADMIN)

    assert out.precedence_trace == _decision().precedence_trace
    assert len(out.recent_decisions) == 1
    assert out.recent_decisions[0].decision == "denied"
    assert out.recent_decisions[0].reason_code == "cooldown_active"
    assert out.recent_decisions[0].at == "2026-06-09T12:00:00"
    resolve.assert_awaited_once_with(_CTX, dry_run=True)
    query.assert_awaited_once()


async def test_policy_explanation_audit_failure_degrades(monkeypatch):
    monkeypatch.setattr(
        nlp,
        "resolve",
        AsyncMock(
            return_value=_decision(
                allowed=False, reason=PolicyDenialReason.COOLDOWN_ACTIVE
            )
        ),
    )
    monkeypatch.setattr(
        ai_decision_audit_service,
        "query",
        AsyncMock(side_effect=RuntimeError("db down")),
    )

    out = await svc.build_policy_explanation(_CTX, scope=AIScope.ADMIN)

    # The authoritative decision still comes back; only the supplementary history is empty.
    assert out.allowed is False
    assert out.reason_code == "cooldown_active"
    assert out.recent_decisions == ()
