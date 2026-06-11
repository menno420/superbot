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
``workflow == WORKFLOW_KEY``. Since 2026-06-11 that includes the compatible
default and balanced-helper presets (BUG-0001 recurred live on a default-
profile channel: the normal model+tools path *cannot* answer arithmetic
questions by design — the number guard rightly blocks ungrounded sums — so
gating the only workflow that can answer them behind a manually-set profile
left every default channel refusing; see ``ai_orchestration_presets``).
``no_tools`` keeps it off (an explicit conversational-only operator choice).

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
from utils.btd6.keywords import ABR_CUE_RE as _ABR_CUE_RE

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
    # "… at the END of r53" (live, 2026-06-11): the completion cue on the
    # range's lower round shifts the start one round later (that round's
    # income is already counted/held); kept here so the answer's assumption
    # line can say so explicitly.
    completed_round_anchor: int | None = None
    # BUG-0010 (live, 2026-06-11): "how much cash do I get in ABR from r25 to
    # r83" computed the standard set and the model then claimed ABR was
    # uncovered. The cue routes the calculation to the ABR round set, which
    # the data service has always supported.
    roundset: str = "default"
    # A cash modifier named in the question ("double cash", "half cash") —
    # never applied (the calculator computes base economy only); carried so
    # the answer states that explicitly instead of leaving it to the model.
    unsupported_modifier: str | None = None


# ---------------------------------------------------------------------------
# Plan — deterministic question recognition
# ---------------------------------------------------------------------------

_CASH_KEYWORD_RE = re.compile(r"\b(?:cash|money|income|earn(?:ed|ings?|s)?)\b", re.I)

# Cash modifiers the calculator deliberately never applies (Q-0043 honesty
# posture: base economy only, never a guessed number).
_MODIFIER_RE = re.compile(r"\b(double|half)\s+cash\b", re.I)

# A "how much would I have …" money question carries no cash noun at all —
# the live 2026-06-11 miss "if I have 20K by round 50, how much would I have
# by round 60?" failed this gate and refused. The verb set is money-flavoured
# (have/get/make/earn/gain); stat verbs ("how much pierce does X have") can
# slip the gate but are filtered by the range patterns, which still require
# two round anchors.
_MONEY_QUESTION_RE = re.compile(
    r"\bhow\s+much\b[^.?!\n]{0,60}?\b(?:have|get|make|earn|gain)\b",
    re.I,
)

# One shared round-token vocabulary: "round 53" / "rounds 53" / "r53" /
# "r 53" — players use the r-shorthand constantly and the live 2026-06-11
# "on r70 … at the end of r53" question matched nothing because every
# pattern demanded the literal word "round". The trailing \b on the digits
# keeps "r2d2"-style tokens out (digit→letter is not a boundary).
_RT = r"(?:rounds?|r)\s*"
# An anchor may reference a round's completion ("at the END of r53", "after
# round 53"); the start-shift logic reads the cue separately, this fragment
# only lets the patterns match through it.
_RTA = r"(?:the\s+)?(?:end\s+of\s+)?" + _RT

_RANGE_RES = (
    re.compile(
        r"\bfrom\s+" + _RTA + r"(\d{1,3})\s*(?:to|through|thru|until|till|[-–])"
        r"\s*(?:" + _RTA + r")?(\d{1,3})\b",
        re.I,
    ),
    re.compile(
        r"\b" + _RT + r"(\d{1,3})\s*(?:to|through|thru|[-–])"
        r"\s*(?:" + _RT + r")?(\d{1,3})\b",
        re.I,
    ),
    re.compile(r"\bbetween\s+" + _RT + r"(\d{1,3})\s+and\s+(\d{1,3})\b", re.I),
    # BUG-0001 (live miss 2026-06-11): anchors separated by a clause — "at
    # round 60, what is the cash that i will get by going to round 68". Both
    # anchors must carry a literal round token and sit within one sentence
    # (≤80 chars apart), so the conservatism of the adjacent patterns is kept;
    # the cash-keyword gate still applies before any range pattern is tried.
    # "by" joined both anchor sets for the same-day follow-up miss "i have
    # 20K by round 50, how much would I have by round 60"; the r-shorthand +
    # completion infix came from "on r70 if I had 26932 at the end of r53"
    # (the reversed anchors are normalised downstream).
    re.compile(
        r"\b(?:at|from|on|by)\s+" + _RTA + r"(\d{1,3})\b[^.?!\n]{0,80}?"
        r"\b(?:to|until|till|reach(?:ing)?|going\s+to|get(?:ting)?\s+to|by|at)"
        r"\s+" + _RTA + r"(\d{1,3})\b",
        re.I,
    ),
)

# "end of round N" / "after r N" — the completion cue that shifts a range
# start one round later when attached to the LOWER round (its income is
# already earned); on the upper round it is a no-op (ranges are inclusive).
_COMPLETED_ROUND_TMPL = (
    r"\b(?:end\s+of|after|beat(?:ing)?|clear(?:ed|ing)?|finish(?:ed|ing)?|"
    r"complet(?:ed|ing))\s+(?:the\s+)?(?:rounds?|r)\s*{n}\b"
)


