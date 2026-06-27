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
    """One corpus question + how to judge it at each layer.

    ``expect``/``forbid`` grade the OFFLINE layer (substrings of the grounded
    *facts*, whose wording we control). ``rubric``/``forbid`` grade the LIVE
    layer (the model's *paraphrased* answer, judged semantically) — a live answer
    states the right thing in its own words, so substring-matching the fact text
    against it gives false negatives.
    """

    question: str
    # Substrings that must appear (case-insensitive) in the joined grounded
    # facts — the answer-bearing fact the bot retrieves for this question.
    expect: tuple[str, ...]
    # The correctness criterion for the LIVE model answer (LLM-as-judge rubric).
    rubric: str = ""
    # Substrings that must NOT appear — a known wrong claim (e.g. the live
    # screenshot's "lead resists glue"). Checked at BOTH layers.
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
        rubric=(
            "Must say glue is a STATUS effect that ignores damage-type immunity "
            "(so Lead does NOT resist glue), and that affecting MOAB-class bloons "
            "like DDTs needs MOAB Glue. It may also note Glue Strike only debuffs "
            "/ doesn't pop. PASS as long as it never claims Lead resists/blocks "
            "glue."
        ),
        forbid=("lead resists glue", "lead is immune to glue"),
        note="screenshot #2 — the 'Lead resists glue' hallucination",
    ),
    GroundingProbe(
        question="can ice monkey slow ddts",
        expect=("cold", "lead", "cold snap"),
        rubric=(
            "Must say base Ice Monkey CANNOT slow/freeze DDTs because its effect "
            "is Cold-based and blocked by the Lead property, AND name a crosspath "
            "that fixes it (Cold Snap, or Embrittlement). Failing to name the "
            "crosspath fix is a FAIL."
        ),
        note="screenshot #3 — ice is cold-based, blocked by lead; Cold Snap fixes it",
    ),
    GroundingProbe(
        question="does glue work on lead bloons",
        expect=("lead does not resist glue",),
        rubric=(
            "Must answer YES — glue works on Lead bloons because glue is a status "
            "effect that ignores damage-type immunity. FAIL if it says Lead "
            "resists or is immune to glue."
        ),
        forbid=("lead resists glue",),
    ),
    # --- damage-type interactions --------------------------------------------
    GroundingProbe(
        question="what damage can pop lead bloons",
        expect=("needs explosion, fire, plasma, glacier, acid",),
        rubric=(
            "Must list damage types that pop Lead — Explosion, Fire, Plasma, "
            "Glacier, Acid, and/or Normal — and NOT offer Sharp, Cold, Shatter, "
            "or Energy as able to pop Lead."
        ),
        note="the lead pop-guide 'needs' clause is grounded",
    ),
    GroundingProbe(
        question="can you pop purple bloons with plasma",
        expect=("energy, plasma, fire, and frigid damage cannot pop purple",),
        rubric="Must answer NO — Purple bloons are immune to Plasma damage.",
    ),
    GroundingProbe(
        question="can a bomb shooter pop black bloons",
        expect=("explosion damage cannot pop black",),
        rubric=(
            "Must answer NO — a base Bomb Shooter deals Explosion damage, which "
            "is blocked by the Black property."
        ),
    ),
    GroundingProbe(
        question="does sharp damage pop lead",
        expect=("sharp, shatter, cold, and energy damage cannot pop lead",),
        rubric="Must answer NO — Lead bloons are immune to Sharp damage.",
    ),
    GroundingProbe(
        question="how do I deal with a DDT",
        expect=("camo detection", "fire, plasma, normal, acid, or glacier"),
        rubric=(
            "Must say a DDT needs CAMO DETECTION plus a damage type that is not "
            "blocked by Lead+Black — i.e. Fire, Plasma, Normal, Acid, or Glacier "
            "(NOT Sharp, Cold, Energy, or Explosion). PASS if it conveys the "
            "camo-detection + non-blocked-damage requirement, even without naming "
            "specific towers."
        ),
        forbid=("ddts are immune to glue", "lead resists glue"),
    ),
    GroundingProbe(
        question="can glacier damage pop lead",
        expect=("unlike plain cold",),
        rubric=(
            "Must answer YES — Glacier damage CAN pop Lead bloons. (Noting that "
            "plain Cold cannot is a plus but not required for a pass.)"
        ),
        note="Glacier is the cold variant that DOES pop lead",
    ),
    # --- bloon immunities (game-sourced) -------------------------------------
    GroundingProbe(
        question="what is a DDT immune to",
        expect=("immune to sharp, shatter, cold, energy, explosion",),
        rubric=(
            "Must state a DDT is immune to Sharp, Shatter, Cold, Energy, and "
            "Explosion damage (it has Lead + Black). Naming all five is required; "
            "omitting one is a FAIL."
        ),
    ),
    GroundingProbe(
        question="what is a zebra bloon immune to",
        expect=("explosion", "cold"),
        rubric=(
            "Must state a Zebra bloon is immune to BOTH Explosion AND Cold "
            "damage (Black + White). Naming only one is a FAIL."
        ),
        note="Zebra = Black + White → both",
    ),
    GroundingProbe(
        question="what is a purple bloon immune to",
        expect=("energy", "plasma", "fire"),
        rubric=(
            "Must state a Purple bloon is immune to Energy, Plasma, and Fire "
            "damage (Frigid too is acceptable). Missing any of Energy/Plasma/Fire "
            "is a FAIL."
        ),
    ),
    # --- regression probes for prior fixed live misses -----------------------
    # Each pins the answer-bearing fact for a documented owner-reported bug so a
    # data/retrieval regression of the fix is caught offline on every PR. Themes
    # beyond damage-type interactions (paragon degree, paragon existence, entity
    # shorthand, boss HP) — see docs/btd6/qa-accuracy-corpus-2026-06-27.md.
    GroundingProbe(
        question="what is the damage of a d67 dart paragon",
        expect=("apex plasma master at degree 67", "not an upgrade-path code"),
        rubric=(
            "Must treat 'd67' as the paragon's DEGREE (1-100) and give the Apex "
            "Plasma Master's Degree-67 stats (~48 dmg). FAIL if it reads 'd67' as "
            "an upgrade path '0-6-7' or claims it can't exist because tiers cap at 5."
        ),
        forbid=("0-6-7",),
        note="BUG-0015 — 'd67' is the paragon DEGREE, not a 0-6-7 upgrade-path code",
    ),
    GroundingProbe(
        question="does the monkey buccaneer have a paragon",
        expect=("navarch of the seas",),
        rubric=(
            "Must answer YES and name Navarch of the Seas as the Monkey "
            "Buccaneer's paragon. FAIL if it claims the Monkey Buccaneer has no "
            "paragon."
        ),
        forbid=("no paragon", "does not have a paragon", "doesn't have a paragon"),
        note=(
            "absence-claim repro (absence-guard design doc Update 2) — the false "
            "'Monkey Buccaneer has no paragon' that the committed data grounds against"
        ),
    ),
    GroundingProbe(
        question="how much is a despo on impoppable",
        expect=("desperado", "impoppable $360"),
        rubric=(
            "Must identify and price the Desperado (a Primary-category tower; "
            "Impoppable base $360), resolving the 'despo' shorthand correctly. "
            "FAIL if it answers about the Plasma Monkey Fan Club (PMFC) or any "
            "other tower."
        ),
        forbid=("plasma monkey fan club", "pmfc"),
        note="BUG-0003 — 'despo'/'despos' shorthand resolves to Desperado, not PMFC",
    ),
    GroundingProbe(
        question="what is the health of an elite lych",
        expect=("elite lych per-tier health", "30,000 hp"),
        rubric=(
            "Must give the ELITE Lych health from the Elite table (T1 30,000 HP "
            "up to T5 24,000,000 HP), NOT the Standard table (T1 14,000 HP). FAIL "
            "if it serves Standard HP as Elite."
        ),
        note="BUG-0002 — Elite boss HP comes from the Elite table, not the Standard one",
    ),
)


__all__ = ["GROUNDING_PROBES", "GroundingProbe"]
