# 2026-06-27 — BTD6: ground VERIFIED DDT counter towers (fix the over-refusal)

> **Status:** `complete`

**Run type:** owner-directed (owner picked "enrich grounding" for the over-refusal finding)

## What this run did

The live eval (#1491) surfaced that "how do I deal with a DDT" **refuses**: the model names towers, the
faithfulness guard rejects them as ungrounded, and the deterministic refusal is served. Owner chose to
**enrich the grounding with verified tower recommendations** (keep the guard strong). Done — derived from
the dump, not freelanced.

**PR — verified DDT counter grounding.**

1. **`btd6_capability_service.towers_that_can_damage(bloon_id)`** — a tower can damage a bloon when some
   config's **PRIMARY** attack (`attacks[0].projectiles[0]`, read raw — `normal_stats` can pick a
   sub-attack, e.g. it reports the Ninja's caltrops as Normal while the main shuriken is Sharp) deals a
   damage type the bloon does NOT resist (`immune_to`, game-sourced) AND detects camo if the bloon is
   camo. Pure derivation, always matches the data.
2. **`btd6_interaction_service`** appends a grounded `[btd6_interaction] Towers whose attack can damage a
   DDT … : <list>` fact when the DDT pop-guide fires — so the model names **grounded** towers and the
   guard passes instead of refusing.
3. Tests: the capability **invariant** (every counter deals a non-resisted type + sees camo; canonical
   damage-dealers present) + the grounding test.

**Verification that mattered.** The first derivation (via `normal_stats`) flagged Sniper 0-4-0 and Ninja
0-0-3 as DDT-poppers — Ninja was a false positive (sub-attack), and Sniper looked wrong (I assumed only
Full Metal Jacket grants lead-popping). **The owner confirmed + the wiki confirmed the dump:** Supply
Drop / Elite Sniper (0-4-0+) main bullet IS Normal and pops Lead even without FMJ (the shrapnel is the
part that needs the 1-x-x crosspath). So the dump's per-tier damage types are reliable; reading the
PRIMARY projectile drops the false positives. Net DDT counter list: 13 towers, all verified
(Dart 0-0-5, Ice 2-0-0 Glacier, Super, Wizard, Spike Factory, Sniper, Dartling, Ace, Druid, Buccaneer,
Desperado, Mermonkey, + Monkey Village's Monkeyopolis attack — framed as a *capability* list, not a
ranking).

CI: `check_quality --check-only` green, arch 0 errors, mypy clean, 1566 btd6/capability/interaction/
context/tools tests pass.

## ⚑ Self-initiated

None unprompted — owner explicitly chose this fix path (the AskUserQuestion answer).

## 💡 Session idea (Q-0089)

*Generalize the counter grounding to the other "which tower?" bloons (camo-lead, the in-game Camo bloon)
behind the same `_COUNTER_BLOON_FOR` map.* The derivation is already general (`towers_that_can_damage`
takes any bloon id); only DDT is wired today. A one-line map extension would close the same over-refusal
on "what pops a camo lead" etc. Routed as an idea (DDT was the demonstrated case; widen once it's proven
live).

## ⟲ Previous-session review (Q-0102)

The grader-fix run (#1491) did the right thing reporting the over-refusal instead of silently patching it
— that surfaced the real question (enrich vs. loosen the guard) for an owner decision, and the owner
picked the safe path. What it could have done better: it could have *started* the capability derivation as
a proof-of-concept so the decision came with evidence ("here's the verified list we'd ground"). Lesson
applied here: when reporting a finding with fix options, prototype the recommended one far enough to show
it's sound (the derivation + the wiki-confirmed Sniper check) so the owner decides on evidence, not a
promise. The verify-before-grounding discipline (owner + wiki confirmed the dump) is exactly what kept a
plausible-but-wrong tower rec out of the data.

## 🧾 Doc audit (Q-0104)

`check_docs`/`check_consistency` green. The capability function + grounding are self-documenting
(docstrings); the corpus doc's DDT guidance still holds (the counter list augments it). No new owner
decision to route beyond the AskUserQuestion answer (recorded here). Ledger: next reconciliation pass.
