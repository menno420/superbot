"""BTD6 QA accuracy corpus — the machine-readable half of
``docs/btd6/qa-accuracy-corpus-2026-06-27.md``.

Two layers, both keyed off the SAME real grounding the production AI path uses
(``services.btd6_context_service.build``), so a pass means the *bot's own*
retrieved facts answer the question — not that a model can answer from perfect
hand-fed context:

* :data:`GROUNDING_PROBES` + ``test_btd6_qa_corpus.py`` — the **offline**,
  deterministic, creds-free layer. For each question it asserts the answer-bearing
  fact is actually grounded (``expect``) and the known wrong claim never is
  (``forbid``). This is the trustworthy "test all these questions at once" check:
  it runs the real retrieval pipeline, needs no API keys, and runs on every PR.

* :func:`live_cases` — the **live** layer for ``scripts/run_evals.py --btd6``
  (paid, opt-in). It injects each question's real ``build()`` facts into the
  model prompt (mirroring production, where facts enter the instruction stack)
  and grades the phrased answer. Same facts as the offline layer, so the only
  extra thing it tests is whether the model *phrases* a faithful answer.

Grow both from real misses: when a BTD6 answer is reported wrong, add a probe
here so it becomes a permanent regression.
"""

from __future__ import annotations

from dataclasses import dataclass

from tests.evals.graders import all_of, contains, not_contains
from tests.evals.harness import EvalCase

from core.runtime.ai.contracts import AITask


@dataclass(frozen=True)
class GroundingProbe:
    """One corpus question + what its REAL grounding must / must not contain."""

    question: str
    # Substrings that must appear (case-insensitive) in the joined grounded
    # facts — the answer-bearing fact the bot retrieves for this question.
    expect: tuple[str, ...]
    # Substrings that must NOT appear — a known wrong claim (e.g. the live
    # screenshot's "lead resists glue"). Optional.
    forbid: tuple[str, ...] = ()
    note: str = ""


# Every probe's `expect` is a fact the curated data + the interaction layer
# ground deterministically (verified against the dump). These are the
# error-prone interaction questions from the live screenshots plus the core
# bloon/immunity facts. Numbers/immunities trace to the game-sourced dump.
GROUNDING_PROBES: tuple[GroundingProbe, ...] = (
    # --- the live screenshot misses ------------------------------------------
    GroundingProbe(
        question="can glue strike and avenger deal with DDTs",
        expect=("lead does not resist glue", "moab glue", "status effect"),
        forbid=("lead resists glue", "lead is immune to glue"),
        note="screenshot #2 — the 'Lead resists glue' hallucination",
    ),
    GroundingProbe(
        question="can ice monkey slow ddts",
        expect=("cold", "lead", "cold snap"),
        note="screenshot #3 — ice is cold-based, blocked by lead; Cold Snap fixes it",
    ),
    GroundingProbe(
        question="does glue work on lead bloons",
        expect=("lead does not resist glue",),
        forbid=("lead resists glue",),
    ),
    # --- damage-type interactions --------------------------------------------
    GroundingProbe(
        question="what damage can pop lead bloons",
        expect=("needs explosion, fire, plasma, glacier, acid",),
        note="the lead pop-guide 'needs' clause is grounded",
    ),
    GroundingProbe(
        question="can you pop purple bloons with plasma",
        expect=("energy, plasma, fire, and frigid damage cannot pop purple",),
    ),
    GroundingProbe(
        question="can a bomb shooter pop black bloons",
        expect=("explosion damage cannot pop black",),
    ),
    GroundingProbe(
        question="does sharp damage pop lead",
        expect=("sharp, shatter, cold, and energy damage cannot pop lead",),
    ),
    GroundingProbe(
        question="how do I deal with a DDT",
        expect=("camo detection", "fire, plasma, normal, acid, or glacier"),
        forbid=("ddts are immune to glue", "lead resists glue"),
    ),
    GroundingProbe(
        question="can glacier damage pop lead",
        expect=("unlike plain cold",),
        note="Glacier is the cold variant that DOES pop lead",
    ),
    # --- bloon immunities (game-sourced) -------------------------------------
    GroundingProbe(
        question="what is a DDT immune to",
        expect=("immune to sharp, shatter, cold, energy, explosion",),
    ),
    GroundingProbe(
        question="what is a zebra bloon immune to",
        expect=("explosion", "cold"),
        note="Zebra = Black + White → both",
    ),
    GroundingProbe(
        question="what is a purple bloon immune to",
        expect=("energy", "plasma", "fire"),
    ),
)


# --- live-eval grading rubrics (one per probe id, keyed by question) ---------
# The live model must state the same correct fact in prose. Kept lenient
# (contains/not_contains on the key token) so model phrasing variance doesn't
# cause false fails — the strict assertion is the offline grounding layer.
_LIVE_FORBID_GLOBAL = ("lead resists glue", "lead is immune to glue")


def _grounding_block(facts: list[str]) -> str:
    """Wrap real grounded facts the way the production instruction stack frames
    them: an untrusted-data block the model must answer FROM, not from memory.
    """
    body = "\n".join(facts) if facts else "(no grounded facts retrieved)"
    return (
        "You are SuperBot answering a Bloons TD 6 question. Answer ONLY from the "
        "grounded BTD6 facts below — do not add facts from memory, and if the "
        "facts do not cover it, say so. Keep it short.\n\n"
        "<grounded_btd6_facts>\n"
        f"{body}\n"
        "</grounded_btd6_facts>"
    )


async def live_cases() -> list[EvalCase]:
    """Build live EvalCases whose grounding is the REAL ``build()`` output.

    Async because it calls the production grounding pipeline once per probe.
    Each case grades the model's phrased answer with lenient contains/not_contains
    over the same expect/forbid the offline layer asserts — so the live layer
    tests *phrasing faithfulness given the real facts*, nothing hand-fed.
    """
    from services import btd6_context_service

    cases: list[EvalCase] = []
    for i, probe in enumerate(GROUNDING_PROBES):
        ctx = await btd6_context_service.build(probe.question)
        graders = [contains(s) for s in probe.expect[:1]]  # at least the headline fact
        graders += [not_contains(s) for s in (*probe.forbid, *_LIVE_FORBID_GLOBAL)]
        cases.append(
            EvalCase(
                id=f"btd6_corpus.{i:02d}",
                category="btd6_grounding",
                user_message=probe.question,
                task=AITask.GENERAL_NL_ANSWER,
                system_prompt=_grounding_block(list(ctx.facts)),
                grader=all_of(*graders),
                max_output_tokens=400,
            ),
        )
    return cases


__all__ = ["GROUNDING_PROBES", "GroundingProbe", "live_cases"]
