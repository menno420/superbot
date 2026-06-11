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


def test_plan_separated_anchors_production_phrasing_bug_0001() -> None:
    # BUG-0001 (live, 2026-06-11) — the exact production message, verbatim.
    plan = wf.plan_question(
        "lets say i have 8094$ at round 60, "
        "what is the cash that i will get by going to round 68",
    )
    assert plan is not None
    assert plan.intent == "range_cash"
    assert (plan.round_start, plan.round_end) == (60, 68)
    # The stated cash-in-hand is captured (postfix "8094$" form included).
    assert plan.starting_balance == 8094.0


def test_plan_separated_anchors_without_balance_cue() -> None:
    plan = wf.plan_question(
        "i'm at round 40 — how much money will i earn by getting to round 60?",
    )
    assert plan is not None
    assert plan.intent == "range_cash"
    assert (plan.round_start, plan.round_end) == (40, 60)
    assert plan.starting_balance is None  # no ownership cue → no balance


def test_plan_afford_accepts_postfix_dollar() -> None:
    plan = wf.plan_question("can I afford a 8094$ upgrade at round 50?")
    assert plan is not None
    assert plan.intent == "afford_check"
    assert plan.round_start == 50
    assert plan.target_cost == 8094.0


def test_plan_separated_anchors_stay_conservative() -> None:
    cases = [
        # No cash keyword → the range patterns are never consulted.
        "what bloons come at round 60 and going to round 68?",
        # Anchors more than one sentence apart stay out.
        "i have cash at round 60. " + ("x" * 40) + ". going to round 68?",
    ]
    for text in cases:
        assert wf.plan_question(text) is None, text


def test_plan_by_round_anchors_with_balance_production_phrasing() -> None:
    # Live miss (2026-06-11, same morning as BUG-0001's recurrence) — the
    # exact production message, verbatim: no cash noun at all ("how much
    # would I have") and both anchors carried by "by round N".
    plan = wf.plan_question(
        "if I have 20K by round 50, how much would I have by round 60?",
    )
    assert plan is not None
    assert plan.intent == "range_cash"
    assert (plan.round_start, plan.round_end) == (50, 60)
    # "20K" is a stated balance (ownership cue + k-suffix amount).
    assert plan.starting_balance == 20000.0


def test_plan_money_question_gate_stays_conservative() -> None:
    cases = [
        # Money-ish verb but no two round anchors → out.
        "how much pierce does juggernaut have",
        "how much would I have if I sell everything",
        # Cost questions are not round-cash questions.
        "how much do 10 041 despos cost on impop",
        # "how much … have" with only one round anchor → out.
        "how much would I have by round 60?",
    ]
    for text in cases:
        assert wf.plan_question(text) is None, text


def test_plan_r_shorthand_with_completed_round_production_phrasing() -> None:
    # Live miss (2026-06-11, post-#703): "How much do I have on r70 if I had
    # 26932 at the end of r53" — r-shorthand anchors matched nothing, the
    # workflow stayed out, and the model presented cumulative(70) =
    # $71,315.20 as the total. Truth: 26,932 + range(54..70) = $56,318.70.
    plan = wf.plan_question(
        "How much do I have on r70 if I had 26932 at the end of r53",
    )
    assert plan is not None
    assert plan.intent == "range_cash"
    # Anchors arrive reversed (70 first); "end of r53" shifts the lower
    # anchor to 54 — the service normalises the order downstream.
    assert {plan.round_start, plan.round_end} == {70, 54}
    assert plan.starting_balance == 26932.0
    assert plan.completed_round_anchor == 53


def test_run_completed_round_projection_counts_from_next_round() -> None:
    answer = wf.run("How much do I have on r70 if I had 26932 at the end of r53")
    assert answer is not None
    assert answer.status == "complete"
    outputs = answer.evidence[0].outputs
    assert (outputs["round_start"], outputs["round_end"]) == (54, 70)
    assert outputs["starting_balance"] == 26932.0
    assert outputs["projected_total"] == 56318.7
    assert "$56,318.70" in answer.result_text
    assert any("end of round 53" in a for a in answer.assumptions)


def test_plan_r_shorthand_basic_range() -> None:
    plan = wf.plan_question("how much cash from r50 to r60")
    assert plan is not None
    assert (plan.round_start, plan.round_end) == (50, 60)
    assert plan.completed_round_anchor is None


