# 2026-06-27 — BTD6: revert the auto-derived DDT counter list (it grounded wrong towers)

> **Status:** `complete`

**Run type:** owner-directed (owner live-tested #1492 and reported 3 wrong recommendations)

## What this run did

The owner live-tested the #1492 DDT counter-tower list in production and found it **wrong**:

1. **Ice Monkey 2-0-0** — base ice can't damage MOAB-class, and a DDT *is* MOAB-class (needs Embrittlement
   4-x-x). The list recommended a tower that literally can't hit a DDT.
2. **Monkey Ace 0-2-5** — its explosions can't pop Black (DDT has Black).
3. **Sniper 0-4-0** — a weak config; the real answers are 2-4-0 / 2-5-0 / 4-2-0 / 5-2-0.

**Root cause:** "can damage a DDT" needs (a) MOAB-class targeting and (b) config quality, and the
committed stats encode **neither** — I confirmed Ice 2-0-0 and 4-0-0 have byte-identical projectiles; the
only "can hit MOAB-class" signal is Embrittlement's *description text*. So the primary-attack damage-type
derivation is **unsound** for this. Grounding it ground misinformation, which is worse than refusing.

**Revert + correct curation:**
- Removed `towers_that_can_damage` / `CounterHit` / `_primary_attack` from `btd6_capability_service` and
  the `_counter_fact` wiring from `btd6_interaction_service` (+ their tests).
- Replaced it with **correct curated prose** in the DDT pop-guide note (`damage_types.json`): a DDT is
  MOAB-class, so a counter needs camo + a non-resisted damage type **AND** the ability to hit MOAB-class —
  base Ice (until Embrittlement) and Glue (until MOAB Glue 0-0-3) cannot. This captures the owner's Ice
  correction as real knowledge.
- Updated the corpus doc with the lesson + the open question.

The damage-type **rules** grounding (camo + non-resisted type) stays — it is correct. The bot no longer
auto-lists specific counter towers (the part that was wrong).

CI: `check_quality --check-only` green, arch 0 errors, mypy clean, 1719 btd6 tests pass.

## ⚑ Self-initiated

None — owner-reported bug; this is the fix.

## 💡 Session idea (Q-0089)

*A "derivation confidence" convention: a data-derived BTD6 claim may only be grounded when every premise
is in the structured data — if any premise lives only in description text (like MOAB-class targeting),
the claim is curated prose, not auto-derived.* This run's bug was exactly an auto-derivation built on a
premise (MOAB-class capability) the data doesn't encode. Routed as an idea.

## ⟲ Previous-session review (Q-0102)

The #1492 run verified the *damage-type* premise carefully (owner + wiki confirmed Sniper) but shipped a
derivation resting on an *unverified* premise — that "primary attack pops lead+black+camo" ⇒ "can damage a
DDT" — without checking the MOAB-class requirement at all. Lesson applied: verify EVERY premise a derived
claim depends on, not just the one you happened to doubt. The owner's live test was the safety net that
caught it; the durable fix is the confidence convention above. Good that the damage-type rules were
separable and correct, so the revert kept the real value.

## 🧾 Doc audit (Q-0104)

`check_docs`/`check_consistency` green. The reverted feature + the lesson + the open owner question are
recorded in the corpus doc; the capability/interaction code carries revert-note comments. **Open owner
decision** (how to do tower recommendations) is surfaced to the owner in-chat for a call. Ledger: next
reconciliation pass.