def _apply_completed_round_shift(
    text: str,
    first: int,
    second: int,
) -> tuple[int, int, int | None]:
    """Shift the range start past a completed lower round, order preserved.

    "How much do I have on r70 if I had 26932 at the end of r53" must count
    rounds 54-70 — round 53's income is already inside the stated 26,932.
    Without the shift the inclusive range double-counts it (live wrong
    answer, 2026-06-11: the model presented cumulative(70) = $71,315.20 as
    the total; truth is 26,932 + range(54,70) = $56,318.70).
    """
    lo, hi = min(first, second), max(first, second)
    if lo >= hi:
        return first, second, None
    if re.search(_COMPLETED_ROUND_TMPL.format(n=lo), text, re.I) is None:
        return first, second, None
    shifted = lo + 1
    return (
        shifted if first == lo else first,
        shifted if second == lo else second,
        lo,
    )


# An ownership cue that marks a stated balance ("i have 8094$ at round 60",
# "if I had 26932 at the end of r53"), as opposed to an incidental number;
# required before a range question's residual amount is read as starting cash.
_BALANCE_CUE_RE = re.compile(
    r"\b(?:i|we)\s+(?:have|had|got|hold|held)\b|\bstart(?:ing|ed)?\s+with\b"
    r"|\bhaving\b",
    re.I,
)

# Masks every round-token span ("round 60", "r53") so round numbers can never
# be read as money when extracting a balance from a range question (same idea
# as the afford branch's anchor masking).
_ROUND_SPAN_RE = re.compile(r"\b(?:rounds?|r)\s*\d{1,3}\b", re.I)

_AFFORD_RE = re.compile(r"\bafford\b", re.I)
_AFFORD_ROUND_RE = re.compile(
    r"\b(?:at|by|on|in)\s+" + _RTA + r"(\d{1,3})\b",
    re.I,
)

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
                    roundset=_roundset_for(text),
                    unsupported_modifier=_modifier_for(text),
                )
    if not (_CASH_KEYWORD_RE.search(text) or _MONEY_QUESTION_RE.search(text)):
        return None
    for pattern in _RANGE_RES:
        match = pattern.search(text)
        if match is not None:
            start, end, completed = _apply_completed_round_shift(
                text,
                int(match.group(1)),
                int(match.group(2)),
            )
            return RoundCashPlan(
                intent="range_cash",
                round_start=start,
                round_end=end,
                starting_balance=_extract_balance(text),
                completed_round_anchor=completed,
                roundset=_roundset_for(text),
                unsupported_modifier=_modifier_for(text),
            )
    return None


def _roundset_for(text: str) -> str:
    """Return "abr" when the question names the Alternate Bloons Rounds set."""
    return "abr" if _ABR_CUE_RE.search(text) else "default"


def _modifier_for(text: str) -> str | None:
    """A named cash modifier ("double cash"/"half cash"), or ``None``."""
    match = _MODIFIER_RE.search(text)
    return match.group(0).lower() if match else None


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
    suffix = ":abr" if plan.roundset == "abr" else ""
    if plan.intent == "afford_check":
        return f"afford:r{plan.round_start}:cost{plan.target_cost:g}{suffix}"
    end = plan.round_end if plan.round_end is not None else plan.round_start
    return f"round_cash:r{plan.round_start}-r{end}{suffix}"


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


def _economy_label(plan: RoundCashPlan) -> str:
    """The round-set/economy phrase every result_text carries (BUG-0010)."""
    if plan.roundset == "abr":
        return "ABR — Alternate Bloons Rounds, entered at round 3"
    return "standard rounds, Medium difficulty"


def _modifier_warning(plan: RoundCashPlan) -> tuple[str, ...]:
    if plan.unsupported_modifier is None:
        return ()
    return (
        f"{plan.unsupported_modifier} is NOT applied — the calculator computes "
        "base economy only; these figures are without any cash modifier",
    )


def _run_range(plan: RoundCashPlan) -> AIAnswerWithEvidence:
    from services import btd6_data_service

    result = btd6_data_service.round_cash(
        plan.round_start,
        plan.round_end,
        roundset=plan.roundset,
    )
    inputs: dict[str, Any] = {
        "round_start": plan.round_start,
        "round_end": plan.round_end,
        "roundset": plan.roundset,
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
            f"Cash earned on round {result['round_start']} "
            f"({_economy_label(plan)}): ${float(round_value):,.2f}. "
            f"Cumulative cash through round {result['round_start']}: "
            f"${float(cumulative):,.2f}."
        )
        return _answer(
            plan,
            status="complete",
            result_text=result_text,
            inputs=inputs,
            outputs=outputs,
            assumptions=assumptions,
            warnings=_modifier_warning(plan),
        )

    problems = _verify_range(result)
    if problems:
        return _verification_failed(plan, inputs, problems)

    if plan.completed_round_anchor is not None:
        assumptions = assumptions + (
            f'"end of round {plan.completed_round_anchor}" anchors the range '
            f"start at round {plan.completed_round_anchor + 1} — round "
            f"{plan.completed_round_anchor}'s income is already counted in "
            f"what the user holds",
        )

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
    warnings: tuple[str, ...] = _modifier_warning(plan)
    if result.get("normalized"):
        warnings = warnings + (
            "range endpoints were given reversed and have been normalised",
        )
    result_text = (
        f"Cash earned from round {result['round_start']} through round "
        f"{result['round_end']} — inclusive of both endpoints — is "
        f"${float(result['range_cash']):,.2f} ({_economy_label(plan)}, "
        f"no income towers)."
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

    result = btd6_data_service.round_cash(plan.round_start, roundset=plan.roundset)
    target = float(plan.target_cost or 0)
    inputs: dict[str, Any] = {
        "round": plan.round_start,
        "target_cost": target,
        "roundset": plan.roundset,
    }
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
        f"{result['round_start']} ({_economy_label(plan)}, nothing "
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
        warnings=_modifier_warning(plan),
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
