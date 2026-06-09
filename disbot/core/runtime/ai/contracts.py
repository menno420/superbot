"""Provider-neutral AI contracts for future SuperBot AI services.

Inert scaffold: these types are not imported by existing runtime code yet.
They define the shared language future services should use so setup,
diagnostics, log triage, settings help, and command help do not invent
parallel request/response shapes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class AITask(str, Enum):
    """Stable task identifiers for metrics, policy, and diagnostics."""

    SETUP_SUGGEST = "setup.suggest"
    SETUP_EXPLAIN = "setup.explain"
    PLATFORM_EXPLAIN_STATUS = "platform.explain_status"
    PLATFORM_EXPLAIN_CONSISTENCY = "platform.explain_consistency"
    LOGS_TRIAGE = "logs.triage"
    SETTINGS_EXPLAIN = "settings.explain"
    SETTINGS_PROPOSE = "settings.propose"
    HELP_ANSWER = "help.answer"
    CODE_CONTEXT_EXPLAIN = "code_context.explain"
    MODERATION_ASSIST = "moderation.assist"
    # M2 — central natural-language orchestrator routes per task.
    BTD6_ANSWER = "btd6.answer"
    GENERAL_NL_ANSWER = "general.nl_answer"
    # M4 — strategy submission review (AI extracts + validates;
    # publishing requires staff confirmation).
    BTD6_STRATEGY_REVIEW = "btd6.strategy_review"
    # M5 — YouTube video context tasks (URL-driven; feature-flag gated).
    VIDEO_DESCRIBE = "video.describe"
    VIDEO_COMPARE = "video.compare"
    VIDEO_QA = "video.qa"


class PolicyDenialReason(str, Enum):
    """Stable reason codes recorded on every ai_decision_audit row.

    Success rows (``decision IN ('allowed','replied')``) use the
    sentinel ``NONE``; denial rows pick the specific cause. Every
    code in this enum is safe to expose in admin diagnostics.
    """

    NONE = "none"
    AI_GLOBALLY_DISABLED = "ai_globally_disabled"
    AI_NL_DISABLED_FOR_GUILD = "ai_nl_disabled_for_guild"
    CHANNEL_DISABLED = "channel_disabled"
    CATEGORY_DISABLED = "category_disabled"
    ROLE_DENIED = "role_denied"
    BELOW_MIN_LEVEL = "below_min_level"
    COOLDOWN_ACTIVE = "cooldown_active"
    NO_MENTION_REQUIRED = "no_mention_required"
    NOT_A_QUESTION = "not_a_question"
    NO_ROUTE_MATCHED = "no_route_matched"
    EMPTY_MESSAGE = "empty_message"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    GROUNDING_FAILED = "grounding_failed"
    GUILD_NOT_CONFIGURED = "guild_not_configured"


class AIScope(str, Enum):
    """Where an AI request is allowed to operate."""

    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SERVER_OWNER = "server_owner"
    PLATFORM_OWNER = "platform_owner"
    SYSTEM = "system"


class AIResponseMode(str, Enum):
    """Expected response shape."""

    TEXT = "text"
    JSON = "json"
    SUGGESTIONS = "suggestions"


class AISuggestionKind(str, Enum):
    """Kinds of advisory suggestions AI services may produce."""

    EXPLANATION = "explanation"
    SETTING_CHANGE = "setting_change"
    BINDING_CHANGE = "binding_change"
    RESOURCE_PROVISION = "resource_provision"
    DIAGNOSTIC_NEXT_STEP = "diagnostic_next_step"
    HELP_NAVIGATION = "help_navigation"
    MODERATION_REVIEW = "moderation_review"


Confidence = Literal["high", "medium", "low"]
Severity = Literal["info", "warning", "error", "critical"]


@dataclass(frozen=True)
class AIRequestContext:
    """Low-risk metadata attached to an AI request.

    Do not store sensitive values here.  Provider keys, raw tokens, and
    private environment values belong outside the request payload.
    """

    task: AITask
    scope: AIScope
    guild_id: int | None = None
    actor_id: int | None = None
    channel_id: int | None = None
    correlation_id: str | None = None
    source: str = "unknown"


@dataclass(frozen=True)
class AIToolSpec:
    """Provider-neutral declaration of a read-only tool the model may call.

    Specs are pure data (no handler): they describe the tool to the
    provider so the model can decide to call it. The live handler is
    supplied separately to the gateway via ``tool_handlers`` so this
    contract stays a clean, redaction-safe data object. ``parameters``
    is a JSON-Schema object describing the tool's arguments.

    ``min_scope`` is the least-privileged :class:`AIScope` allowed to be
    offered this tool; the natural-language stage filters the offered
    toolset by the caller's scope before the request is built.
    """

    name: str
    description: str
    parameters: dict[str, Any]
    min_scope: AIScope = AIScope.USER


class ToolExclusionReason(str, Enum):
    """Stable, deterministic reason a tool was withheld from a request's offered set.

    Safe to surface in an effective-policy preview / dry run (no IDs, no arguments).
    Mirrors the orchestration selection precedence in the tool-orchestration plan
    (``docs/ai/ai-complex-request-tool-orchestration-plan.md`` §5.3). Authority
    (``scope_denied``) and runtime availability are checked first; toolset / explicit
    policy may only *narrow* the offered set, never widen it.
    """

    SCOPE_DENIED = "scope_denied"
    RUNTIME_UNAVAILABLE = "runtime_unavailable"
    TASK_MISMATCH = "task_mismatch"
    TOOLSET_DISABLED = "toolset_disabled"
    EXPLICITLY_DISABLED = "explicitly_disabled"
    BUDGET_DISALLOWED = "budget_disallowed"
    FRESHNESS_DISALLOWED = "freshness_disallowed"


class ToolRequirementMode(str, Enum):
    """How strongly the model must call a tool this turn (orchestration plan §4.2).

    Provider-neutral: each adapter maps these onto its own ``tool_choice`` semantics
    (``docs/ai/ai-complex-request-tool-orchestration-plan.md`` §8.2). ``REQUIRED_GROUP`` is a
    SuperBot rule, not a native provider feature — the resolver narrows the *offered* tools to
    the group and the adapter then uses "require any" over that narrowed set.
    """

    NONE = "none"  # no model-visible tools (single-shot answer)
    AUTO = "auto"  # model may call zero or more (the historical default)
    REQUIRED_ANY = "required_any"  # at least one offered tool
    REQUIRED_GROUP = "required_group"  # at least one tool from a pre-narrowed group
    REQUIRED_TOOL = "required_tool"  # force one named tool


@dataclass(frozen=True)
class AIToolChoice:
    """Provider-neutral tool-choice policy for one request.

    The default (``AUTO``) reproduces the historical behaviour exactly: tools, when present,
    are offered with automatic choice. ``tool_name`` is required for ``REQUIRED_TOOL`` and
    ``group_name`` labels a ``REQUIRED_GROUP`` (for traces); both are ignored otherwise.
    """

    mode: ToolRequirementMode = ToolRequirementMode.AUTO
    tool_name: str | None = None
    group_name: str | None = None


@dataclass(frozen=True)
class AIToolBudget:
    """Per-request bound on the model<->tool loop.

    The defaults are **compatibility-preserving**: ``max_hops`` mirrors the adapters'
    historical hop limit, and the remaining caps are ``None`` ("no limit"), so a request that
    does not set a budget behaves exactly as before (hop-bounded only). A policy may tighten
    any field; the adapters enforce them (orchestration plan §11.1).
    """

    max_hops: int = 4
    max_calls: int | None = None
    max_wall_seconds: float | None = None
    max_result_chars: int | None = None


@dataclass(frozen=True)
class AIToolMetadata:
    """Selection/UI metadata for one registered AI tool — the catalogue half of a
    tool, kept separate from its provider-facing :class:`AIToolSpec` (a clean data
    object the model sees) and its live runtime handler.

    This is the per-tool record the orchestration layer selects from. ``min_scope`` on
    the spec stays **authoritative** for authority: a toolset/disable policy may only
    *narrow* the offered set, never grant a tool above the caller's scope.

    Only ``toolsets`` and ``grounding_domain`` drive behaviour today (deterministic
    selection + deriving the BTD6 grounding allowlist). The remaining fields are the
    declared contract the later orchestration phases (budgets, preflight, task-affinity
    narrowing, answer/UI metadata) will consume; they carry conservative defaults until
    those phases wire and verify them.
    """

    toolsets: frozenset[str]
    task_affinity: frozenset[AITask] = frozenset()
    grounding_domain: str | None = None
    capability_tags: frozenset[str] = frozenset()
    cost_class: Literal["cheap", "normal", "expensive"] = "normal"
    freshness: Literal["static", "cached", "live"] = "static"
    parallel_safe: bool = True
    preflight_safe: bool = False
    result_contract: str = ""


@dataclass(frozen=True)
class AIRequest:
    """Provider-neutral request passed to a future AI gateway."""

    context: AIRequestContext
    system_prompt: str
    payload: dict[str, Any]
    mode: AIResponseMode = AIResponseMode.TEXT
    response_schema: dict[str, Any] | None = None
    max_output_tokens: int = 1500
    timeout_seconds: float = 20.0
    tools: tuple[AIToolSpec, ...] = ()
    # Orchestration policy (plan §8.1). Defaults reproduce the historical behaviour:
    # AUTO choice + hop-bounded loop with no call/wall/result caps. A resolver may set
    # a tighter policy; the provider adapters enforce it. They can only narrow, never
    # widen, what the scope-filtered ``tools`` already permit.
    tool_choice: AIToolChoice = AIToolChoice()
    tool_budget: AIToolBudget = AIToolBudget()


@dataclass(frozen=True)
class AISuggestion:
    """Advisory suggestion returned by an AI service.

    Suggestions must remain advisory until converted into typed operations
    and validated by the existing deterministic service layer.
    """

    kind: AISuggestionKind
    title: str
    summary: str
    confidence: Confidence = "medium"
    severity: Severity = "info"
    subsystem: str | None = None
    target: str | None = None
    proposed_value: Any | None = None
    next_command: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIResponse:
    """Provider-neutral response returned by a future AI gateway."""

    task: AITask
    provider: str
    model: str
    text: str | None = None
    data: dict[str, Any] | None = None
    suggestions: tuple[AISuggestion, ...] = ()
    latency_ms: float | None = None
    degraded: bool = False
    fallback_reason: str | None = None


@dataclass(frozen=True)
class AIDiagnosticsSnapshot:
    """Read-only snapshot for a future `!platform ai` surface."""

    provider_requested: str
    provider_active: str
    model: str
    enabled: bool
    redaction_enabled: bool
    degraded: bool = False
    last_error_type: str | None = None
    last_fallback_reason: str | None = None
    requests_observed: int = 0
    failures_observed: int = 0


__all__ = [
    "AIDiagnosticsSnapshot",
    "AIRequest",
    "AIRequestContext",
    "AIResponse",
    "AIResponseMode",
    "AIScope",
    "AISuggestion",
    "AISuggestionKind",
    "AITask",
    "AIToolBudget",
    "AIToolChoice",
    "AIToolSpec",
    "Confidence",
    "PolicyDenialReason",
    "Severity",
    "ToolRequirementMode",
]
