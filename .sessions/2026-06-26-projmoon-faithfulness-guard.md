# 2026-06-26 — Project Moon (Limbus) faithfulness guard (S1)

> **Status:** `in-progress`

## Goal (dispatch run, empty scheduled fire → advance the next plan slice)

Empty scheduled fire, **zero open PRs**. Per the routine: advance the next **▶ startable**
plan slice. The Project Moon knowledge-domain plan's ▶ Next item (b) is **the projmoon
faithfulness guard follow-up** — the §6 "hardest correctness risk". PR #1467 (Slice A item 2)
shipped the Limbus grounding *injection* path but deliberately deferred the prose-faithfulness
*validation* guard: a `PROJMOON_ANSWER` reply grounds on the injected facts but is **not**
verified against them the way `btd6_grounding_service.validate_btd6_reply` verifies BTD6 replies.
This slice closes that gap — offline-verifiable, default-preserving (only Limbus-detected
messages route to `PROJMOON_ANSWER`).

## Plan

1. New `disbot/services/projmoon_grounding_service.py` — `validate_projmoon_reply(reply, facts)`
   mirroring the BTD6 name-guard: reuse the domain-agnostic `utils.btd6.name_guard` matchers,
   index the **distinctive** Limbus proper names (the 12 Sinners + the E.G.O grade names),
   skip the common-English categories (Sins / damage types / statuses). Names-only — Limbus
   exact numbers aren't ingested yet (Slice A item 1).
2. Wire a `PROJMOON_ANSWER` faithfulness block into `natural_language_stage.py` parallel to the
   BTD6 one: reject → regenerate-once with a do-not-state constraint → floor to a deterministic
   projmoon refusal.
3. Offline unit tests (the guard logic + the name-index discipline + the wiring).

## Status checklist
- [ ] `projmoon_grounding_service` + name index + tests
- [ ] NL-stage `PROJMOON_ANSWER` guard wiring + deterministic refusal
- [ ] CI mirror green + arch strict 0 errors
- [ ] De-stale the project-moon plan + S1 sector doc
- [ ] Session enders (idea / prev-review / doc audit / run-report footer)
