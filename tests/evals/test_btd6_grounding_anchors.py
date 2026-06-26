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

Curation principle (why not every rubric/fixture number is anchored): an anchor is
only added for a value that is BOTH an asserted *truth* AND cleanly reproducible
from a public ``btd6_*_service`` accessor. The range-cash figures anchor via
``round_cash(start, end).range_cash`` and the projected running totals via
``stated_start + range_cash`` — the stated start being the constant in each case's
``user_message`` (the convention is *start + range*, NOT cumulative-from-round-1;
a naive ``round_cash(1, N)`` lands ~$10+ off precisely because it is the wrong
accessor — that was an earlier curation miss, now resolved). The numbers that stay
deliberately NOT anchored are: (a) *distractors* the rubric tells the judge to
REJECT (BUG-0004's "$71,315.20" cumulative mislabel, truth "$56,318.70"; BUG-0010's
"$107,164.60" standard-set figure given as the ABR answer), and (b) the bare
user-supplied starting figures (8094 / 20000 / 26932 / 5443) — those are inputs
stated in the prompt, not data-derived truths, so a *data*-drift guard over them
would be meaningless. Anchoring a distractor or a non-derivable value would assert a
wrong "truth" and make the guard lie — the opposite of its purpose (CLAUDE.md Q-0120:
a green check that contradicts the evidence is a bug in the check). Add an anchor only
when you can derive it exactly from the dataset.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

import pytest
from tests.evals.cases import CASES

from services import ai_introspection_service, btd6_data_service, btd6_stats_service

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


def _projected_total(
    start_cash: float, start: int, end: int, roundset: str = "default"
) -> Callable[[], float]:
    """The running total a projection case asserts: stated start + range cash.

    The convention is ``stated_starting_cash + round_cash(start, end).range_cash``
    — the stated start is the constant in the case's ``user_message`` (e.g.
    "i have 8094$ at round 60"), NOT a cumulative-from-round-1 figure. (A naive
    ``round_cash(1, end)`` does not reproduce the total; that was the curation
    gap #1458 flagged — it used the wrong accessor.)"""

    def derive() -> float:
        res = btd6_data_service.round_cash(start, end, roundset=roundset)
        assert res.get("found"), res
        return round(float(start_cash) + float(res["range_cash"]), 2)

    return derive


_MOAB_SPECIAL_RE = re.compile(r"\+(\d+) vs MOAB-Class")


