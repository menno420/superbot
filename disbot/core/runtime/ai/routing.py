"""Task → (provider, model, timeout) resolution.

Routing keeps provider/model decisions out of the gateway core so
the gateway stays focused on safety, redaction, and fault handling.
Each :class:`AITask` resolves to a typed :class:`RoutingTarget`.

Resolution order:

1. Explicit override stored via :func:`override` (test seam; cleared
   by :func:`clear_overrides`).
2. Per-task env var: ``AI_ROUTING_<TASK_NAME>=<provider>:<model>``.
3. Default registry built from :func:`feature_flags.ai_default_provider`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from core.runtime.ai.contracts import AITask
from core.runtime.ai.feature_flags import ai_default_provider

DEFAULT_TIMEOUT_SECONDS = 20.0

# Default per-task model. Kept conservative; operators can override
# via env var or :func:`override` without code change. The setup
# advisor used gpt-4o-mini historically; that's the safe default.
_DEFAULT_MODELS: dict[AITask, str] = {
    AITask.SETUP_SUGGEST: "gpt-4o-mini",
    AITask.SETUP_EXPLAIN: "gpt-4o-mini",
    AITask.PLATFORM_EXPLAIN_STATUS: "gpt-4o-mini",
    AITask.PLATFORM_EXPLAIN_CONSISTENCY: "gpt-4o-mini",
    AITask.LOGS_TRIAGE: "gpt-4o-mini",
    AITask.SETTINGS_EXPLAIN: "gpt-4o-mini",
    AITask.SETTINGS_PROPOSE: "gpt-4o-mini",
    AITask.HELP_ANSWER: "gpt-4o-mini",
    AITask.CODE_CONTEXT_EXPLAIN: "gpt-4o-mini",
    AITask.MODERATION_ASSIST: "gpt-4o-mini",
    AITask.VIDEO_DESCRIBE: "gpt-4o-mini",
    AITask.VIDEO_COMPARE: "gpt-4o-mini",
    AITask.VIDEO_QA: "gpt-4o-mini",
}


@dataclass(frozen=True)
class RoutingTarget:
    """Resolved provider + model + timeout for a single AI call."""

    provider: str
    model: str
    timeout_seconds: float


_OVERRIDES: dict[AITask, RoutingTarget] = {}


def override(task: AITask, target: RoutingTarget) -> None:
    """Install a routing override; primarily a test seam.

    Production code does not call this; tests use it to direct a
    task at a fake provider without touching env vars.
    """
    _OVERRIDES[task] = target


def clear_overrides() -> None:
    """Reset every routing override; restores env/default resolution."""
    _OVERRIDES.clear()


# Default per-task Claude model when the resolved provider is Anthropic.
# Reasoning-heavier tasks → Sonnet; lighter explain / answer tasks → Haiku.
_ANTHROPIC_DEFAULT_MODELS: dict[AITask, str] = {
    AITask.SETUP_SUGGEST: "claude-sonnet-4-6",
    AITask.SETTINGS_PROPOSE: "claude-sonnet-4-6",
    AITask.LOGS_TRIAGE: "claude-sonnet-4-6",
    AITask.CODE_CONTEXT_EXPLAIN: "claude-sonnet-4-6",
    AITask.MODERATION_ASSIST: "claude-sonnet-4-6",
    AITask.BTD6_ANSWER: "claude-sonnet-4-6",
    AITask.BTD6_STRATEGY_REVIEW: "claude-sonnet-4-6",
    AITask.GENERAL_NL_ANSWER: "claude-sonnet-4-6",
    AITask.SETUP_EXPLAIN: "claude-haiku-4-5",
    AITask.SETTINGS_EXPLAIN: "claude-haiku-4-5",
    AITask.PLATFORM_EXPLAIN_STATUS: "claude-haiku-4-5",
    AITask.PLATFORM_EXPLAIN_CONSISTENCY: "claude-haiku-4-5",
    AITask.HELP_ANSWER: "claude-haiku-4-5",
    AITask.VIDEO_DESCRIBE: "claude-haiku-4-5",
    AITask.VIDEO_COMPARE: "claude-haiku-4-5",
    AITask.VIDEO_QA: "claude-haiku-4-5",
}

_OPENAI_FALLBACK_MODEL = "gpt-4o-mini"
_ANTHROPIC_FALLBACK_MODEL = "claude-sonnet-4-6"


def default_model_for(provider: str, task: AITask) -> str:
    """Return the default model for ``task`` under ``provider``.

    Lets an operator switch provider (via env or guild policy) without
    also supplying a model: the right vendor-specific default is chosen so
    an OpenAI model string never reaches Anthropic, or vice versa.
    """
    if provider == "anthropic":
        return _ANTHROPIC_DEFAULT_MODELS.get(task, _ANTHROPIC_FALLBACK_MODEL)
    return _DEFAULT_MODELS.get(task, _OPENAI_FALLBACK_MODEL)


def resolve(task: AITask) -> RoutingTarget:
    """Resolve the provider, model, and timeout for ``task``."""
    if task in _OVERRIDES:
        return _OVERRIDES[task]

    env_name = f"AI_ROUTING_{task.name}"
    env_value = os.getenv(env_name, "").strip()
    if env_value:
        provider, _, model = env_value.partition(":")
        if provider:
            provider = provider.strip().lower()
            return RoutingTarget(
                provider=provider,
                model=(model.strip() or default_model_for(provider, task)),
                timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
            )

    provider = ai_default_provider()
    return RoutingTarget(
        provider=provider,
        model=default_model_for(provider, task),
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
