"""Shared request/result types for the AI feature-facts gather step.

Lives here rather than in natural_language_stage.py to avoid that
module becoming a shared type owner (circular import risk).  Consumed
by natural_language_stage, youtube_context_service, and
response_renderer_registry.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.runtime.ai.contracts import AITask


@dataclass(frozen=True)
class FeatureFactRequest:
    task: AITask
    text: str
    guild_id: int | None
    channel_id: int | None
    author_id: int | None
    message_id: int | None
    # The router routed this turn to BTD6 via the conversation cue (a pronoun
    # follow-up) — the grounding layer then adds the carryover facts even when
    # the text itself grounds something (the "which of those can damage lead"
    # partial-grounding miss, 2026-06-11).
    conversation_followup: bool = False


@dataclass(frozen=True)
class FeatureFactsResult:
    facts: tuple[str, ...]
    render_context: object | None = None
    error_reason: str | None = None


__all__ = ["FeatureFactRequest", "FeatureFactsResult"]
