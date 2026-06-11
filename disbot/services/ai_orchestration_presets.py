"""Built-in AI tool-orchestration presets (Phase 3 — typed policy).

An *orchestration profile* answers the four orchestration questions for a
request (orchestration plan §4): which toolsets are offered, which tool (if any)
must be called, how much tool/loop budget may be spent, and which workflow/
answer-contract applies. It is deliberately separate from the natural-language
*reply* policy (mode / min_level / cooldown / instruction profile).

v1 ships **built-in presets only** (orchestration plan product-decision #6): a
scope stores just a profile *key*; the resolved components live here as code.
This keeps presets immutable through normal guild mutation paths and guarantees
they can only reference catalogue-approved toolsets (a drift test pins it).

Authority is never widened here. ``AIToolSpec.min_scope`` stays authoritative —
``services.ai_tool_catalogue.select_tools`` enforces it, so a preset that enables
``server_context_sensitive`` still offers a USER-scope caller nothing above their
scope. A preset only ever *narrows* what the scope already permits.

**Compatibility is the contract — with one deliberate, owner-driven
divergence.** The default key (:data:`DEFAULT_PROFILE_KEY`) reproduces the
pre-orchestration behaviour: every scope-allowed tool offered
(``enabled_toolsets=None``), automatic tool choice, and the historical
hop-bounded budget with no other caps. Any scope with no profile set resolves
to it, so migration 062 changed nothing on its own (orchestration plan §6.3).
Since 2026-06-11 the default (and ``balanced_helper``) also declare the
deterministic round-cash ``workflow`` — BUG-0001 recurred live on a
default-profile channel because the workflow that *can* answer round-cash
arithmetic was gated behind a profile nobody had set there, while the normal
path refuses such questions by design (the faithfulness guard correctly
blocks model arithmetic). The workflow is read-only and deterministic
(standing lift Q-0048) and engages only on conservatively-matched round-cash
questions, so every other default behaviour is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.runtime.ai.contracts import (
    AIToolBudget,
    AIToolChoice,
    ToolRequirementMode,
)
from services import ai_tool_catalogue as catalogue


@dataclass(frozen=True)
class OrchestrationProfile:
    """A named, immutable orchestration preset — the resolved tool policy.

    ``enabled_toolsets`` is the canonical-catalogue toolset filter: ``None``
    means "no restriction" (offer every scope-allowed tool, the historical
    behaviour); a tuple narrows the offered set to those toolset families; the
    empty tuple offers no tools at all. ``disabled_tools`` removes specific tool
    names regardless of toolset. ``tool_choice`` / ``tool_budget`` are the
    provider-neutral contracts the adapters already enforce (Phase 2).

    ``workflow`` selects the deterministic complex-request workflow for the
    scope: ``analyze_execute_verify`` engages the Phase 4 MVP round-cash
    plan→execute→verify workflow (:mod:`services.ai_round_cash_workflow`,
    Q-0046) for recognised round-cash questions; every other label carries no
    behaviour yet beyond being surfaced in the operator preview.
    ``answer_contract`` is still a declared label only — the workflow emits the
    one typed contract (``calculation_explained``) itself.
    """

    key: str
    label: str
    description: str
    enabled_toolsets: tuple[str, ...] | None
    disabled_tools: tuple[str, ...]
    tool_choice: AIToolChoice
    tool_budget: AIToolBudget
    workflow: str
    answer_contract: str


# The compatibility default: any scope with no orchestration profile resolves
# here, and it reproduces today's behaviour exactly.
DEFAULT_PROFILE_KEY = "compatible_default"

# The BTD6 factual toolsets a grounded preset narrows to. Kept as a module
# constant so the preset definitions and the drift test share one list.
_BTD6_FACTUAL_TOOLSETS: tuple[str, ...] = (
    catalogue.TOOLSET_BTD6_REFERENCE,
    catalogue.TOOLSET_BTD6_ROUNDS,
    catalogue.TOOLSET_BTD6_COSTS,
    catalogue.TOOLSET_BTD6_PARAGON,
)


_PRESETS: dict[str, OrchestrationProfile] = {
    DEFAULT_PROFILE_KEY: OrchestrationProfile(
        key=DEFAULT_PROFILE_KEY,
        label="Compatible (today's behaviour)",
        description=(
            "Offer every tool the caller's scope allows, with automatic tool "
            "choice and the historical hop-bounded budget. Recognised "
            "round-cash questions are answered by the deterministic workflow. "
            "The implicit default for any scope with no orchestration profile "
            "set."
        ),
        enabled_toolsets=None,
        disabled_tools=(),
        tool_choice=AIToolChoice(mode=ToolRequirementMode.AUTO),
        tool_budget=AIToolBudget(),
        workflow="analyze_execute_verify",
        answer_contract="concise_fact",
    ),
    "balanced_helper": OrchestrationProfile(
        key="balanced_helper",
        label="Balanced helper",
        description=(
            "General-purpose. Every scope-allowed tool is available with "
            "automatic choice, but the loop is capped (3 hops / 4 tool calls) "
            "to keep trivial questions cheap. Recognised round-cash questions "
            "are answered by the deterministic workflow."
        ),
        enabled_toolsets=None,
        disabled_tools=(),
        tool_choice=AIToolChoice(mode=ToolRequirementMode.AUTO),
        tool_budget=AIToolBudget(max_hops=3, max_calls=4),
        workflow="analyze_execute_verify",
        answer_contract="concise_fact",
    ),
    "btd6_grounded": OrchestrationProfile(
        key="btd6_grounded",
        label="BTD6 grounded",
        description=(
            "Offer only the BTD6 factual toolsets (reference, rounds, costs, "
            "paragon). Automatic choice — the model may answer a social turn "
            "directly without forcing a tool. Best for BTD6-focused channels."
        ),
        enabled_toolsets=_BTD6_FACTUAL_TOOLSETS,
        disabled_tools=(),
        tool_choice=AIToolChoice(mode=ToolRequirementMode.AUTO),
        tool_budget=AIToolBudget(max_hops=3, max_calls=4),
        workflow="analyze_execute_verify",
        answer_contract="concise_fact",
    ),
    "btd6_grounded_strict": OrchestrationProfile(
        key="btd6_grounded_strict",
        label="BTD6 grounded (strict)",
        description=(
            "Offer only the BTD6 factual toolsets AND require at least one of "
            "them before answering (a hard grounding guarantee). Until request-"
            "intent analysis lands (Phase 4) this forces a tool on every turn — "
            "use for dedicated BTD6 expert channels, not general chat."
        ),
        enabled_toolsets=_BTD6_FACTUAL_TOOLSETS,
        disabled_tools=(),
        tool_choice=AIToolChoice(
            mode=ToolRequirementMode.REQUIRED_GROUP,
            group_name="btd6_grounding",
        ),
        tool_budget=AIToolBudget(max_hops=3, max_calls=4),
        workflow="analyze_execute_verify",
        answer_contract="calculation_explained",
    ),
    "no_tools": OrchestrationProfile(
        key="no_tools",
        label="No tools (conversational)",
        description=(
            "Offer no tools at all — a single-shot conversational answer. The "
            "model must not claim live, current, or private facts. Useful for "
            "social channels or strict cost control."
        ),
        enabled_toolsets=(),
        disabled_tools=(),
        tool_choice=AIToolChoice(mode=ToolRequirementMode.NONE),
        tool_budget=AIToolBudget(),
        workflow="direct_answer",
        answer_contract="concise_fact",
    ),
}


def all_presets() -> tuple[OrchestrationProfile, ...]:
    """Every built-in preset, default first then the rest alphabetically."""
    rest = sorted(
        (p for k, p in _PRESETS.items() if k != DEFAULT_PROFILE_KEY),
        key=lambda p: p.key,
    )
    return (_PRESETS[DEFAULT_PROFILE_KEY], *rest)


def known_profile_keys() -> frozenset[str]:
    """The set of valid orchestration profile keys."""
    return frozenset(_PRESETS)


def is_known(key: str | None) -> bool:
    """True if ``key`` names a built-in preset. ``None`` is not a key."""
    return key in _PRESETS


def get(key: str | None) -> OrchestrationProfile | None:
    """Return the preset for ``key``, or ``None`` if unknown / ``None``."""
    if key is None:
        return None
    return _PRESETS.get(key)


def default() -> OrchestrationProfile:
    """The compatibility-default preset (today's behaviour)."""
    return _PRESETS[DEFAULT_PROFILE_KEY]


def resolve_or_default(key: str | None) -> OrchestrationProfile:
    """Return the preset for ``key``, falling back to the default.

    Defensive: a key persisted by an older build whose preset was later
    removed must not break resolution — it degrades to the compatible default
    rather than raising.
    """
    return _PRESETS.get(key or "", _PRESETS[DEFAULT_PROFILE_KEY])


def unknown_toolset_references(
    *,
    known_toolsets: frozenset[str] | None = None,
) -> dict[str, tuple[str, ...]]:
    """Return any preset → toolset names that are NOT in the catalogue.

    A non-empty result means a preset references a toolset that no catalogue
    tool declares membership in (drift). Exposed for the drift-guard test; the
    catalogue is the source of truth, so this stays self-maintaining.
    """
    known = known_toolsets if known_toolsets is not None else catalogue.known_toolsets()
    out: dict[str, tuple[str, ...]] = {}
    for profile in _PRESETS.values():
        if profile.enabled_toolsets is None:
            continue
        bad = tuple(ts for ts in profile.enabled_toolsets if ts not in known)
        if bad:
            out[profile.key] = bad
    return out


__all__ = [
    "DEFAULT_PROFILE_KEY",
    "OrchestrationProfile",
    "all_presets",
    "default",
    "get",
    "is_known",
    "known_profile_keys",
    "resolve_or_default",
    "unknown_toolset_references",
]
