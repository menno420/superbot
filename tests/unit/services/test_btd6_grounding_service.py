"""M4 — btd6_grounding_service tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_grounding_service, btd6_knowledge_api  # noqa: E402


async def test_validate_answer_accepts_supported_numeric_claims():
    facts = [{"body": "Round 40 sends 200 ceramics.", "entity_key": "round_40",
              "confidence": 1.0}]
    result = await btd6_grounding_service.validate_answer(
        "Round 40 sends 200 ceramics.", context_facts=facts,
    )
    assert result.grounded is True
    assert result.reason_code == "none"
    assert result.used_fact_keys == ("round_40",)


async def test_validate_answer_rejects_unsupported_number():
    facts = [{"body": "Round 40 sends 200 ceramics.", "entity_key": "round_40",
              "confidence": 1.0}]
    result = await btd6_grounding_service.validate_answer(
        "Round 40 sends 999 ceramics.", context_facts=facts,
    )
    assert result.grounded is False
    assert result.reason_code == "grounding_failed"


async def test_validate_strategy_field_uses_knowledge_api(monkeypatch):
    async def _stub_get_map(name):
        # Build a minimal FactBundle-shaped object.
        from services.btd6_knowledge_api import FactBundle

        return FactBundle(
            fact_type="map", entity_kind="map", entity_key=name,
            body={"difficulty": "Beginner", "rounds": 100},
            source_key="nk_btd6_maps", source_trust_tier=1,
            source_url="https://example.test/btd6/maps",
            game_version=None, fetched_at=None, validated_at=None,
            freshness_status="fresh", confidence=1.0,
        )

    monkeypatch.setattr(btd6_knowledge_api, "get_map", _stub_get_map)
    result = await btd6_grounding_service.validate_strategy_field(
        fact_type="map", entity_kind="map", entity_key="monkey_meadow",
        proposed_body={"difficulty": "Beginner", "rounds": 100},
    )
    assert result.grounded is True


async def test_validate_strategy_field_rejects_when_entity_unknown(monkeypatch):
    async def _none(*a, **kw):
        return None

    monkeypatch.setattr(btd6_knowledge_api, "get_map", _none)
    result = await btd6_grounding_service.validate_strategy_field(
        fact_type="map", entity_kind="map", entity_key="not_a_map",
        proposed_body={"x": 1},
    )
    assert result.grounded is False
    assert "entity_not_in_knowledge_api" in result.notes
