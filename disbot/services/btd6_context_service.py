"""BTD6 context owner for the central AI stage (M2).

The BTD6 cog's intent-resolution / confidence-threshold logic moves
here so it can be invoked by the central natural-language stage
when the task router classifies a message as
:attr:`AITask.BTD6_ANSWER`. The cog itself no longer owns the
question/answer pipeline.

M2 ships a minimal context surface — facts come from the existing
``services.btd6_ai_service`` fixture provider. M3A swaps that out
for :class:`BTD6KnowledgeAPI`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("bot.services.btd6_context")


@dataclass(frozen=True)
class BTD6Context:
    """Retrieved facts ready for the instruction stack."""

    facts: tuple[str, ...]
    source_summary: str
    confidence: float


async def build(message_text: str) -> BTD6Context:
    """Build a BTD6 context bundle for ``message_text``.

    M2 reuses :mod:`services.btd6_resolver_service` (entity intent)
    + :mod:`services.btd6_ai_service` (facts) so deterministic
    fallback continues to work end-to-end. The bundle is wrapped as
    untrusted data by the instruction service before reaching the
    gateway, so anything in ``facts`` is treated as data not
    instructions even though it came from a Tier-1 source.
    """
    facts: list[str] = []
    source_summary = "fixture (M3A wires real BTD6KnowledgeAPI)"
    confidence = 0.0
    try:
        from services import btd6_resolver_service

        intent = btd6_resolver_service.resolve(message_text)
        confidence = float(getattr(intent, "confidence", 0.0) or 0.0)
        summary = getattr(intent, "summary", None)
        if summary:
            facts.append(str(summary))
    except Exception as exc:  # noqa: BLE001 — defensive
        logger.debug("btd6_context_service: resolver unavailable (%s)", exc)

    return BTD6Context(
        facts=tuple(facts),
        source_summary=source_summary,
        confidence=confidence,
    )


__all__ = ["BTD6Context", "build"]
