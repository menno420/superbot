# 2026-06-27 — BTD6 QA accuracy: damage-type/status-effect interaction grounding + verified Q&A corpus

> **Status:** `in-progress`

**Run type:** owner-directed (session prompt + live Discord screenshots)

## What I'm about to do

Owner reports the bot still answers many BTD6 questions wrong (screenshots: Glue Strike / Avenger / DDT
thread). Root cause from probing: the data dump's bloon **immunities are correct**, but there is **no
grounding for damage-type ↔ bloon-property INTERACTION** — "can glue/ice/sharp deal with a DDT", "what
pops lead", "does X resist glue". The model is handed bloon immunities + tower descriptions separately
and invents the interaction rule (e.g. confidently said *"Lead resists glue"* — false; glue ignores
damage-type immunity, MOAB-class just needs MOAB Glue to be targeted).

Plan (one coherent PR):
1. Curated, wiki-verified `damage_types.json` — the 11 damage types + which properties block each, and
   a **status-effects** section (glue / slow / stun / freeze / knockback are NOT damage; how they
   interact with Lead / MOAB-class / BAD / Camo).
2. Loader + a new grounding pass in `btd6_context_service.build()` emitting `[btd6_damage_type]` /
   `[btd6_interaction]` facts for interaction questions.
3. Fix incomplete bloon prose (Lead "immune to Sharp" → all four; DDT description → all immunities).
4. A large **verified Q&A accuracy corpus** doc (the "big list of questions" the owner asked for), each
   with verified answer + wiki source.
5. Regression tests: grounding tests for the interaction facts + eval cases for the screenshot misses.

(Filling close-out enders + flipping this card to `complete` as the deliberate final step.)
