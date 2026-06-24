"""Canonical AI tool catalogue + deterministic selection — the orchestration foundation.

This is the single source of truth for per-tool **selection metadata** (which toolset(s)
a tool belongs to, whether it grounds a BTD6 answer, and forward-looking budget/freshness
hints). It is deliberately separate from:

- ``core.runtime.ai.contracts.AIToolSpec`` — the provider-facing data the model sees;
- ``services.ai_tools`` — where the specs and their (runtime-bound) handlers live.

``services.ai_tools.build_registry`` consults this catalogue to decide which scope-allowed
tools to offer, and derives the BTD6 grounding allowlist from it (``grounding_tool_names``)
so the allowlist can no longer drift from the registered tool set by hand.

**Authority is never widened here.** ``AIToolSpec.min_scope`` stays authoritative: the
selector can *remove* a scope-allowed tool (an operator disabling a toolset) but can never
grant a tool above the caller's :class:`AIScope`. See
``docs/ai/ai-complex-request-tool-orchestration-plan.md`` §5 (catalogue/toolsets/selection).

Phase 1 of that plan: catalogue + deterministic selector, compatibility-preserving. Budgets,
preflight, task-affinity narrowing, requirement modes, storage, and UI are later phases.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass

from core.runtime.ai.contracts import (
    AIScope,
    AITask,
    AIToolMetadata,
    AIToolSpec,
    ToolExclusionReason,
)

# --- Named toolsets (plan §5.2) ---------------------------------------------
# Stable string identifiers so an orchestration profile can name a family without
# enumerating tools. ``btd6_grounding`` is intentionally NOT a stored toolset — it is
# *derived* from ``grounding_domain`` metadata (see ``grounding_tool_names``).

TOOLSET_BTD6_REFERENCE = "btd6_reference"
TOOLSET_BTD6_ROUNDS = "btd6_rounds"
TOOLSET_BTD6_COSTS = "btd6_costs"
TOOLSET_BTD6_PARAGON = "btd6_paragon"
TOOLSET_BTD6_LIVE = "btd6_live"
TOOLSET_SERVER_CONTEXT_BASIC = "server_context_basic"
TOOLSET_SERVER_CONTEXT_SENSITIVE = "server_context_sensitive"
TOOLSET_DIAGNOSTICS = "diagnostics"
TOOLSET_SELF_AWARENESS = "self_awareness"
# Support tickets — the one *action* toolset. ``open_support_ticket`` writes
# (it opens a ticket through the audited mutation seam), unlike every other
# catalogued tool, which is read-only.
TOOLSET_TICKET = "support_ticket"

# --- Scope ordering (canonical home; re-exported by ai_tools as _scope_allows) ----

_SCOPE_RANK: dict[AIScope, int] = {
    AIScope.USER: 0,
    AIScope.MODERATOR: 1,
    AIScope.ADMIN: 2,
    AIScope.SERVER_OWNER: 3,
    AIScope.PLATFORM_OWNER: 4,
    AIScope.SYSTEM: 5,
}


def scope_allows(caller: AIScope, required: AIScope) -> bool:
    """True if ``caller`` is privileged enough to be offered ``required``."""
    return _SCOPE_RANK.get(caller, 0) >= _SCOPE_RANK.get(required, 0)


# --- The catalogue ----------------------------------------------------------


def _btd6(
    *toolsets: str,
    freshness: str = "static",
    cost_class: str = "cheap",
) -> AIToolMetadata:
    """A read-only BTD6 fact/calculation tool: grounds BTD6 answers, static fixture
    data by default. ``freshness="live"`` for the Ninja-Kiwi-backed ones.
    """
    return AIToolMetadata(
        toolsets=frozenset(toolsets),
        task_affinity=frozenset({AITask.BTD6_ANSWER}),
        grounding_domain="btd6",
        cost_class=cost_class,  # type: ignore[arg-type]
        freshness=freshness,  # type: ignore[arg-type]
    )


def _server(*toolsets: str) -> AIToolMetadata:
    """A read-only server/diagnostics context tool — live Discord/runtime state, not a
    BTD6 grounding fact.
    """
    return AIToolMetadata(toolsets=frozenset(toolsets), freshness="live")


# One entry per registered tool in ``ai_tools.build_registry``. An invariant test
# (``tests/unit/services/test_ai_tool_catalogue.py``) pins this set == the registered
# tool names, so a new tool without catalogue metadata (or vice versa) fails CI.
CATALOGUE: dict[str, AIToolMetadata] = {
    # --- BTD6 reference lookups (static fixture data) ---
    "btd6_lookup": _btd6(TOOLSET_BTD6_REFERENCE),
    "btd6_list_roster": _btd6(TOOLSET_BTD6_REFERENCE),
    "btd6_capability_lookup": _btd6(TOOLSET_BTD6_REFERENCE),
    "btd6_map_lookup": _btd6(TOOLSET_BTD6_REFERENCE),
    "btd6_mode_lookup": _btd6(TOOLSET_BTD6_REFERENCE),
    "btd6_relic_lookup": _btd6(TOOLSET_BTD6_REFERENCE),
    "btd6_power_lookup": _btd6(TOOLSET_BTD6_REFERENCE),
    "btd6_power_effect": _btd6(TOOLSET_BTD6_REFERENCE),
    "btd6_buff_uptime": _btd6(TOOLSET_BTD6_REFERENCE),
    "btd6_monkey_knowledge_lookup": _btd6(TOOLSET_BTD6_REFERENCE),
    "btd6_geraldo_lookup": _btd6(TOOLSET_BTD6_REFERENCE),
    "btd6_boss_lookup": _btd6(TOOLSET_BTD6_REFERENCE),
    # --- BTD6 round questions / range aggregation ---
    "btd6_round_composition": _btd6(TOOLSET_BTD6_ROUNDS),
    "btd6_round_cash": _btd6(TOOLSET_BTD6_ROUNDS, TOOLSET_BTD6_COSTS),
    "btd6_bloon_filter": _btd6(TOOLSET_BTD6_REFERENCE, TOOLSET_BTD6_ROUNDS),
    # --- BTD6 cost / economy calculators ---
    "btd6_difficulty_cost": _btd6(TOOLSET_BTD6_COSTS),
    "btd6_cumulative_cost": _btd6(TOOLSET_BTD6_COSTS),
    "btd6_superlative_lookup": _btd6(TOOLSET_BTD6_REFERENCE, TOOLSET_BTD6_COSTS),
    # --- BTD6 paragon calculators (derived numbers) ---
    "btd6_paragon_calculate": _btd6(TOOLSET_BTD6_PARAGON, cost_class="normal"),
    "btd6_paragon_requirements": _btd6(TOOLSET_BTD6_PARAGON),
    "btd6_paragon_stats_at_degree": _btd6(TOOLSET_BTD6_PARAGON, cost_class="normal"),
    # --- BTD6 live (Ninja Kiwi-backed) ---
    "btd6_ct_team_status": _btd6(
        TOOLSET_BTD6_LIVE,
        freshness="live",
        cost_class="normal",
    ),
    # --- Server context (live Discord/runtime state; never a BTD6 grounding fact) ---
    "get_user_standing": _server(TOOLSET_SERVER_CONTEXT_BASIC),
    "get_server_time": _server(TOOLSET_SERVER_CONTEXT_BASIC),
    "get_server_overview": _server(TOOLSET_SERVER_CONTEXT_BASIC),
    "list_server_roles": _server(TOOLSET_SERVER_CONTEXT_BASIC),
    "list_server_channels": _server(TOOLSET_SERVER_CONTEXT_BASIC),
    "lookup_member": _server(TOOLSET_SERVER_CONTEXT_SENSITIVE),
    "list_all_members": _server(TOOLSET_SERVER_CONTEXT_SENSITIVE),
    "get_guild_ai_config": _server(TOOLSET_SERVER_CONTEXT_SENSITIVE),
    "recent_audit": _server(TOOLSET_SERVER_CONTEXT_SENSITIVE),
    "diagnostics_health_snapshot": _server(TOOLSET_DIAGNOSTICS),
    # --- Self-awareness / introspection (answerability Phase 3, Q-0047) ---
    # Read-only, audience-tiered-at-construction views over
    # ``services.ai_introspection_service``. ``btd6_answerability`` carries the
    # btd6 grounding domain (and so the ``btd6_`` name prefix the grounding
    # invariant demands): the fixture counts / versions it reports must be able
    # to ground a BTD6 answer, or the faithfulness number-guard would block the
    # very replies the tool exists to serve. The catalog/policy tools are meta
    # views, never BTD6 facts.
    "get_ai_tool_catalog": AIToolMetadata(
        toolsets=frozenset({TOOLSET_SELF_AWARENESS}),
    ),
    "get_ai_policy_explanation": AIToolMetadata(
        toolsets=frozenset({TOOLSET_SELF_AWARENESS}),
        freshness="live",
    ),
    "btd6_answerability": _btd6(TOOLSET_SELF_AWARENESS, TOOLSET_BTD6_REFERENCE),
    # --- Support tickets (the one write-capable / action tool) ---
    "open_support_ticket": AIToolMetadata(
        toolsets=frozenset({TOOLSET_TICKET}),
        freshness="live",
    ),
}


def known_toolsets() -> frozenset[str]:
    """Every toolset name any catalogue entry declares membership in."""
    return frozenset(ts for meta in CATALOGUE.values() for ts in meta.toolsets)


def grounding_tool_names(domain: str = "btd6") -> frozenset[str]:
    """Tools whose results may ground a ``domain`` answer (join the faithfulness ledger).

    Derived from ``grounding_domain`` metadata — the single source of truth that replaces
    the hand-maintained ``ai_tools.BTD6_GROUNDING_TOOL_NAMES`` frozenset, so the allowlist
    can no longer silently drift from the registered tool set.
    """
    return frozenset(
        name for name, meta in CATALOGUE.items() if meta.grounding_domain == domain
    )


# --- Deterministic selection (plan §5.3-5.4) --------------------------------


@dataclass(frozen=True)
class ToolDecision:
    """Why one candidate tool was offered or withheld for a request.

    Deterministic and inspectable (the model never chooses what it may see). The set of
    ``included`` decisions is exactly the offered toolset; the excluded ones carry a stable
    :class:`ToolExclusionReason` for an effective-policy preview / dry run.
    """

    name: str
    included: bool
    reason: ToolExclusionReason | None = None


def select_tools(
    candidates: Sequence[AIToolSpec],
    *,
    scope: AIScope,
    enabled_toolsets: Collection[str] | None = None,
    disabled_tools: Collection[str] | None = None,
    catalogue: Mapping[str, AIToolMetadata] | None = None,
) -> list[ToolDecision]:
    """Decide which ``candidates`` to offer, in catalogue precedence order.

    Precedence (authority first; policy may only narrow):

    1. ``scope_denied`` — caller's :class:`AIScope` is below the tool's ``min_scope``.
    2. ``explicitly_disabled`` — the tool name is in ``disabled_tools`` (explicit disable
       wins over an enabling toolset).
    3. ``toolset_disabled`` — ``enabled_toolsets`` is set and the tool shares no toolset
       with it.

    With ``enabled_toolsets=None`` **and** ``disabled_tools=None`` the only filter is scope
    — i.e. the historical ``build_registry`` behaviour, unchanged. ``candidates`` is the
    runtime-assembled list (so guild/feature availability is already reflected by which
    specs are present; this function does not re-derive ``runtime_unavailable``).
    """
    cat = catalogue if catalogue is not None else CATALOGUE
    disabled = set(disabled_tools or ())
    enabled = set(enabled_toolsets) if enabled_toolsets is not None else None

    decisions: list[ToolDecision] = []
    for spec in candidates:
        reason = _exclusion_reason(
            spec,
            scope=scope,
            enabled=enabled,
            disabled=disabled,
            cat=cat,
        )
        decisions.append(ToolDecision(spec.name, reason is None, reason))
    return decisions


def _exclusion_reason(
    spec: AIToolSpec,
    *,
    scope: AIScope,
    enabled: set[str] | None,
    disabled: set[str],
    cat: Mapping[str, AIToolMetadata],
) -> ToolExclusionReason | None:
    """The reason ``spec`` is withheld, or ``None`` if it is offered (precedence order)."""
    if not scope_allows(scope, spec.min_scope):
        return ToolExclusionReason.SCOPE_DENIED
    if spec.name in disabled:
        return ToolExclusionReason.EXPLICITLY_DISABLED
    if enabled is not None:
        meta = cat.get(spec.name)
        tool_toolsets = meta.toolsets if meta is not None else frozenset()
        if enabled.isdisjoint(tool_toolsets):
            return ToolExclusionReason.TOOLSET_DISABLED
    return None
