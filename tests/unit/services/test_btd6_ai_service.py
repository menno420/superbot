"""BTD6 orchestrator tests — deterministic-only mode (Modules 3+4)."""

from __future__ import annotations

import pytest

from services.btd6_ai_service import answer_question, deterministic_answer
from services.btd6_resolver_service import resolve


def test_deterministic_answer_for_tower_intent():
    intent = resolve("Dart Monkey costs how much?")
    response = deterministic_answer(intent)
    assert "Dart Monkey" in response.title
    assert response.confidence == "high"
    assert response.sources  # at least one source label


def test_deterministic_answer_for_round_intent():
    intent = resolve("any tips for round 63?")
    response = deterministic_answer(intent)
    assert "Round 63" in response.title
    assert response.confidence == "high"


def test_unresolved_intent_yields_helpful_response():
    intent = resolve("anyway, hello there friend")
    response = deterministic_answer(intent)
    assert response.confidence == "low"
    assert "couldn" in response.short_answer.lower()


@pytest.mark.asyncio
async def test_answer_question_runs_without_ai_gateway():
    """Default path (no AI augmentation) must not call the gateway."""
    response = await answer_question("Sauda on round 28")
    assert "Sauda" in response.title


@pytest.mark.asyncio
async def test_augment_with_ai_falls_through_to_module_5_stub():
    """Module 3+4: augmentation is a no-op stub. Same shape returns."""
    base = await answer_question("Boomerang Monkey", augment_with_ai=False)
    augmented = await answer_question("Boomerang Monkey", augment_with_ai=True)
    assert augmented.title == base.title
    assert augmented.short_answer == base.short_answer
