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


# --- #655 answerability item 5: bloon branch + facts-led fallback ------------


def test_bloon_intent_yields_bloon_answer():
    # The resolver matched bloons all along; deterministic_answer had no
    # branch for them, so this fell through to the unresolved refusal.
    intent = resolve("what does a ceramic bloon pop into")
    response = deterministic_answer(intent)
    assert "Ceramic Bloon" in response.title
    assert response.confidence == "high"
    assert any("Pops into" in opt for opt in response.recommended_options)


def test_round_still_wins_over_bloon():
    # Precedence: "ceramic rush on round 63" is a round question.
    intent = resolve("ceramic rush on round 63")
    response = deterministic_answer(intent)
    assert "Round 63" in response.title


@pytest.mark.asyncio
async def test_unresolved_with_grounding_facts_leads_with_facts():
    # Powers / MK / bosses have no resolver intent — the shared grounding
    # pipeline answers, and the response must lead with those facts instead
    # of a "couldn't find anything" headline.
    response = await answer_question("what does the more cash monkey knowledge do")
    assert response.title == "BTD6 reference"
    assert "More Cash" in response.short_answer
    assert response.live_facts
    assert response.confidence == "medium"


@pytest.mark.asyncio
async def test_unresolved_without_facts_keeps_refusal():
    response = await answer_question("anyway, hello there friend")
    assert response.confidence == "low"
    assert "couldn" in response.short_answer.lower()
