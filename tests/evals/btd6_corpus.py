"""BTD6 QA accuracy corpus — the machine-readable half of
``docs/btd6/qa-accuracy-corpus-2026-06-27.md``.

One shared table (:data:`GROUNDING_PROBES`) feeds two layers, both keyed off the
bot's REAL retrieval so a pass means the *bot's own* facts answer the question —
not that a model can answer from perfect hand-fed context:

* ``test_btd6_qa_corpus.py`` — the **offline**, deterministic, creds-free layer.
  For each question it asserts the answer-bearing fact is actually grounded by
  ``btd6_context_service.build`` (``expect``) and the known wrong claim is not
  (``forbid``). This is the trustworthy "test all these questions at once" check:
  real retrieval pipeline, no API keys, runs on every PR.

* ``btd6_live_path.run_btd6_live_suite`` (via ``scripts/run_evals.py --btd6``) —
  the **live** layer. It replays each question through the REAL production answer
  path (router → grounding → instruction assembly → gateway → faithfulness guard)
  and grades the reply, so a result is what a live Discord user would get.

Grow both from real misses: when a BTD6 answer is reported wrong, add a probe.
"""

from __future__ import annotations

from dataclasses import dataclass


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


__all__ = ["GROUNDING_PROBES", "GroundingProbe"]
