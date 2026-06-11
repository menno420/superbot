"""Round-cash plan→execute→verify workflow (orchestration Phase 4 MVP).

The first — deliberately the *only* — deterministic complex-request workflow
(orchestration plan §7, MVP slice per owner decision Q-0046): the round-cash
question family — "how much cash from round A to B?" and "can I afford X at
round R?". Everything else in plan §7 (general request analysis, the
multi-entity comparison helper, more answer contracts) stays deferred behind
this proven template.

How the slice composes (plan §7.2, specialised to one calculator):

1. **Plan** — :func:`plan_question` deterministically recognises the question
   family from the user's text. Conservative by design (plan §5.4: selection
   stays deterministic and inspectable): a missed match costs nothing — the
   normal model+tools path answers — while a false positive would inject wrong
   evidence, so only clearly matching phrasings engage.
2. **Execute** — the deterministic owner
   :func:`services.btd6_data_service.round_cash` computes the numbers; the
   model never does arithmetic (plan §7.3).
3. **Verify** — the evidence-completeness gate (plan §10.2): required outputs
   present and the Q-0043 inclusive identity
   ``range_cash == cumulative_at_end − cumulative_before_start`` actually
   holds. A failure degrades to a precise *unsupported* answer — never a
   fabricated or contradictory number.
4. **Synthesize** — the natural-language stage appends
   :func:`render_system_block` to the system prompt (the model explains the
   already-computed result and must not alter it) and
   :func:`render_ledger_entry` to the BTD6 faithfulness ledger (so every
   number the model restates is grounded for the post-generation verifier).

Activation is **profile-gated**: ``natural_language_stage._invoke_gateway``
consults this module only when the resolved orchestration profile declares
``workflow == WORKFLOW_KEY`` (today: ``btd6_grounded`` /
``btd6_grounded_strict``). The compatible default profile never reaches it, so
default behaviour stays byte-identical.

Range semantics are an owner decision (**Q-0043**): ``range_cash(A, B)`` counts
BOTH endpoints. The emitted :class:`AIAnswerWithEvidence` carries that
explicitly (``inclusive_range=True`` plus an assumption line) so renderers and
evals can pin it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Literal

from core.runtime.ai.contracts import AIAnswerWithEvidence, CalculationEvidence

# The orchestration-profile workflow label this module implements. Profiles
# declaring it (ai_orchestration_presets) opt their scopes into the workflow.
WORKFLOW_KEY = "analyze_execute_verify"

# The one typed answer contract of the MVP slice (plan §10.1).
ANSWER_CONTRACT = "calculation_explained"

CALCULATOR = "btd6_data_service.round_cash"
# Versions the calculation *semantics* this workflow pins (Q-0043 inclusive
# endpoints) — not the game-data version (CalculationEvidence.data_version).
CALCULATOR_VERSION = "q0043-inclusive-v1"

_INCLUSIVE_ASSUMPTION = (
    "Round ranges are inclusive of both endpoints (owner decision Q-0043): "
    "range_cash(A, B) = cumulative(B) - cumulative(A-1)."
)
_AFFORD_ASSUMPTION = (
    '"At round R" means after completing round R, assuming no cash has been '
    "spent on towers or upgrades up to that point."
)


@dataclass(frozen=True)
class RoundCashPlan:
    """The typed analysis for one recognised round-cash question (plan §7.1)."""

    intent: Literal["range_cash", "afford_check"]
    round_start: int
    round_end: int | None = None
    target_cost: float | None = None
    # BUG-0001: a stated cash-in-hand ("i have 8094$ at round 60 …") — when
    # present the range answer also projects starting_balance + range_cash,
    # deterministically, so the total is grounded in the evidence ledger.
    starting_balance: float | None = None


# ---------------------------------------------------------------------------
# Plan — deterministic question recognition
# ---------------------------------------------------------------------------

_CASH_KEYWORD_RE = re.compile(r"\b(?:cash|money|income|earn(?:ed|ings?|s)?)\b", re.I)

_RANGE_RES = (
    re.compile(
        r"\bfrom\s+rounds?\s+(\d{1,3})\s*(?:to|through|thru|until|till|[-–])"
        r"\s*(?:rounds?\s+)?(\d{1,3})\b",
        re.I,
    ),
    re.compile(
        r"\brounds?\s+(\d{1,3})\s*(?:to|through|thru|[-–])"
        r"\s*(?:rounds?\s+)?(\d{1,3})\b",
        re.I,
    ),
    re.compile(r"\bbetween\s+rounds?\s+(\d{1,3})\s+and\s+(\d{1,3})\b", re.I),
    # BUG-0001 (live miss 2026-06-11): anchors separated by a clause — "at
    # round 60, what is the cash that i will get by going to round 68". Both
    # anchors must carry the literal word "round" and sit within one sentence
    # (≤80 chars apart), so the conservatism of the adjacent patterns is kept;
    # the cash-keyword gate still applies before any range pattern is tried.
    re.compile(
        r"\b(?:at|from|on)\s+round\s+(\d{1,3})\b[^.?!\n]{0,80}?"
        r"\b(?:to|until|till|reach(?:ing)?|going\s+to|get(?:ting)?\s+to)"
        r"\s+round\s+(\d{1,3})\b",
        re.I,
    ),
)

# An ownership cue that marks a stated balance ("i have 8094$ at round 60"),
# as opposed to an incidental number; required before a range question's
# residual amount is read as starting cash.
_BALANCE_CUE_RE = re.compile(
    r"\b(?:i|we)\s+(?:have|got|hold)\b|\bstart(?:ing)?\s+with\b|\bhaving\b",
    re.I,
)

# Masks every "round N" span so round numbers can never be read as money when
# extracting a balance from a range question (same idea as the afford branch's
# anchor masking).
_ROUND_SPAN_RE = re.compile(r"\brounds?\s+\d{1,3}\b", re.I)

_AFFORD_RE = re.compile(r"\bafford\b", re.I)
_AFFORD_ROUND_RE = re.compile(r"\b(?:at|by|on|in)\s+round\s+(\d{1,3})\b", re.I)

# An explicit money amount: $-prefixed, k/m-suffixed, or a bare number of at
# least 3 digits / with thousands commas — so "afford 2 farms at round 30"
# never parses the 2 as a $2 cost (no amount → the workflow stays out).
_AMOUNT_DOLLAR_RE = re.compile(r"\$\s*(\d[\d,]*(?:\.\d+)?)\s*([km])?", re.I)
# Postfix form ("8094$") — seen verbatim in the BUG-0001 production message.
_AMOUNT_DOLLAR_POSTFIX_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*([km])?\s*\$", re.I)
_AMOUNT_SUFFIX_RE = re.compile(r"\b(\d[\d,]*(?:\.\d+)?)\s*([km])\b", re.I)
_AMOUNT_BARE_RE = re.compile(r"\b(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{3,}(?:\.\d+)?)\b")


def _extract_amount(text: str) -> float | None:
    """First explicit money amount in ``text``, or ``None``."""
    match = (
        _AMOUNT_DOLLAR_RE.search(text)
        or _AMOUNT_DOLLAR_POSTFIX_RE.search(text)
        or _AMOUNT_SUFFIX_RE.search(text)
    )
    if match is not None:
        raw, suffix = match.group(1), match.group(2)
    else:
        bare = _AMOUNT_BARE_RE.search(text)
        if bare is None:
            return None
        raw, suffix = bare.group(1), None
    try:
        value = float(raw.replace(",", ""))
    except ValueError:
        return None
    if suffix:
        value *= 1_000 if suffix.lower() == "k" else 1_000_000
    return value


def plan_question(text: str) -> RoundCashPlan | None:
    """Deterministically recognise a round-cash family question, else ``None``.

    ``None`` means "the workflow stays out" — the normal model+tools path runs
    unchanged. The afford branch is tried first ("can I afford X at round R"
    needs no cash keyword); when it cannot extract both a round anchor and an
    explicit amount it falls through to the range branch rather than blocking
    it (compound questions keep whatever deterministic help is extractable).
    """
    if not text:
        return None
    if _AFFORD_RE.search(text):
        round_match = _AFFORD_ROUND_RE.search(text)
        if round_match is not None:
            masked = (
                text[: round_match.start()]
                + " " * (round_match.end() - round_match.start())
                + text[round_match.end() :]
            )
            amount = _extract_amount(masked)
            if amount is not None and amount > 0:
                return RoundCashPlan(
                    intent="afford_check",
                    round_start=int(round_match.group(1)),
                    target_cost=amount,
                )
    if not _CASH_KEYWORD_RE.search(text):
        return None
    for pattern in _RANGE_RES:
        match = pattern.search(text)
        if match is not None:
            return RoundCashPlan(
                intent="range_cash",
                round_start=int(match.group(1)),
                round_end=int(match.group(2)),
                starting_balance=_extract_balance(text),
            )
    return None


def _extract_balance(text: str) -> float | None:
    """A stated cash-in-hand for a range question, or ``None`` (BUG-0001).

    Conservative on purpose: requires an ownership cue, and masks every
    "round N" span first so round numbers can never be misread as money.
    """
    if not _BALANCE_CUE_RE.search(text):
        return None
    masked = _ROUND_SPAN_RE.sub(lambda m: " " * len(m.group()), text)
    amount = _extract_amount(masked)
    if amount is None or amount <= 0:
        return None
    return amount


# ---------------------------------------------------------------------------
# Execute + verify
# ---------------------------------------------------------------------------

_REQUIRED_RANGE_FIELDS = (
    "range_cash",
    "cumulative_before_start",
    "cumulative_at_end",
    "rounds_counted",
)


def _data_version() -> str | None:
    try:
        from services import btd6_data_service

        return btd6_data_service.get_dataset().game_version or None
    except Exception:  # noqa: BLE001 — version stamp must never block the answer
        return None


def _evidence_id(plan: RoundCashPlan) -> str:
    if plan.intent == "afford_check":
        return f"afford:r{plan.round_start}:cost{plan.target_cost:g}"
    end = plan.round_end if plan.round_end is not None else plan.round_start
    return f"round_cash:r{plan.round_start}-r{end}"


def _result_assumptions(result: dict[str, Any]) -> tuple[str, ...]:
    base = result.get("assumptions")
    parts: list[str] = [str(base)] if base else []
    parts.append(_INCLUSIVE_ASSUMPTION)
    return tuple(parts)


def _verify_range(result: dict[str, Any]) -> tuple[str, ...]:
    """Evidence-completeness gate for an inclusive-range result (plan §10.2).

    Checks the Q-0043 identity on the owner's own outputs — a disagreement
    means corrupt data, and the answer must degrade to *unsupported* rather
    than present numbers that contradict each other.
    """
    missing = [
        field
        for field in _REQUIRED_RANGE_FIELDS
        if not isinstance(result.get(field), (int, float))
    ]
    if missing:
        return (f"evidence_incomplete: missing {', '.join(missing)}",)
    problems: list[str] = []
    expected = round(
        float(result["cumulative_at_end"]) - float(result["cumulative_before_start"]),
        2,
    )
    if abs(expected - float(result["range_cash"])) > 0.05:
        problems.append(
            f"verification_failed: range_cash ({result['range_cash']}) != "
            f"cumulative_at_end - cumulative_before_start ({expected})",
        )
    span = int(result["round_end"]) - int(result["round_start"]) + 1
    if int(result["rounds_counted"]) != span:
        problems.append(
            f"verification_failed: rounds_counted ({result['rounds_counted']}) "
            f"!= inclusive span ({span})",
        )
    return tuple(problems)


def _answer(
    plan: RoundCashPlan,
    *,
    status: Literal["complete", "unsupported"],
    result_text: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    assumptions: tuple[str, ...],
    warnings: tuple[str, ...] = (),
) -> AIAnswerWithEvidence:
    evidence = CalculationEvidence(
        evidence_id=_evidence_id(plan),
        calculator=CALCULATOR,
        calculator_version=CALCULATOR_VERSION,
        normalized_inputs=inputs,
        assumptions=assumptions,
        outputs=outputs,
        warnings=warnings,
        data_version=_data_version(),
    )
    return AIAnswerWithEvidence(
        contract=ANSWER_CONTRACT,
        workflow=WORKFLOW_KEY,
        intent=plan.intent,
        status=status,
        result_text=result_text,
        inclusive_range=True,
        evidence=(evidence,),
        assumptions=assumptions,
        warnings=warnings,
    )


def _unsupported(
    plan: RoundCashPlan,
    inputs: dict[str, Any],
    result: dict[str, Any],
) -> AIAnswerWithEvidence:
    """Precise refusal (plan §7.2 step 8) — names what is missing, no numbers."""
    reason = str(result.get("reason") or "unavailable")
    note = str(result.get("note") or "the round-cash data cannot answer this")
    return _answer(
        plan,
        status="unsupported",
        result_text=(
            f"The deterministic round-cash calculator cannot answer this "
            f"({reason}): {note}"
        ),
        inputs=inputs,
        outputs={"found": False, "reason": reason},
        assumptions=(_INCLUSIVE_ASSUMPTION,),
        warnings=(f"{reason}: {note}",),
    )


def _verification_failed(
    plan: RoundCashPlan,
    inputs: dict[str, Any],
    problems: tuple[str, ...],
) -> AIAnswerWithEvidence:
    return _answer(
        plan,
        status="unsupported",
        result_text=(
            "The deterministic round-cash result failed its verification gate, "
            "so no number can be stated for this question."
        ),
        inputs=inputs,
        outputs={"found": False, "reason": "verification_failed"},
        assumptions=(_INCLUSIVE_ASSUMPTION,),
        warnings=problems,
    )


def _run_range(plan: RoundCashPlan) -> AIAnswerWithEvidence:
    from services import btd6_data_service

    result = btd6_data_service.round_cash(plan.round_start, plan.round_end)
    inputs: dict[str, Any] = {
        "round_start": plan.round_start,
        "round_end": plan.round_end,
    }
    if not result.get("found"):
        return _unsupported(plan, inputs, result)

    assumptions = _result_assumptions(result)
    if result.get("single_round"):
        round_value = result.get("round_cash")
        cumulative = result.get("cumulative_cash")
        if not isinstance(round_value, (int, float)) or not isinstance(
            cumulative,
            (int, float),
        ):
            return _verification_failed(
                plan,
                inputs,
                ("evidence_incomplete: missing round_cash / cumulative_cash",),
            )
        outputs: dict[str, Any] = {
            "round": result["round_start"],
            "round_cash": round_value,
            "cumulative_cash": cumulative,
            "starting_cash": result.get("starting_cash"),
        }
        result_text = (
            f"Cash earned on round {result['round_start']} (standard rounds, "
            f"Medium difficulty): ${float(round_value):,.2f}. Cumulative cash "
            f"through round {result['round_start']}: ${float(cumulative):,.2f}."
        )
        return _answer(
            plan,
            status="complete",
            result_text=result_text,
            inputs=inputs,
            outputs=outputs,
            assumptions=assumptions,
        )

    problems = _verify_range(result)
    if problems:
        return _verification_failed(plan, inputs, problems)

    outputs = {
        "round_start": result["round_start"],
        "round_end": result["round_end"],
        "rounds_counted": result["rounds_counted"],
        "inclusive": True,
        "range_cash": result["range_cash"],
        "cumulative_before_start": result["cumulative_before_start"],
        "cumulative_at_end": result["cumulative_at_end"],
        "starting_cash": result.get("starting_cash"),
    }
    warnings: tuple[str, ...] = ()
    if result.get("normalized"):
        warnings = ("range endpoints were given reversed and have been normalised",)
    result_text = (
        f"Cash earned from round {result['round_start']} through round "
        f"{result['round_end']} — inclusive of both endpoints — is "
        f"${float(result['range_cash']):,.2f} (standard rounds, Medium "
        f"difficulty, no income towers)."
    )
    if plan.starting_balance is not None:
        projected = round(
            float(plan.starting_balance) + float(result["range_cash"]),
            2,
        )
        inputs["starting_balance"] = plan.starting_balance
        outputs["starting_balance"] = plan.starting_balance
        outputs["projected_total"] = projected
        result_text += (
            f" Starting from ${float(plan.starting_balance):,.2f}, that "
            f"projects to ≈ ${projected:,.2f} by the end of round "
            f"{result['round_end']}."
        )
        assumptions = assumptions + (
            f"the stated ${float(plan.starting_balance):,.2f} is treated as "
            f"cash in hand entering round {result['round_start']}, and the "
            f"projection assumes nothing is spent in between",
        )
    return _answer(
        plan,
        status="complete",
        result_text=result_text,
        inputs=inputs,
        outputs=outputs,
        assumptions=assumptions,
        warnings=warnings,
    )


def _run_afford(plan: RoundCashPlan) -> AIAnswerWithEvidence:
    from services import btd6_data_service

    result = btd6_data_service.round_cash(plan.round_start)
    target = float(plan.target_cost or 0)
    inputs: dict[str, Any] = {"round": plan.round_start, "target_cost": target}
    if not result.get("found"):
        return _unsupported(plan, inputs, result)
    cumulative = result.get("cumulative_cash")
    if not isinstance(cumulative, (int, float)):
        return _verification_failed(
            plan,
            inputs,
            ("evidence_incomplete: missing cumulative_cash",),
        )
    affordable = float(cumulative) >= target
    margin = round(float(cumulative) - target, 2)
    outputs: dict[str, Any] = {
        "round": result["round_start"],
        "cumulative_cash": cumulative,
        "target_cost": target,
        "affordable": affordable,
        "margin": margin,
    }
    verdict = "Yes" if affordable else "No"
    relation = f"${margin:,.2f} to spare" if affordable else f"${-margin:,.2f} short"
    result_text = (
        f"{verdict} — total cash earned through the end of round "
        f"{result['round_start']} (standard rounds, Medium difficulty, nothing "
        f"spent) is ${float(cumulative):,.2f}, which is {relation} against a "
        f"${target:,.2f} cost."
    )
    assumptions = _result_assumptions(result) + (_AFFORD_ASSUMPTION,)
    return _answer(
        plan,
        status="complete",
        result_text=result_text,
        inputs=inputs,
        outputs=outputs,
        assumptions=assumptions,
    )


def run(text: str) -> AIAnswerWithEvidence | None:
    """Plan → execute → verify for one user message.

    ``None`` means the question is not in the round-cash family — the caller
    proceeds exactly as if this module did not exist. A non-``None`` answer is
    always evidence-backed: complete, or a precise unsupported refusal.
    """
    plan = plan_question(text)
    if plan is None:
        return None
    if plan.intent == "afford_check":
        return _run_afford(plan)
    return _run_range(plan)


# ---------------------------------------------------------------------------
# Synthesize — render for the system prompt + the faithfulness ledger
# ---------------------------------------------------------------------------


def _evidence_payload(answer: AIAnswerWithEvidence) -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": e.evidence_id,
            "calculator": e.calculator,
            "calculator_version": e.calculator_version,
            "normalized_inputs": e.normalized_inputs,
            "outputs": e.outputs,
            "data_version": e.data_version,
        }
        for e in answer.evidence
    ]


def render_system_block(answer: AIAnswerWithEvidence) -> str:
    """The system-prompt block handing the computed result to the model.

    Plan §7.3: the model explains; it must not recompute or alter the numbers.
    Bounded: evidence outputs are the compact summary fields (never per-round
    detail), so the block stays a few hundred characters.
    """
    if answer.status == "unsupported":
        directive = (
            "A deterministic BTD6 calculator determined this round-cash "
            "question cannot be answered from the available data. Tell the "
            "user exactly what is unavailable; do NOT invent or estimate "
            "numbers."
        )
    else:
        directive = (
            "A deterministic BTD6 calculator already answered this round-cash "
            "question. Base your reply on this result exactly: explain it "
            "briefly, state the assumptions, and do NOT recompute, alter, or "
            "contradict its numbers."
        )
    lines = [
        f"[Deterministic round-cash workflow result — answer contract: "
        f"{answer.contract}]",
        directive,
        f"Result: {answer.result_text}",
    ]
    if answer.assumptions:
        lines.append("Assumptions: " + " ".join(answer.assumptions))
    if answer.warnings:
        lines.append("Warnings: " + "; ".join(answer.warnings))
    lines.append(
        "Evidence: "
        + json.dumps(_evidence_payload(answer), default=str, sort_keys=True),
    )
    return "\n".join(lines)


def render_ledger_entry(answer: AIAnswerWithEvidence) -> str:
    """The faithfulness-ledger entry grounding the reply's numbers.

    Carries BOTH the formatted ``result_text`` and the raw evidence outputs:
    the post-generation verifier's number check is a comma-normalised
    substring test, so the model restating either ``$19,840.00`` (formatted)
    or ``19840.0`` (raw JSON) must find its form in the haystack.
    """
    return json.dumps(
        {
            "workflow": answer.workflow,
            "result": answer.result_text,
            "evidence": _evidence_payload(answer),
        },
        default=str,
        sort_keys=True,
    )


__all__ = [
    "ANSWER_CONTRACT",
    "CALCULATOR",
    "CALCULATOR_VERSION",
    "WORKFLOW_KEY",
    "RoundCashPlan",
    "plan_question",
    "render_ledger_entry",
    "render_system_block",
    "run",
]
