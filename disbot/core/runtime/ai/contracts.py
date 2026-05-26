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
class AIRequest:
    """Provider-neutral request passed to a future AI gateway."""

    context: AIRequestContext
    system_prompt: str
    payload: dict[str, Any]
    mode: AIResponseMode = AIResponseMode.TEXT
    response_schema: dict[str, Any] | None = None
    max_output_tokens: int = 800
    timeout_seconds: float = 20.0


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
    "Confidence",
    "PolicyDenialReason",
    "Severity",
]
