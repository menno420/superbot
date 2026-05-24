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


def resolve(task: AITask) -> RoutingTarget:
    """Resolve the provider, model, and timeout for ``task``."""
    if task in _OVERRIDES:
        return _OVERRIDES[task]

    env_name = f"AI_ROUTING_{task.name}"
    env_value = os.getenv(env_name, "").strip()
    if env_value:
        provider, _, model = env_value.partition(":")
        if provider:
            return RoutingTarget(
                provider=provider.strip().lower(),
                model=(model.strip() or _DEFAULT_MODELS.get(task, "gpt-4o-mini")),
                timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
            )

    return RoutingTarget(
        provider=ai_default_provider(),
        model=_DEFAULT_MODELS.get(task, "gpt-4o-mini"),
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