def _moab_class_bonus(tower_id: str, code: str) -> Callable[[], float]:
    """The ``+N vs MOAB-Class`` bonus for a tower tier, from its committed stats.

    This is the #855 Layer A data the grounding case asserts. It reads the public
    ``btd6_stats_service`` tier ``specials`` (a structured tuple, e.g.
    ``('+15 vs MOAB-Class',)``) — the same source the grounding renders from — and
    extracts the integer bonus."""

    def derive() -> float:
        tower = btd6_stats_service.get_tower_stats(tower_id)
        assert tower is not None, f"{tower_id} stats missing"
        stats = btd6_stats_service.normal_stats(tower.tier(code))
        for special in stats.specials:
            match = _MOAB_SPECIAL_RE.search(special)
            if match:
                return float(match.group(1))
        raise AssertionError(
            f"no '+N vs MOAB-Class' special for {tower_id}:{code}: {stats.specials!r}"
        )

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
    # --- Projected running totals (stated start + range cash). The convention is
    # stated_start + range_cash, NOT cumulative-from-round-1; the stated start is
    # the constant in each case's user_message. (#1458 left these unanchored after
    # a naive round_cash(1, N) probe came up ~$10 short — the wrong accessor.) ---
    # BUG-0001 — "8094$ at round 60" → total at round 68.
    Anchor(
        "knowledge.btd6_round_cash_balance_bug_0001",
        "Standard rounds 60-68 projected total ($8094 start)",
        21187.90,
        _projected_total(8094, 60, 68),
    ),
    # By-round projection — "20K by round 50" → total by round 60.
    Anchor(
        "knowledge.btd6_round_cash_by_round_projection",
        "Standard rounds 50-60 projected total ($20000 start)",
        39840.0,
        _projected_total(20000, 50, 60),
    ),
    # BUG-0004 — "26932 at the end of r53" → total at r70.
    Anchor(
        "knowledge.btd6_round_cash_r_shorthand_bug_0004",
        "Standard rounds 54-70 projected total ($26932 start)",
        56318.70,
        _projected_total(26932, 54, 70),
    ),
    # BUG-0010 — "started with 5443" in ABR → total over ABR rounds 25-83.
    Anchor(
        "knowledge.btd6_abr_range_cash_bug_0010",
        "ABR rounds 25-83 projected total ($5443 start)",
        119315.30,
        _projected_total(5443, 25, 83, "abr"),
    ),
    # --- #855 Layer A — Bomb Shooter middle-path MOAB-Class bonuses. The grounding
    # case asserts the answer AFFIRMS +15 / +30 / +99 (MOAB Mauler / Assassin /
    # Eliminator); pin each to the committed tier stats so a re-seed that changed a
    # bonus fails CI instead of leaving the case testing a stale truth. ---
    Anchor(
        "grounding.btd6_bomb_middle_path_moab_855",
        "MOAB Mauler (0-3-0) bonus vs MOAB-Class",
        15.0,
        _moab_class_bonus("bomb_shooter", "030"),
    ),
    Anchor(
        "grounding.btd6_bomb_middle_path_moab_855",
        "MOAB Assassin (0-4-0) bonus vs MOAB-Class",
        30.0,
        _moab_class_bonus("bomb_shooter", "040"),
    ),
    Anchor(
        "grounding.btd6_bomb_middle_path_moab_855",
        "MOAB Eliminator (0-5-0) bonus vs MOAB-Class",
        99.0,
        _moab_class_bonus("bomb_shooter", "050"),
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
# Fixture-drift anchors — the BTD6 *grounding* cases use ``contains(...)`` graders
# with their truth baked into the ``tool_results`` FIXTURE (the canned tool reply),
# not an ``llm_judge`` rubric. The rubric-number anchors above never see those, so
# the fixture numbers had no data-drift guard at all: a re-seed that changed
# Navarch's income or a paragon cost would leave the eval silently testing against
# a stale fixture. These anchors close the same two directions for the fixture
# cases — data drift (the number must come back from the dataset) and fixture drift
# (the number must still appear in the named case's fixture).
# --------------------------------------------------------------------------- #
def _fixture_numbers(case: object, tool_name: str) -> set[float]:
    """All numeric tokens in ``case``'s ``tool_results`` facts for ``tool_name``.

    Mirrors :func:`_rubric_numbers` but reads the canned tool reply (the
    ``facts`` list) instead of an ``llm_judge`` rubric, normalizing ``$`` and
    thousands separators so "3,200" and "3200" compare equal."""
    payload = getattr(case, "tool_results", {}).get(tool_name, {})
    facts = payload.get("facts", ()) if isinstance(payload, dict) else ()
    nums: set[float] = set()
    for fact in facts:
        for token in _NUMBER_RE.findall(str(fact)):
            cleaned = token.replace("$", "").replace(",", "")
            try:
                nums.add(round(float(cleaned), 2))
            except ValueError:  # pragma: no cover - regex guarantees a number
                continue
    return nums


def _navarch_income() -> float:
    stats = btd6_stats_service.get_paragon_stats("navarch_of_the_seas")
    assert stats is not None, "navarch_of_the_seas paragon stats missing"
    assert stats.income_per_round is not None, "navarch income_per_round missing"
    return float(stats.income_per_round)


def _navarch_cost() -> float:
    stats = btd6_stats_service.get_paragon_stats("navarch_of_the_seas")
    assert stats is not None, "navarch_of_the_seas paragon stats missing"
    assert stats.cost is not None, "navarch paragon cost missing"
    return float(stats.cost)


@dataclass(frozen=True)
class FixtureAnchor:
    case_id: str
    tool_name: str
    label: str
    expected: float  # the truth baked into the case fixture (the bridge value)
    derive: Callable[[], float]  # re-derivation from btd6_stats_service


FIXTURE_ANCHORS: tuple[FixtureAnchor, ...] = (
    # The 2026-06-10 "no coins" Navarch miss (PR #662): the income fact that now
    # grounds the answer is baked into the grounding-case fixtures via contains().
    FixtureAnchor(
        "grounding.btd6_navarch_income",
        "btd6_lookup",
        "Navarch income per round (navarch case fixture)",
        3200.0,
        _navarch_income,
    ),
    FixtureAnchor(
        "grounding.btd6_navarch_income",
        "btd6_lookup",
        "Navarch paragon cost (navarch case fixture)",
        550000.0,
        _navarch_cost,
    ),
    # The pronoun-followup turn (PR #668) carries the same income fact forward.
    FixtureAnchor(
        "grounding.btd6_carryover_followup",
        "btd6_lookup",
        "Navarch income per round (carryover case fixture)",
        3200.0,
        _navarch_income,
    ),
)


def test_fixture_anchor_table_references_only_real_cases():
    """A stale fixture anchor (renamed/removed case) is itself drift — fail loudly."""
    missing = sorted({a.case_id for a in FIXTURE_ANCHORS} - set(_CASES_BY_ID))
    assert not missing, (
        f"Fixture anchor(s) reference eval case id(s) that no longer exist: {missing}. "
        "Update tests/evals/test_btd6_grounding_anchors.py to the current case ids."
    )


@pytest.mark.parametrize(
    "anchor", FIXTURE_ANCHORS, ids=lambda a: f"{a.case_id}:{a.label}"
)
def test_fixture_number_is_reproduced_by_the_dataset(anchor: FixtureAnchor):
    """Direction 1 — data drift: the fixture value must come back from the data."""
    derived = round(anchor.derive(), 2)
    assert derived == round(anchor.expected, 2), (
        f"{anchor.label}: dataset now yields {derived}, but the grounding-case "
        f"fixture bakes {anchor.expected}. The BTD6 data drifted from the eval "
        f"fixture — re-sync the case fixture (and this anchor) to the data, or fix "
        f"the data."
    )


@pytest.mark.parametrize(
    "anchor", FIXTURE_ANCHORS, ids=lambda a: f"{a.case_id}:{a.label}"
)
def test_fixture_number_appears_in_the_case_fixture(anchor: FixtureAnchor):
    """Direction 2 — fixture drift: the bridge value must be in the case fixture."""
    case = _CASES_BY_ID[anchor.case_id]
    baked = _fixture_numbers(case, anchor.tool_name)
    assert round(anchor.expected, 2) in baked, (
        f"{anchor.label}: {anchor.expected} is grounded in the data but not present "
        f"in the {anchor.tool_name!r} fixture of {anchor.case_id!r}. The fixture was "
        f"edited away from the grounded truth (fixture numbers: {sorted(baked)})."
    )


def test_fixture_introspection_actually_reads_a_known_number():
    """Guard the guard: a fixture case whose canned facts assert a number must
    surface it, so a silently-broken extractor can't make the checks above
    vacuous."""
    case = _CASES_BY_ID["grounding.btd6_navarch_income"]
    assert 3200.0 in _fixture_numbers(case, "btd6_lookup")


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


# --------------------------------------------------------------------------- #
# Anchor-coverage report — every *significant* number a BTD6 case asserts must
# be accounted for: either it is anchored (an Anchor/FixtureAnchor re-derives it)
# or it is on the curated allowlist below (a distractor the rubric tells the judge
# to REJECT, or a user-supplied input restated in the rubric). A rubric/fixture
# edit that introduces a NEW dollar/HP *truth* without anchoring it then fails CI
# here, instead of silently leaving an un-guarded "truth" the eval grades against.
#
# Why a significance threshold: a rubric is full of structural small integers —
# round numbers (60, 68, 25, 83), boss tiers (1-5), crosspath digits (0/4/1), the
# "6" in "BTD6", the "2" in "multiply by 2". None of those are data-derived truths,
# and listing them would drown the real figures in noise (the #1458 "so it isn't
# noisy" requirement). Every actual asserted truth/distractor/input in these
# economy + HP cases is >= $1,000 (smallest real truth: Navarch's $3,200 income),
# so the threshold cleanly separates the figures worth accounting for from the
# structural noise. Sub-$1,000 asserted truths are rare in this domain and fall
# outside this report by design (documented, tunable via _SIGNIFICANCE_THRESHOLD).
# --------------------------------------------------------------------------- #
_SIGNIFICANCE_THRESHOLD = 1000.0

# Every BTD6 case id this coverage report governs (the knowledge.* / grounding.*
# BTD6 cases). Derived from the case list so a new BTD6 case is automatically in
# scope (and a structural rename is caught by the real-case guard below).
_BTD6_CASE_IDS: tuple[str, ...] = tuple(
    cid
    for cid in _CASES_BY_ID
    if cid.startswith("knowledge.btd6") or cid.startswith("grounding.btd6")
)

# Significant non-anchored numbers, per case, each with WHY it is not anchored.
# Two allowed reasons (the #1458 spec): a *distractor* (the rubric rejects it) or
# a *user-input* (a figure the prompt supplies, restated in the rubric — not a
# data-derived truth, so a data-drift guard over it would be meaningless). A value
# here that becomes a real derivable truth should move to ANCHORS instead.
_UNANCHORED_ALLOWLIST: dict[str, dict[float, str]] = {
    "knowledge.btd6_round_cash_by_round_projection": {
        20000.0: "user-input: the stated starting cash ('20K by round 50')",
    },
    "knowledge.btd6_round_cash_r_shorthand_bug_0004": {
        26932.0: "user-input: the stated cash held after r53",
        71315.2: "distractor: BUG-0004 from-round-1 cumulative mislabel (truth $56,318.70)",
    },
    "knowledge.btd6_abr_range_cash_bug_0010": {
        5443.0: "user-input: the stated starting cash ('started with 5443')",
        107164.6: "distractor: BUG-0010 standard-set range given as the ABR answer",
    },
    "knowledge.btd6_elite_lych_hp_bug_0002": {
        14000.0: "distractor: STANDARD Lych T1 HP presented as the elite value",
        52500.0: "distractor: STANDARD Lych T2 HP presented as the elite value",
        220000.0: "distractor: STANDARD Lych T3 HP presented as the elite value",
        525000.0: "distractor: STANDARD Lych T4 HP presented as the elite value",
        2100000.0: "distractor: STANDARD Lych T5 HP presented as the elite value",
    },
    "knowledge.btd6_despo_bulk_cost_bug_0003": {
        10041.0: "distractor: '10 041' misread as the quantity 10,041 (truth: ten 0-4-1)",
    },
}


def _case_numbers(case: object) -> set[float]:
    """All numeric tokens a case asserts — rubric numbers plus every fixture
    number across its ``tool_results`` (the two places a truth can be baked)."""
    nums = set(_rubric_numbers(getattr(case, "grader", None)))
    for tool_name in getattr(case, "tool_results", {}) or {}:
        nums |= _fixture_numbers(case, tool_name)
    return nums


def _significant_numbers(case: object) -> set[float]:
    """The case's asserted numbers worth accounting for (>= the threshold)."""
    return {n for n in _case_numbers(case) if n >= _SIGNIFICANCE_THRESHOLD}


def _anchored_numbers(case_id: str) -> set[float]:
    """Every number anchored for ``case_id`` (Anchor + FixtureAnchor)."""
    return {round(a.expected, 2) for a in ANCHORS if a.case_id == case_id} | {
        round(a.expected, 2) for a in FIXTURE_ANCHORS if a.case_id == case_id
    }


def test_btd6_case_scope_is_non_empty():
    """Guard the guard: the BTD6 case-id scope must actually match cases, so a
    case-id convention change can't silently empty the whole coverage report."""
    assert _BTD6_CASE_IDS, (
        "no knowledge.btd6*/grounding.btd6* eval cases matched — the coverage "
        "report would be vacuous; update _BTD6_CASE_IDS to the current convention."
    )


def test_anchor_coverage_allowlist_references_only_real_cases():
    """A stale allowlist entry (renamed/removed case) is itself drift — fail loudly."""
    missing = sorted(set(_UNANCHORED_ALLOWLIST) - set(_CASES_BY_ID))
    assert not missing, (
        f"Coverage allowlist references eval case id(s) that no longer exist: "
        f"{missing}. Update _UNANCHORED_ALLOWLIST to the current case ids."
    )


@pytest.mark.parametrize("case_id", _BTD6_CASE_IDS)
def test_every_significant_btd6_number_is_anchored_or_allowlisted(case_id: str):
    """Coverage: every >= $1,000 figure a BTD6 case asserts is either anchored
    (re-derived from the dataset) or an explicitly allowlisted distractor / input.

    An un-accounted-for figure is the failure this exists to catch — a rubric or
    fixture edit that introduced a new dollar/HP *truth* the golden set now grades
    against with nothing re-deriving it. Resolve it by adding an Anchor (if it is a
    derivable truth) or an _UNANCHORED_ALLOWLIST entry (a distractor / user-input)."""
    case = _CASES_BY_ID[case_id]
    significant = _significant_numbers(case)
    accounted = _anchored_numbers(case_id) | set(_UNANCHORED_ALLOWLIST.get(case_id, {}))
    unaccounted = sorted(significant - accounted)
    assert not unaccounted, (
        f"{case_id}: significant asserted number(s) {unaccounted} are neither "
        f"anchored nor allowlisted. Add an Anchor (if derivable from the dataset) "
        f"or an _UNANCHORED_ALLOWLIST entry (distractor / user-input). "
        f"(significant={sorted(significant)}, anchored={sorted(_anchored_numbers(case_id))})"
    )


@pytest.mark.parametrize("case_id", sorted(_UNANCHORED_ALLOWLIST))
def test_allowlisted_numbers_are_present_and_unanchored(case_id: str):
    """No dead allowlist entries: each allowlisted number must still be asserted by
    its case AND not already anchored (else it belongs in ANCHORS, not here). Stops
    the allowlist from silently masking a number a later edit removed or anchored."""
    significant = _significant_numbers(_CASES_BY_ID[case_id])
    anchored = _anchored_numbers(case_id)
    for value, reason in _UNANCHORED_ALLOWLIST[case_id].items():
        assert value in significant, (
            f"{case_id}: allowlisted {value} ({reason}) is no longer a significant "
            f"asserted number — remove the stale allowlist entry. "
            f"(significant={sorted(significant)})"
        )
        assert value not in anchored, (
            f"{case_id}: allowlisted {value} ({reason}) is also anchored — drop the "
            f"allowlist entry; the Anchor already accounts for it."
        )


# --------------------------------------------------------------------------- #
# Distractor negative-anchors — the inverse of the truth anchors above. A BTD6
# case earns its keep by REJECTING a specific wrong number; the case only stays
# discriminating while that wrong number stays *wrong*. A data re-seed that made a
# distractor coincide with the truth would silently gut the case (the wrong answer
# becoming a right one) with nothing to notice. These pin that each documented
# distractor stays distinct from the truth(s) the case asserts — and, where the
# distractor is itself a derivable *wrong computation* (a right calculation on the
# wrong roundset), that it keeps reproducing exactly, so the confusion the case
# guards against stays a real, live confusion.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DistractorNegativeAnchor:
    case_id: str
    distractor: float  # the number the rubric tells the judge to REJECT
    reason: str  # where the distractor comes from / why it tempts the model
    must_differ_from: tuple[Callable[[], float], ...]  # truths it must NOT equal
    derive_alias: Callable[[], float] | None = None  # the wrong computation it IS


DISTRACTOR_NEGATIVE_ANCHORS: tuple[DistractorNegativeAnchor, ...] = (
    # BUG-0004 — "$71,315.20" was the model's from-round-1 cumulative mislabel.
    # It is NOT cleanly derivable (the actual cumulative rounds 1-70 is $70,665.20),
    # so it has no alias; the guard pins that it stays distinct from BOTH truths the
    # case asserts (the $29,386.70 range AND the $56,318.70 projected total).
    DistractorNegativeAnchor(
        "knowledge.btd6_round_cash_r_shorthand_bug_0004",
        71315.2,
        "BUG-0004 from-round-1 cumulative mislabel presented as the user's total",
        (_range_cash(54, 70), _projected_total(26932, 54, 70)),
    ),
    # BUG-0010 — "$107,164.60" is the STANDARD-set range over rounds 25-83 given as
    # the ABR answer. It IS a derivable wrong computation (right range, wrong
    # roundset), so the alias pins it to the standard range, and must_differ_from
    # pins it apart from the real ABR truth ($113,872.30).
    DistractorNegativeAnchor(
        "knowledge.btd6_abr_range_cash_bug_0010",
        107164.6,
        "BUG-0010 standard-set range over r25-83 given as the ABR answer",
        (_range_cash(25, 83, "abr"),),
        derive_alias=_range_cash(25, 83, "default"),
    ),
    # BUG-0002 — the STANDARD Lych per-tier HP presented as the ELITE values. Each
    # standard tier must stay strictly below (i.e. distinct from) its elite tier, or
    # the "standard given as elite" confusion the case rejects would evaporate.
    DistractorNegativeAnchor(
        "knowledge.btd6_elite_lych_hp_bug_0002",
        14000.0,
        "standard Lych T1 HP presented as the elite value",
        (_elite_lych_tier(1),),
    ),
    DistractorNegativeAnchor(
        "knowledge.btd6_elite_lych_hp_bug_0002",
        52500.0,
        "standard Lych T2 HP presented as the elite value",
        (_elite_lych_tier(2),),
    ),
    DistractorNegativeAnchor(
        "knowledge.btd6_elite_lych_hp_bug_0002",
        220000.0,
        "standard Lych T3 HP presented as the elite value",
        (_elite_lych_tier(3),),
    ),
    DistractorNegativeAnchor(
        "knowledge.btd6_elite_lych_hp_bug_0002",
        525000.0,
        "standard Lych T4 HP presented as the elite value",
        (_elite_lych_tier(4),),
    ),
    DistractorNegativeAnchor(
        "knowledge.btd6_elite_lych_hp_bug_0002",
        2100000.0,
        "standard Lych T5 HP presented as the elite value",
        (_elite_lych_tier(5),),
    ),
)


def test_distractor_negative_anchor_table_references_only_real_cases():
    """A stale negative anchor (renamed/removed case) is itself drift — fail loudly."""
    missing = sorted({a.case_id for a in DISTRACTOR_NEGATIVE_ANCHORS} - set(_CASES_BY_ID))
    assert not missing, (
        f"Distractor negative anchor(s) reference eval case id(s) that no longer "
        f"exist: {missing}. Update DISTRACTOR_NEGATIVE_ANCHORS to the current ids."
    )


@pytest.mark.parametrize(
    "anchor", DISTRACTOR_NEGATIVE_ANCHORS, ids=lambda a: f"{a.case_id}:{a.distractor}"
)
def test_distractor_stays_distinct_from_the_truth(anchor: DistractorNegativeAnchor):
    """The core negative guard: the rejected number must not equal any truth the
    case asserts. If a data re-seed collapses the gap, the case stops discriminating
    and this fails — surfacing the silent loss instead of letting the eval pass a
    now-correct 'wrong' answer."""
    for derive in anchor.must_differ_from:
        truth = round(derive(), 2)
        assert round(anchor.distractor, 2) != truth, (
            f"{anchor.case_id}: distractor {anchor.distractor} ({anchor.reason}) now "
            f"equals a derived truth ({truth}). The data drifted so the case's "
            f"'wrong' answer is now correct — the case no longer discriminates. "
            f"Re-examine the case and the dataset."
        )


@pytest.mark.parametrize(
    "anchor", DISTRACTOR_NEGATIVE_ANCHORS, ids=lambda a: f"{a.case_id}:{a.distractor}"
)
def test_distractor_is_still_rejected_by_the_rubric(anchor: DistractorNegativeAnchor):
    """The distractor must still be named in the case's rubric — a rubric edit that
    dropped the explicit rejection would leave the negative anchor guarding a
    confusion the golden set no longer tests."""
    asserted = _rubric_numbers(_CASES_BY_ID[anchor.case_id].grader)
    assert round(anchor.distractor, 2) in asserted, (
        f"{anchor.case_id}: distractor {anchor.distractor} ({anchor.reason}) is no "
        f"longer present in the rubric — the case stopped rejecting it. Re-add the "
        f"rejection or remove this negative anchor (rubric numbers: {sorted(asserted)})."
    )


@pytest.mark.parametrize(
    "anchor",
    [a for a in DISTRACTOR_NEGATIVE_ANCHORS if a.derive_alias is not None],
    ids=lambda a: f"{a.case_id}:{a.distractor}",
)
def test_distractor_alias_reproduces_the_wrong_computation(
    anchor: DistractorNegativeAnchor,
):
    """For a distractor that IS a derivable wrong computation (right calc, wrong
    roundset), pin that it keeps reproducing — so the documented confusion stays a
    live, exactly-reproducible one and a data change to the wrong-roundset figure is
    noticed rather than silently making the distractor stop matching."""
    assert anchor.derive_alias is not None  # narrowed by the parametrize filter
    derived = round(anchor.derive_alias(), 2)
    assert derived == round(anchor.distractor, 2), (
        f"{anchor.case_id}: the wrong computation behind distractor "
        f"{anchor.distractor} ({anchor.reason}) now yields {derived}. The distractor "
        f"no longer reproduces from the dataset — re-derive it or update the case."
    )
