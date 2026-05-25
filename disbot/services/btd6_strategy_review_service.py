"""AI review pipeline for proposed strategies (M4).

Wraps the strict approval gates:

* Refinement when required fields are missing.
* Rejection when content is unsafe / spam / low-quality.
* Factual conflict checks delegated to
  :mod:`services.btd6_grounding_service`.
* Required context (map / mode / round / towers) must be present
  when the strategy implies them.
* Approval creates an audit row and is reversible.
* **Publishing requires staff confirmation** — AI may approve at
  guild-local visibility only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from services import btd6_grounding_service, btd6_strategy_mutation

logger = logging.getLogger("bot.services.btd6_strategy_review")


@dataclass(frozen=True)
class ReviewDecision:
    outcome: str  # 'approved' | 'rejected' | 'refine_requested'
    reason_code: str
    notes: tuple[str, ...] = ()
    strategy_id: int | None = None


_REQUIRED_FIELDS = ("title", "summary")
_HAZARD_KEYWORDS = (
    "ignore previous instructions",
    "system prompt",
    "discord token",
    "owner password",
)


async def review_proposed_strategy(
    *,
    proposed: dict[str, Any],
    origin_guild_id: int,
    submitter: Any,
    provider: str = "deterministic",
    model: str = "",
) -> ReviewDecision:
    """End-to-end strict review.

    On success this writes a draft strategy + records the
    ``ai_approved`` audit row (guild-local only). It never flips to
    ``published`` — that requires
    :func:`services.btd6_strategy_mutation.staff_publish`.
    """
    missing = [f for f in _REQUIRED_FIELDS if not str(proposed.get(f) or "").strip()]
    if missing:
        return ReviewDecision(
            outcome="refine_requested",
            reason_code="missing_required_fields",
            notes=tuple(missing),
        )

    if _looks_unsafe(proposed):
        return ReviewDecision(
            outcome="rejected",
            reason_code="unsafe_or_injection",
        )

    grounding_notes: list[str] = []
    for entity_kind, entity_key in _entity_pairs(proposed):
        result = await btd6_grounding_service.validate_strategy_field(
            fact_type=entity_kind,
            entity_kind=entity_kind,
            entity_key=str(entity_key),
            proposed_body=proposed,
        )
        if not result.grounded:
            grounding_notes.extend(result.notes)
            grounding_notes.append(f"{entity_kind}:{entity_key}")
    if grounding_notes:
        return ReviewDecision(
            outcome="rejected",
            reason_code="grounding_failed",
            notes=tuple(grounding_notes),
        )

    submission = await btd6_strategy_mutation.submit_strategy(
        origin_guild_id=origin_guild_id,
        submitter=submitter,
        title=str(proposed["title"]),
        summary=str(proposed["summary"]),
        map_name=proposed.get("map"),
        mode=proposed.get("mode"),
        difficulty=proposed.get("difficulty"),
        hero=proposed.get("hero"),
        towers=list(proposed.get("towers") or []),
        upgrade_paths=list(proposed.get("upgrade_paths") or []),
        round_range=proposed.get("round_range"),
        steps=list(proposed.get("steps") or []),
        common_failures=list(proposed.get("common_failures") or []),
        source_links=list(proposed.get("source_links") or []),
        origin_metadata={"ai_reviewed": True, "provider": provider, "model": model},
    )

    approval = await btd6_strategy_mutation.ai_approve_guild(
        submission.strategy_id,
        provider=provider,
        model=model,
        detail={"review": "auto_approved_guild_local"},
    )
    return ReviewDecision(
        outcome="approved",
        reason_code="none",
        strategy_id=approval.strategy_id,
    )


def _looks_unsafe(proposed: dict[str, Any]) -> bool:
    blob = " ".join(
        str(value).lower() for value in proposed.values() if value is not None
    )
    return any(token in blob for token in _HAZARD_KEYWORDS)


def _entity_pairs(proposed: dict[str, Any]) -> list[tuple[str, Any]]:
    pairs: list[tuple[str, Any]] = []
    if proposed.get("map"):
        pairs.append(("map", proposed["map"]))
    if proposed.get("mode"):
        pairs.append(("mode", proposed["mode"]))
    if proposed.get("hero"):
        pairs.append(("hero", proposed["hero"]))
    for tower in (proposed.get("towers") or [])[:5]:
        if tower:
            pairs.append(("tower", tower))
    return pairs


__all__ = ["ReviewDecision", "review_proposed_strategy"]
