"""BTD6 grounding-anchor guard — the asserted numbers in the golden set must be
*grounded*, and the capability message must match what the deterministic layer
can actually do.

This encodes the [PR #704 live-test triage finding](../../docs/audits/pr704-live-test-triage-2026-06-14.md),
routed to the **P1-1 BTD6 eval-cases** lane:

    "capability message must match refusal behaviour; asserted BTD6 numbers must
     be grounded."

The BTD6 *knowledge* eval cases (``tests/evals/cases.py``) are LLM-judged, so their
rubrics bake **hand-written truths** into prose — "$12,025 per 0-4-1 Desperado on
Impoppable", "Elite Lych T1 30,000", "≈ $113,872.30 over ABR rounds 25-83". Those
numbers are exactly what a confident-but-wrong model would also produce, so the
golden set is only meaningful if its asserted truths are themselves reproducible
from the bot's own deterministic data. If the BTD6 dataset is re-seeded to a new
game version, or a rubric number is edited, the eval would otherwise keep grading
against a stale "truth" with nothing to catch the drift.

These guards are **offline** (no provider key, no DB) — they run in the normal
suite, unlike the live ``llm_judge`` evals.

Two directions are closed:

1. **Data drift** — each anchor's number is re-derived from ``services.btd6_data_service``
   and must equal the truth the table claims (so a re-seed that changes a price fails here).
2. **Prose drift** — that same truth must appear (numerically, comma/decimal-insensitive)
   in the named eval case's rubric (so editing a rubric number fails here).

The anchor table is the single bridge between the data and the golden set's prose.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

import pytest
from tests.evals.cases import CASES

from services import ai_introspection_service, btd6_data_service

# --------------------------------------------------------------------------- #
# Rubric introspection — pull the asserted numbers out of a case's grader(s).
# --------------------------------------------------------------------------- #
_NUMBER_RE = re.compile(r"\$?\d[\d,]*(?:\.\d+)?")


def _rubrics(grader: object) -> list[str]:
    """Every ``llm_judge`` rubric reachable from ``grader`` (recursing combinators).

    ``llm_judge`` exposes ``.rubric``; ``all_of`` / ``any_of`` expose ``.subgraders``
    (introspection metadata added in ``tests/evals/graders.py``)."""
    out: list[str] = []
    rubric = getattr(grader, "rubric", None)
    if isinstance(rubric, str):
        out.append(rubric)
    for sub in getattr(grader, "subgraders", ()):  # type: ignore[arg-type]
        out.extend(_rubrics(sub))
    return out


def _rubric_numbers(grader: object) -> set[float]:
    """All numeric tokens asserted across a case's rubric(s), normalized.

    Strips ``$`` and thousands separators so "13,093.90" and "13093.9" compare
    equal, and rounds to cents so the comparison is float-stable."""
    nums: set[float] = set()
    for rubric in _rubrics(grader):
        for token in _NUMBER_RE.findall(rubric):
            cleaned = token.replace("$", "").replace(",", "")
            try:
                nums.add(round(float(cleaned), 2))
            except ValueError:  # pragma: no cover - regex guarantees a number
                continue
    return nums


_CASES_BY_ID = {case.id: case for case in CASES}


# --------------------------------------------------------------------------- #
# Deterministic re-derivations from the live dataset (offline, no DB).
# --------------------------------------------------------------------------- #
def _despo_041_impoppable_unit() -> float:
    res = btd6_data_service.crosspath_cost("desperado", "041", quantity=10)
    assert res.get("found"), res
    return float(res["unit_costs_by_difficulty"]["impoppable"])


def _despo_041_impoppable_x10() -> float:
    res = btd6_data_service.crosspath_cost("desperado", "041", quantity=10)
    assert res.get("found"), res
    return float(res["total_costs_by_difficulty"]["impoppable"])


def _elite_lych_tier(tier: int) -> Callable[[], float]:
    def derive() -> float:
        boss = btd6_data_service.find_boss("lych")
        assert boss is not None and boss.elite_tiers, "lych elite_tiers missing"
        by_tier = {t["tier"]: t["health"] for t in boss.elite_tiers}
        return float(by_tier[tier])

    return derive


def _range_cash(start: int, end: int, roundset: str = "default") -> Callable[[], float]:
    def derive() -> float:
        res = btd6_data_service.round_cash(start, end, roundset=roundset)
        assert res.get("found"), res
        return round(float(res["range_cash"]), 2)

    return derive


# --------------------------------------------------------------------------- #
# The anchor table — each BTD6 number the golden set asserts as truth, paired
# with the deterministic source that must reproduce it.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Anchor:
    case_id: str
    label: str
    expected: float  # the truth the golden set asserts (the bridge value)
    derive: Callable[[], float]  # re-derivation from btd6_data_service


ANCHORS: tuple[Anchor, ...] = (
    # BUG-0003 — "10 041 despos on impop" = ten 0-4-1 Desperados.
    Anchor(
        "knowledge.btd6_despo_bulk_cost_bug_0003",
        "Desperado 0-4-1 unit cost (Impoppable)",
        12025.0,
        _despo_041_impoppable_unit,
    ),
    Anchor(
        "knowledge.btd6_despo_bulk_cost_bug_0003",
        "Desperado 0-4-1 ×10 cost (Impoppable)",
        120250.0,
        _despo_041_impoppable_x10,
    ),
    # BUG-0002 — Elite Lych per-tier health.
    Anchor(
        "knowledge.btd6_elite_lych_hp_bug_0002",
        "Elite Lych T1 HP",
        30000.0,
        _elite_lych_tier(1),
    ),
    Anchor(
        "knowledge.btd6_elite_lych_hp_bug_0002",
        "Elite Lych T2 HP",
        180000.0,
        _elite_lych_tier(2),
    ),
    Anchor(
        "knowledge.btd6_elite_lych_hp_bug_0002",
        "Elite Lych T3 HP",
        1100000.0,
        _elite_lych_tier(3),
    ),
    Anchor(
        "knowledge.btd6_elite_lych_hp_bug_0002",
        "Elite Lych T4 HP",
        4800000.0,
        _elite_lych_tier(4),
    ),
    Anchor(
        "knowledge.btd6_elite_lych_hp_bug_0002",
        "Elite Lych T5 HP",
        24000000.0,
        _elite_lych_tier(5),
    ),
    # BUG-0010 — ABR range cash, rounds 25-83 inclusive.
    Anchor(
        "knowledge.btd6_abr_range_cash_bug_0010",
        "ABR rounds 25-83 cash earned",
        113872.30,
        _range_cash(25, 83, "abr"),
    ),
    # BUG-0001 — standard range cash, rounds 60-68 inclusive.
    Anchor(
        "knowledge.btd6_round_cash_balance_bug_0001",
        "Standard rounds 60-68 cash earned",
        13093.90,
        _range_cash(60, 68),
    ),
    # By-round projection — earned over rounds 50-60 inclusive.
    Anchor(
        "knowledge.btd6_round_cash_by_round_projection",
        "Standard rounds 50-60 cash earned",
        19840.0,
        _range_cash(50, 60),
    ),
    # BUG-0004 — r-shorthand: earned over rounds 54-70 inclusive.
    Anchor(
        "knowledge.btd6_round_cash_r_shorthand_bug_0004",
        "Standard rounds 54-70 cash earned",
        29386.70,
        _range_cash(54, 70),
    ),
)


def test_anchor_table_references_only_real_cases():
    """A stale anchor (a renamed/removed case) is itself drift — fail loudly."""
    missing = sorted({a.case_id for a in ANCHORS} - set(_CASES_BY_ID))
    assert not missing, (
        f"Anchor(s) reference eval case id(s) that no longer exist: {missing}. "
        "Update tests/evals/test_btd6_grounding_anchors.py to the current case ids."
    )


@pytest.mark.parametrize("anchor", ANCHORS, ids=lambda a: f"{a.case_id}:{a.label}")
def test_asserted_number_is_reproduced_by_the_dataset(anchor: Anchor):
    """Direction 1 — data drift: the bridge value must come back from the data."""
    derived = round(anchor.derive(), 2)
    assert derived == round(anchor.expected, 2), (
        f"{anchor.label}: dataset now yields {derived}, but the golden set asserts "
        f"{anchor.expected}. The BTD6 data drifted from the eval truth — re-sync the "
        f"golden-set rubric (and this anchor) to the data, or fix the data."
    )


@pytest.mark.parametrize("anchor", ANCHORS, ids=lambda a: f"{a.case_id}:{a.label}")
def test_asserted_number_appears_in_the_case_rubric(anchor: Anchor):
    """Direction 2 — prose drift: the bridge value must be claimed by the rubric."""
    case = _CASES_BY_ID[anchor.case_id]
    asserted = _rubric_numbers(case.grader)
    assert round(anchor.expected, 2) in asserted, (
        f"{anchor.label}: {anchor.expected} is grounded in the data but not asserted "
        f"in the rubric of {anchor.case_id!r}. The rubric was edited away from the "
        f"grounded truth (rubric numbers: {sorted(asserted)})."
    )


def test_rubric_introspection_actually_reads_a_known_number():
    """Guard the guard: a case whose rubric asserts a number must surface it
    (so a silently-broken extractor can't make the checks above vacuous)."""
    case = _CASES_BY_ID["knowledge.btd6_despo_bulk_cost_bug_0003"]
    assert 12025.0 in _rubric_numbers(case.grader)


# --------------------------------------------------------------------------- #
# Capability-consistency guard — #704 part 1: the capability/answerability
# message must match what the deterministic layer can (and can't) do.
# --------------------------------------------------------------------------- #
def _answerability_domains() -> dict[str, ai_introspection_service.AnswerabilityDomain]:
    snapshot = ai_introspection_service.build_btd6_answerability()
    assert snapshot.available, "answerability snapshot unexpectedly unavailable offline"
    return {d.name: d for d in snapshot.domains}


def test_round_cash_is_advertised_as_a_calculation_including_projection():
    """The #704 finding was the capability line over-stating round-cash. The shipped
    workflow (#634) genuinely does single-round, range, AND projection — so the
    advertised domain must say so (a calculation whose note covers projection),
    never silently regress to a fixture/lookup-only claim."""
    domains = _answerability_domains()
    assert "round_cash" in domains, "round_cash answerability domain missing"
    rc = domains["round_cash"]
    assert (
        rc.kind == "calculation"
    ), f"round_cash advertised as {rc.kind!r}, expected calculation"
    assert "project" in rc.note.lower(), (
        "round_cash note must advertise projection (the #634 workflow) so the "
        f"capability message matches behaviour; got: {rc.note!r}"
    )


def test_modified_economy_is_advertised_as_a_guarded_gap():
    """The other half of the #704 consistency point: modified-economy math
    (Double Cash / Half Cash / farm income) is the thing it refuses, and must be
    named explicitly as NOT applied — so the message never over-promises it."""
    domains = _answerability_domains()
    assert (
        "modified_economy" in domains
    ), "modified_economy answerability domain missing"
    note = domains["modified_economy"].note.lower()
    assert (
        "double cash" in note and "not applied" in note
    ), f"modified_economy must name the unsupported math as NOT applied; got: {note!r}"
