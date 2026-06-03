"""M4 — btd6_grounding_service tests."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import AITask  # noqa: E402
from services import (  # noqa: E402
    btd6_data_service,
    btd6_grounding_service,
    btd6_knowledge_api,
)
from utils.btd6.paragon_math import PARAGONS  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_grounding_index():
    """Reset the verifier index + dataset cache around every case so a stale
    name index cannot leak across fixture changes (C4)."""
    btd6_grounding_service._reset_for_tests()
    btd6_data_service.reset_cache()
    yield
    btd6_grounding_service._reset_for_tests()
    btd6_data_service.reset_cache()


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


# ---------------------------------------------------------------------------
# validate_btd6_reply — the live answer-path faithfulness verifier
# ---------------------------------------------------------------------------


def test_btd6_reply_blocks_unsupported_number():
    v = btd6_grounding_service.validate_btd6_reply(
        "Round 40 sends 999 ceramics.",
        facts=("Round 40 sends 200 ceramics.",),
        task=AITask.BTD6_ANSWER,
    )
    assert v.grounded is False
    assert "999" in v.offending_numbers
    assert "numeric_claim_unsupported" in v.notes


def test_btd6_reply_accepts_supported_number():
    v = btd6_grounding_service.validate_btd6_reply(
        "Round 40 sends 200 ceramics.",
        facts=("Round 40 sends 200 ceramics.",),
        task=AITask.BTD6_ANSWER,
    )
    assert v.grounded is True


def test_btd6_reply_comma_formatted_number_still_grounded():
    # Grounding renders comma-formatted totals; the model may drop the comma.
    v = btd6_grounding_service.validate_btd6_reply(
        "The total RBE is 48210.",
        facts=("total RBE 48,210 (hits to fully clear)",),
        task=AITask.BTD6_ANSWER,
    )
    assert v.grounded is True


def test_btd6_reply_tool_computed_number_grounds_via_ledger():
    # A number present only in an approved tool result (the ledger) is trusted.
    v = btd6_grounding_service.validate_btd6_reply(
        "At degree 73 it deals 4521 damage.",
        facts=(),
        tool_results=('{"degree": 73, "damage": 4521}',),
        task=AITask.BTD6_ANSWER,
    )
    assert v.grounded is True


def test_btd6_reply_unrelated_number_does_not_whitelist():
    # An unrelated number (e.g. a member count) must not ground a BTD6 claim.
    v = btd6_grounding_service.validate_btd6_reply(
        "The paragon costs 235000.",
        facts=(),
        tool_results=('{"members": 235}',),
        task=AITask.BTD6_ANSWER,
    )
    assert v.grounded is False
    assert "235000" in v.offending_numbers


def test_btd6_reply_blocks_ungrounded_hero_names():
    v = btd6_grounding_service.validate_btd6_reply(
        "BTD6 has five heroes: Quincy, Gwen, Obyn, Geraldo, Adora.",
        facts=(),
        task=AITask.BTD6_ANSWER,
    )
    assert v.grounded is False
    assert "entity_name_unsupported" in v.notes
    assert "quincy" in v.offending_names


def test_btd6_reply_accepts_grounded_hero_name():
    v = btd6_grounding_service.validate_btd6_reply(
        "Quincy is a starter hero.",
        facts=("Quincy is a hero available from the start.",),
        task=AITask.BTD6_ANSWER,
    )
    assert v.grounded is True


def test_btd6_reply_blocks_ungrounded_upgrade_name():
    # "Sharp Shots" is a real Dart Monkey upgrade — indexed, and ungrounded
    # here because it is not in the (empty) payload.
    v = btd6_grounding_service.validate_btd6_reply(
        "Just buy Sharp Shots first.",
        facts=(),
        task=AITask.BTD6_ANSWER,
    )
    assert v.grounded is False
    assert "sharp shots" in v.offending_names


def test_general_path_skips_number_check_but_guards_names():
    # On the general path ordinary numbers are never grounded …
    v = btd6_grounding_service.validate_btd6_reply(
        "There are 7 continents.",
        facts=(),
        task=AITask.GENERAL_NL_ANSWER,
    )
    assert v.grounded is True
    # … but a leaked BTD6 entity name is still blocked.
    v2 = btd6_grounding_service.validate_btd6_reply(
        "The Glaive Dominus is a paragon.",
        facts=(),
        task=AITask.GENERAL_NL_ANSWER,
    )
    assert v2.grounded is False
    assert "glaive dominus" in v2.offending_names


def test_general_path_should_verify_predicate():
    # Ordinary chat naming a hero must not trigger the guard.
    assert (
        btd6_grounding_service.general_path_should_verify(
            "who was benjamin franklin", "Benjamin Franklin was a polymath."
        )
        is False
    )
    # A distinctive multi-word paragon name triggers it without a keyword.
    assert (
        btd6_grounding_service.general_path_should_verify(
            "tell me", "The Apex Plasma Master costs 5000000."
        )
        is True
    )
    # A BTD6 context keyword triggers it.
    assert (
        btd6_grounding_service.general_path_should_verify(
            "which heroes exist?", "There are several."
        )
        is True
    )


def test_reset_clears_name_index(monkeypatch):
    # Build the index, then prove a dataset swap is reflected after reset
    # (no stale stats/name leak — C4).
    real = btd6_grounding_service._name_index()
    assert real.single  # populated from the real dataset

    fake = SimpleNamespace(
        data_version="t1",
        game_version="t",
        towers=(),
        heroes=(SimpleNamespace(canonical="Zztopkek", aliases=()),),
        maps=(),
        modes=(),
        bloons=(),
        ct_relics=(),
    )
    monkeypatch.setattr(btd6_data_service, "get_dataset", lambda: fake)
    btd6_grounding_service._reset_for_tests()

    rebuilt = btd6_grounding_service._name_index()
    assert "zztopkek" in rebuilt.single
    assert "quincy" not in rebuilt.single  # the old index did not leak through


def test_enumeration_roster_is_subset_of_accepted_names():
    # Deterministic paragon enumeration must never produce a name the verifier
    # would later reject (drift guard, C8).
    matchers = btd6_grounding_service._name_index()
    for paragon in PARAGONS:
        present = btd6_grounding_service.name_guard.names_present(
            paragon.name, matchers
        )
        assert present, f"paragon {paragon.name!r} is not in the accepted index"