def test_completed_cue_on_upper_round_is_a_no_op() -> None:
    # Inclusive ranges already count the end round — "to the end of round
    # 60" must not shift anything.
    plan = wf.plan_question("how much cash from round 50 to the end of round 60")
    assert plan is not None
    assert (plan.round_start, plan.round_end) == (50, 60)
    assert plan.completed_round_anchor is None


def test_r_token_requires_digit_boundary() -> None:
    # "r2d2" / "r 5" word salad never reads as a round anchor.
    for text in (
        "how much money does r2d2 have",
        "there r 5 of us, how much cash do we need",
    ):
        assert wf.plan_question(text) is None, text


def test_range_answer_projects_balance_for_by_round_phrasing() -> None:
    answer = wf.run("if I have 20K by round 50, how much would I have by round 60?")
    assert answer is not None
    assert answer.status == "complete"
    outputs = answer.evidence[0].outputs
    assert outputs["starting_balance"] == 20000.0
    expected = round(20000.0 + float(outputs["range_cash"]), 2)
    assert abs(float(outputs["projected_total"]) - expected) < 0.01
    assert "projects to" in answer.result_text


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
    assert evidence.normalized_inputs == {
        "round_start": 50,
        "round_end": 60,
        "roundset": "default",
    }
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


def test_range_answer_projects_stated_starting_balance_bug_0001() -> None:
    # BUG-0001 end-to-end: the production phrasing must produce a grounded
    # projected total = stated balance + the inclusive range sum.
    answer = wf.run(
        "lets say i have 8094$ at round 60, "
        "what is the cash that i will get by going to round 68",
    )
    assert answer is not None
    assert answer.status == "complete"
    assert answer.intent == "range_cash"
    (evidence,) = answer.evidence
    raw = btd6_data_service.round_cash(60, 68)
    assert raw.get("found")
    expected_total = round(8094.0 + float(raw["range_cash"]), 2)
    assert evidence.outputs["starting_balance"] == 8094.0
    assert evidence.outputs["projected_total"] == expected_total
    assert evidence.normalized_inputs["starting_balance"] == 8094.0
    # The projection rides the result text and is stated as an assumption,
    # so the number-guard haystack contains every figure the model may say.
    assert f"${expected_total:,.2f}" in answer.result_text
    assert any("cash in hand" in a for a in answer.assumptions)


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

    def corrupt(round_start, round_end=None, **_kw):
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


def test_plan_abr_qualifier_and_modifier_production_phrasing() -> None:
    # BUG-0010 (live, 2026-06-11, first Q-0086 session): "in ABR … double
    # cash" planned the STANDARD set, the model served $107,164.60 labeled
    # "not ABR" and claimed the calculator can't do ABR — it always could
    # (the tool's roundset='abr'); only the workflow never parsed the cue.
    plan = wf.plan_question(
        "how much cash do I get in ABR from r25 to r83 when I have double "
        "cash and I started with 5443",
    )
    assert plan is not None
    assert plan.intent == "range_cash"
    assert (plan.round_start, plan.round_end) == (25, 83)
    assert plan.roundset == "abr"
    assert plan.starting_balance == 5443.0
    assert plan.unsupported_modifier == "double cash"


def test_run_abr_range_uses_abr_economy_and_flags_modifier() -> None:
    from services import btd6_data_service

    answer = wf.run(
        "how much cash do I get in ABR from r25 to r83 when I have double "
        "cash and I started with 5443",
    )
    assert answer is not None
    assert answer.status == "complete"
    expected = btd6_data_service.round_cash(25, 83, roundset="abr")
    outputs = answer.evidence[0].outputs
    assert outputs["range_cash"] == expected["range_cash"]
    assert answer.evidence[0].normalized_inputs["roundset"] == "abr"
    assert "ABR — Alternate Bloons Rounds" in answer.result_text
    assert "standard rounds" not in answer.result_text
    assert any("double cash is NOT applied" in w for w in answer.warnings)
    assert ":abr" in answer.evidence[0].evidence_id
    # The ABR range genuinely differs from standard — the live answer's
    # standard figure must not appear.
    standard = btd6_data_service.round_cash(25, 83)
    assert expected["range_cash"] != standard["range_cash"]


def test_standard_phrasings_stay_default_roundset() -> None:
    plan = wf.plan_question("how much cash do I earn from round 50 to round 60?")
    assert plan is not None
    assert plan.roundset == "default"
    assert plan.unsupported_modifier is None
    answer = wf.run("how much cash do I earn from round 50 to round 60?")
    assert "$19,840.00" in answer.result_text
    assert "standard rounds, Medium difficulty" in answer.result_text
