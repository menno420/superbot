"""Canonical AI tool catalogue + deterministic selector (orchestration foundation).

These pin the Phase-1 contract from
``docs/ai/ai-complex-request-tool-orchestration-plan.md``: the catalogue is the single
source of truth for tool metadata, the BTD6 grounding allowlist is *derived* from it, and
the selector can only ever **narrow** the offered set — never grant a tool above the
caller's :class:`AIScope`. Default selection must equal the historical scope-only behaviour.
"""

from __future__ import annotations

import pytest

from core.runtime.ai.contracts import AIScope, AIToolSpec, ToolExclusionReason
from services import ai_tool_catalogue as cat
from services import ai_tools
from services.ai_tool_catalogue import (
    CATALOGUE,
    TOOLSET_BTD6_ROUNDS,
    TOOLSET_SERVER_CONTEXT_SENSITIVE,
    grounding_tool_names,
    scope_allows,
    select_tools,
)
from services.ai_tools import build_registry

_EXPECTED_BTD6_GROUNDING = {
    "btd6_lookup",
    "btd6_list_roster",
    "btd6_capability_lookup",
    "btd6_superlative_lookup",
    "btd6_difficulty_cost",
    "btd6_round_composition",
    "btd6_round_cash",
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


def _spec(name: str, scope: AIScope = AIScope.USER) -> AIToolSpec:
    return AIToolSpec(name=name, description="", parameters={}, min_scope=scope)


def _all_registered_tool_names(monkeypatch) -> set[str]:
    """Every tool name build_registry can offer (highest scope + all runtime gates on)."""
    monkeypatch.setattr(
        "core.runtime.ai.feature_flags.ai_server_member_lookup_enabled",
        lambda: True,
    )
    reg = build_registry(
        scope=AIScope.SYSTEM,
        guild_id=1,
        actor_id=2,
        guild=object(),
        member=object(),
        bot=None,
    )
    return {spec.name for spec in reg.specs}


def test_catalogue_covers_exactly_the_registered_tools(monkeypatch):
    # Drift guard: a new tool without catalogue metadata (or a stale catalogue entry
    # for a removed tool) fails here.
    assert set(CATALOGUE) == _all_registered_tool_names(monkeypatch)


def test_grounding_set_is_derived_from_catalogue_metadata():
    derived = grounding_tool_names("btd6")
    assert derived == _EXPECTED_BTD6_GROUNDING
    # ai_tools re-exports the derived value — they must be the same object/contents.
    assert ai_tools.BTD6_GROUNDING_TOOL_NAMES == derived


def test_grounding_tools_are_exactly_the_btd6_tools():
    # Every grounding tool is a btd6_* tool and every btd6_* tool grounds — no
    # server/config/diagnostics tool may whitelist a BTD6 name/number.
    for name, meta in CATALOGUE.items():
        grounds = meta.grounding_domain == "btd6"
        assert grounds == name.startswith("btd6_"), name


def test_known_toolsets_are_the_declared_families():
    assert cat.known_toolsets() == {
        "btd6_reference",
        "btd6_rounds",
        "btd6_costs",
        "btd6_paragon",
        "btd6_live",
        "server_context_basic",
        "server_context_sensitive",
        "diagnostics",
    }


def test_scope_allows_matches_reexported_helper():
    # ai_tools._scope_allows is now the catalogue's scope_allows (single source).
    assert ai_tools._scope_allows is scope_allows
    assert scope_allows(AIScope.ADMIN, AIScope.USER) is True
    assert scope_allows(AIScope.USER, AIScope.ADMIN) is False


def test_select_default_is_scope_only():
    candidates = [_spec("btd6_lookup"), _spec("get_guild_ai_config", AIScope.ADMIN)]
    decisions = {d.name: d for d in select_tools(candidates, scope=AIScope.USER)}
    assert decisions["btd6_lookup"].included is True
    assert decisions["btd6_lookup"].reason is None
    # Above-scope tool excluded with the authoritative reason, no policy needed.
    assert decisions["get_guild_ai_config"].included is False
    assert decisions["get_guild_ai_config"].reason == ToolExclusionReason.SCOPE_DENIED


def test_enabled_toolset_narrows_but_never_grants_above_scope():
    # The core authority invariant: enabling a toolset that *contains* an admin tool
    # must NOT offer it to a USER — scope wins over toolset policy.
    candidates = [
        _spec("btd6_round_cash"),  # in btd6_rounds — NOT in the enabled set
        _spec("get_guild_ai_config", AIScope.ADMIN),  # in server_context_sensitive
    ]
    decisions = {
        d.name: d
        for d in select_tools(
            candidates,
            scope=AIScope.USER,
            enabled_toolsets={TOOLSET_SERVER_CONTEXT_SENSITIVE},
        )
    }
    assert decisions["get_guild_ai_config"].included is False
    assert decisions["get_guild_ai_config"].reason == ToolExclusionReason.SCOPE_DENIED
    assert decisions["btd6_round_cash"].included is False
    assert decisions["btd6_round_cash"].reason == ToolExclusionReason.TOOLSET_DISABLED


def test_enabled_toolset_keeps_only_matching_scope_allowed_tools():
    candidates = [_spec("btd6_round_cash"), _spec("btd6_paragon_calculate"), _spec("btd6_lookup")]
    decisions = {
        d.name: d
        for d in select_tools(candidates, scope=AIScope.USER, enabled_toolsets={TOOLSET_BTD6_ROUNDS})
    }
    assert decisions["btd6_round_cash"].included is True  # btd6_rounds member
    assert decisions["btd6_paragon_calculate"].reason == ToolExclusionReason.TOOLSET_DISABLED
    assert decisions["btd6_lookup"].reason == ToolExclusionReason.TOOLSET_DISABLED


def test_explicit_disable_wins_over_enabled_toolset():
    candidates = [_spec("btd6_round_cash")]
    decisions = {
        d.name: d
        for d in select_tools(
            candidates,
            scope=AIScope.USER,
            enabled_toolsets={TOOLSET_BTD6_ROUNDS},  # would include it…
            disabled_tools={"btd6_round_cash"},  # …but explicit disable wins
        )
    }
    assert decisions["btd6_round_cash"].included is False
    assert decisions["btd6_round_cash"].reason == ToolExclusionReason.EXPLICITLY_DISABLED


def test_build_registry_default_behaviour_unchanged():
    # Compatibility: no policy → exactly the historical USER toolset.
    names = {s.name for s in build_registry(scope=AIScope.USER, guild_id=1, actor_id=2).specs}
    assert "btd6_round_cash" in names
    assert "get_guild_ai_config" not in names  # admin-only, correctly absent at USER


def test_build_registry_toolset_policy_narrows_end_to_end():
    reg = build_registry(
        scope=AIScope.USER,
        guild_id=1,
        actor_id=2,
        enabled_toolsets={TOOLSET_BTD6_ROUNDS},
    )
    names = {s.name for s in reg.specs}
    # Only btd6_rounds-tagged tools survive; reference/paragon/server tools are gone.
    assert names == {"btd6_round_composition", "btd6_round_cash", "btd6_bloon_filter"}
    assert set(reg.handlers) == names


def test_build_registry_enabling_admin_toolset_does_not_grant_to_user():
    # Even enabling a sensitive toolset, a USER never receives admin tools.
    reg = build_registry(
        scope=AIScope.USER,
        guild_id=1,
        actor_id=2,
        enabled_toolsets={TOOLSET_SERVER_CONTEXT_SENSITIVE},
    )
    names = {s.name for s in reg.specs}
    assert "get_guild_ai_config" not in names
    assert "recent_audit" not in names
