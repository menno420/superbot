"""Assemble the per-request :class:`AIRequestContext` payload.

A thin helper so the natural-language stage doesn't have to know
where each piece of metadata comes from. Reads from the discord
:class:`Message` plus the policy snapshot the resolver returned.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.runtime.ai.contracts import AIRequestContext, AIScope, AITask


@dataclass(frozen=True)
class BuiltContext:
    request_context: AIRequestContext
    correlation_id: str


def build(
    *,
    task: AITask,
    guild_id: int,
    actor_id: int,
    channel_id: int,
    correlation_id: str,
    scope: AIScope = AIScope.USER,
    source: str = "natural_language_stage",
) -> BuiltContext:
    ctx = AIRequestContext(
        task=task,
        scope=scope,
        guild_id=guild_id,
        actor_id=actor_id,
        channel_id=channel_id,
        correlation_id=correlation_id,
        source=source,
    )
    return BuiltContext(request_context=ctx, correlation_id=correlation_id)


__all__ = ["BuiltContext", "build"]
