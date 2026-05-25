"""Single owner for BTD6 factual grounding (M4).

Two consumers ask through this module:

* The natural-language stage's answer renderer (validates AI
  output before it reaches the user).
* :mod:`services.btd6_strategy_review_service` (validates a
  proposed strategy field against retrieved facts).

Centralising the grounding check means the prompt-injection +
grounding pin tests have one place to extend, and ensures AI
output paths cannot fabricate stats by going around the validator.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from core.runtime.ai.contracts import PolicyDenialReason
from core.runtime.ai.safety import claims_are_grounded
from services import btd6_knowledge_api

logger = logging.getLogger("bot.services.btd6_grounding")


@dataclass(frozen=True)
class GroundingResult:
    grounded: bool
    reason_code: str  # 'none' or a PolicyDenialReason value
    used_fact_keys: tuple[str, ...]
    notes: tuple[str, ...] = ()


async def validate_answer(
    answer_text: str,
    *,
    context_facts: list[dict[str, Any]] | None = None,
    minimum_confidence: float = 0.5,
) -> GroundingResult:
    """Verify that every numeric claim in ``answer_text`` is supported.

    ``context_facts`` is a list of :class:`btd6_knowledge_api.FactBundle`
    bodies (already retrieved) so the validator does not need to
    re-fetch. If the bundle is empty the validator returns
    ``GROUNDING_FAILED`` unless the answer is purely textual.
    """
    haystack_pieces: list[str] = []
    used_keys: list[str] = []
    if context_facts:
        for fact in context_facts:
            body = fact.get("body") if isinstance(fact, dict) else getattr(
                fact, "body", None,
            )
            if body:
                haystack_pieces.append(str(body))
            key = fact.get("entity_key") if isinstance(fact, dict) else getattr(
                fact, "entity_key", None,
            )
            confidence = (
                fact.get("confidence") if isinstance(fact, dict)
                else getattr(fact, "confidence", 1.0)
            )
            if key and (confidence is None or float(confidence) >= minimum_confidence):
                used_keys.append(str(key))

    if claims_are_grounded(answer_text, allowed_facts=haystack_pieces):
        return GroundingResult(
            grounded=True,
            reason_code=PolicyDenialReason.NONE.value,
            used_fact_keys=tuple(used_keys),
        )
    return GroundingResult(
        grounded=False,
        reason_code=PolicyDenialReason.GROUNDING_FAILED.value,
        used_fact_keys=tuple(used_keys),
        notes=("numeric_claim_unsupported",),
    )


async def validate_strategy_field(
    *,
    fact_type: str,
    entity_kind: str,
    entity_key: str,
    proposed_body: dict[str, Any],
) -> GroundingResult:
    """Verify a single strategy field against the BTD6 KnowledgeAPI."""
    bundle = await btd6_knowledge_api.get_tower(entity_key) if entity_kind == "tower" else None
    if entity_kind == "hero":
        bundle = await btd6_knowledge_api.get_hero(entity_key)
    elif entity_kind == "map":
        bundle = await btd6_knowledge_api.get_map(entity_key)
    elif entity_kind == "mode":
        bundle = await btd6_knowledge_api.get_mode(entity_key)
    elif entity_kind == "round":
        try:
            bundle = await btd6_knowledge_api.get_round(int(entity_key))
        except (TypeError, ValueError):
            bundle = None

    if bundle is None:
        return GroundingResult(
            grounded=False,
            reason_code=PolicyDenialReason.GROUNDING_FAILED.value,
            used_fact_keys=(),
            notes=("entity_not_in_knowledge_api",),
        )

    canonical = bundle.body if hasattr(bundle, "body") else bundle.get("body", {})
    haystack = str(canonical)
    if claims_are_grounded(str(proposed_body), allowed_facts=[haystack]):
        return GroundingResult(
            grounded=True,
            reason_code=PolicyDenialReason.NONE.value,
            used_fact_keys=(str(entity_key),),
        )
    return GroundingResult(
        grounded=False,
        reason_code=PolicyDenialReason.GROUNDING_FAILED.value,
        used_fact_keys=(str(entity_key),),
        notes=("strategy_field_unsupported_by_facts",),
    )


__all__ = ["GroundingResult", "validate_answer", "validate_strategy_field"]
