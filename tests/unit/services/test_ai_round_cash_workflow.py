"""Round-cash plan→execute→verify workflow (orchestration Phase 4 MVP, Q-0046).

Deterministic coverage for every stage of the vertical slice: the conservative
question planner, execution against the real dataset (the Q-0043 inclusive
anchor: r50→r60 = $19,840), the verification gate (including a corrupted-owner
degrade), the afford-check composition, and the two render seams the
natural-language stage consumes (system block + faithfulness-ledger entry).

The model loop itself cannot be exercised here (no provider key in the
sandbox) — these tests pin everything deterministic; the live model pass is a
maintainer production check.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import ai_round_cash_workflow as wf  # noqa: E402
from services import btd6_data_service  # noqa: E402
from services.btd6_data_service import get_round  # noqa: E402


def _cumulative(n: int) -> float:
    entry = get_round(n)
    assert entry is not None and entry.cumulative_cash is not None
    return float(entry.cumulative_cash)


# ---------------------------------------------------------------------------
# Plan — the conservative recogniser
# ---------------------------------------------------------------------------


def test_plan_recognises_range_phrasings() -> None:
    cases = [
        "how much cash do I earn from round 50 to 60?",
        "cash from round 50 to round 60",
        "money earned rounds 50-60",
        "how much income between round 50 and 60",
        "cash earned from round 50 through 60",
    ]
    for text in cases:
        plan = wf.plan_question(text)
        assert plan is not None, text
        assert plan.intent == "range_cash", text
        assert (plan.round_start, plan.round_end) == (50, 60), text


def test_plan_recognises_afford_phrasings() -> None:
    plan = wf.plan_question("can I afford a $45,000 paragon by round 60?")
    assert plan is not None
    assert plan.intent == "afford_check"
    assert plan.round_start == 60
    assert plan.target_cost == 45_000.0

    plan = wf.plan_question("could we afford 12k at round 35")
    assert plan is not None
    assert plan.target_cost == 12_000.0
    assert plan.round_start == 35

    plan = wf.plan_question("afford 850 on round 12?")
    assert plan is not None
    assert plan.target_cost == 850.0


def test_plan_stays_out_of_ambiguous_or_unrelated_text() -> None:
    cases = [
        "",
        "hi",
        "what bloons come in rounds 40 to 60?",  # no cash keyword
        "how much does a dart monkey cost?",  # no round range
        "can I afford a banana farm at round 30",  # afford but no amount
        "can I afford 2 farms at round 30",  # 1-digit bare number is not a cost
        "how much cash do I have?",  # cash but no range
    ]
    for text in cases:
        assert wf.plan_question(text) is None, text


def test_plan_afford_without_anchor_falls_through_to_range() -> None:
    plan = wf.plan_question(
        "I want to afford the upgrade — how much cash from round 50 to 60?",
    )
    assert plan is not None
    assert plan.intent == "range_cash"
    assert (plan.round_start, plan.round_end) == (50, 60)


# ---------------------------------------------------------------------------
# Execute + verify — against the real dataset
# ---------------------------------------------------------------------------


def test_range_answer_pins_the_q0043_inclusive_anchor() -> None:
    answer = wf.run("how much cash from round 50 to 60?")
    assert answer is not None
    assert answer.status == "complete"
    assert answer.contract == wf.ANSWER_CONTRACT == "calculation_explained"
    assert answer.workflow == wf.WORKFLOW_KEY == "analyze_execute_verify"
    assert answer.intent == "range_cash"
    # Q-0043: INCLUSIVE of both endpoints — the canonical $19,840 anchor.
    assert answer.inclusive_range is True
    (evidence,) = answer.evidence
    assert evidence.outputs["range_cash"] == 19_840.0
    assert evidence.outputs["inclusive"] is True
    assert evidence.outputs["rounds_counted"] == 11
    assert evidence.calculator == "btd6_data_service.round_cash"
    assert evidence.calculator_version == wf.CALCULATOR_VERSION
    assert evidence.normalized_inputs == {"round_start": 50, "round_end": 60}
    assert evidence.data_version  # stamped from the dataset
    assert "$19,840.00" in answer.result_text
    assert "inclusive" in answer.result_text
    # The Q-0043 semantics ride the contract explicitly.
    assert any("Q-0043" in a for a in answer.assumptions)


def test_range_answer_single_round_collapse() -> None:
    answer = wf.run("cash from round 50 to 50?")
    assert answer is not None
    assert answer.status == "complete"
    (evidence,) = answer.evidence
    entry = get_round(50)
    assert entry is not None
    assert evidence.outputs["round_cash"] == float(entry.cash)
    assert evidence.outputs["cumulative_cash"] == float(entry.cumulative_cash)


def test_afford_check_compares_against_cumulative() -> None:
    cumulative_60 = _cumulative(60)

    yes = wf.run(f"can I afford ${cumulative_60 - 100:,.0f} by round 60?")
    assert yes is not None and yes.status == "complete"
    assert yes.intent == "afford_check"
    (evidence,) = yes.evidence
    assert evidence.outputs["affordable"] is True
    assert evidence.outputs["cumulative_cash"] == cumulative_60
    assert yes.result_text.startswith("Yes")
    # The no-spending default is a stated assumption (plan §7.2 step 2).
    assert any("spent" in a for a in yes.assumptions)

    no = wf.run(f"can I afford ${cumulative_60 + 100:,.0f} by round 60?")
    assert no is not None and no.status == "complete"
    (evidence,) = no.evidence
    assert evidence.outputs["affordable"] is False
    assert no.result_text.startswith("No")
    assert "short" in no.result_text


def test_unsupported_range_refuses_precisely() -> None:
    answer = wf.run("how much cash from round 500 to 600?")
    assert answer is not None
    assert answer.status == "unsupported"
    assert any("invalid_range" in w for w in answer.warnings)
    (evidence,) = answer.evidence
    assert evidence.outputs == {"found": False, "reason": "invalid_range"}
    # Precise refusal, never a number.
    assert "$" not in answer.result_text


def test_partially_known_range_is_unsupported_not_partial() -> None:
    answer = wf.run("cash from round 100 to 999?")
    assert answer is not None
    assert answer.status == "unsupported"
    assert any("cash_unavailable" in w for w in answer.warnings)


def test_verification_gate_degrades_on_corrupt_owner_output(monkeypatch) -> None:
    """A range_cash that contradicts its own cumulative endpoints must never
    be presented — the §10.2 completeness gate degrades it to unsupported."""

    def corrupt(round_start, round_end=None):
        return {
            "found": True,
            "single_round": False,
            "round_start": 50,
            "round_end": 60,
            "rounds_counted": 11,
            "range_cash": 99_999.0,  # contradicts the endpoints below
            "cumulative_before_start": 1_000.0,
            "cumulative_at_end": 2_000.0,
            "starting_cash": 650.0,
            "assumptions": "test",
        }

    monkeypatch.setattr(btd6_data_service, "round_cash", corrupt)
    answer = wf.run("cash from round 50 to 60?")
    assert answer is not None
    assert answer.status == "unsupported"
    assert any("verification_failed" in w for w in answer.warnings)
    assert "99,999" not in answer.result_text


def test_reversed_range_is_normalised_with_warning() -> None:
    answer = wf.run("cash from round 60 to 50?")
    assert answer is not None
    assert answer.status == "complete"
    (evidence,) = answer.evidence
    assert evidence.outputs["range_cash"] == 19_840.0
    assert any("reversed" in w for w in answer.warnings)


# ---------------------------------------------------------------------------
# Synthesize — the two render seams the stage consumes
# ---------------------------------------------------------------------------


def test_system_block_hands_result_to_model_without_recompute() -> None:
    answer = wf.run("how much cash from round 50 to 60?")
    assert answer is not None
    block = wf.render_system_block(answer)
    assert "calculation_explained" in block
    assert "do NOT recompute" in block
    assert "$19,840.00" in block
    assert "Q-0043" in block
    # Bounded: compact summary fields only, never per-round detail.
    assert "per_round" not in block
    assert len(block) < 2_000


def test_system_block_unsupported_forbids_invention() -> None:
    answer = wf.run("cash from round 500 to 600?")
    assert answer is not None
    block = wf.render_system_block(answer)
    assert "cannot be answered" in block
    assert "do NOT invent" in block


def test_ledger_entry_grounds_both_number_forms() -> None:
    """The faithfulness verifier is a comma-normalised substring test — the
    entry must ground a reply restating either the formatted ('$19,840.00')
    or the raw-JSON ('19840.0') form of the result."""
    answer = wf.run("how much cash from round 50 to 60?")
    assert answer is not None
    entry = wf.render_ledger_entry(answer)
    payload = json.loads(entry)
    assert payload["workflow"] == wf.WORKFLOW_KEY
    assert "19,840.00" in payload["result"]
    assert payload["evidence"][0]["outputs"]["range_cash"] == 19_840.0
    # The verifier's normalisation: both forms reachable after comma-stripping.
    hay = entry.replace(",", "")
    assert "19840.00" in hay and "19840.0" in hay


def test_workflow_key_matches_a_declared_preset_label() -> None:
    """WORKFLOW_KEY must stay in sync with the preset labels that opt scopes
    into this workflow — a rename on either side orphans the gate."""
    from services import ai_orchestration_presets as presets

    declared = {p.workflow for p in presets.all_presets()}
    assert wf.WORKFLOW_KEY in declared
