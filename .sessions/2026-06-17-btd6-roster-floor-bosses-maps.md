# 2026-06-17 — BTD6 answerability floor: boss roster + map filter + boss immunity

> **Status:** `complete`

## Arc

Scheduled dispatch fire, **empty work order**. The night queue
(`planning/night-queue-2026-06-16.md`) is **fully consumed** and both open PRs
(#941 image-mod, #929 security tiers) are `needs-hermes-review`-gated. So I took a
fresh slice of the proven, ungated, factory-pattern **BTD6 deterministic floor**
lane (Q-0048, closes the BUG-0009 wrong-assembly class). Found and closed three
genuine gaps in `disbot/services/btd6_context_service.py` (one PR, #1012).

## Shipped (PR #1012)

1. **Boss roster** — `deterministic_roster_reply` enumerated heroes/towers/
   paragons/maps but never bosses; "list all bosses" fell to the model, which can
   omit/add one of the 7. Added a `boss` branch (canonical + tagline).
2. **Per-difficulty map filter** — "list all expert maps" dumped all 86 maps
   grouped by difficulty instead of the 13 Expert ones. `_map_roster_reply` now
   detects a named tier (Beginner/Intermediate/Advanced/Expert) and filters.
3. **Boss damage-immunity floor** — new `deterministic_boss_immunity_reply` in
   `_BTD6_LIST_BUILDERS`, owning "what is Lych immune to" · "is Blastapopoulos
   immune to fire" · "which bosses are immune to fire" off `bosses[].immune_to`.
   Keyed on a boss reference **plus** an immunity cue, so it never overlaps the
   bloon immunity roster (bloon/blimp/moab subject, never "boss") — proven by the
   exclusivity invariant (new corpus phrase) + the pre-existing
   `is the lead bloon immune to sharp` / `what is the hp of elite lych per tier`
   defer cases.

`check_quality --full` green (10354 passed) · `check_architecture --mode strict`
0 errors · +9 tests (`test_btd6_boss_immunity.py` + exclusivity corpus + roster/
map-filter cases in `test_btd6_context_grounding.py`).

## Context delta

- **Needed and had:** the night-queue doc's "the seam is `_BTD6_LIST_BUILDERS` +
  the exclusivity invariant" pointer made the boss-immunity slice turn-key.
- **Saved by checking source:** `deterministic_roster_reply` *already* covered the
  tower-category roster (my first instinct for slice 1) — caught it before
  duplicating. The `do_not_create` discipline paid off; the real gaps were one
  layer deeper (bosses, map-difficulty filtering).
- **Reusable:** `_match_bloon_damage`'s keyword table already covers every boss
  damage type (Frigid/Shatter/Cold included), so the boss-immunity builder needed
  no new damage vocabulary.

## Flagged for maintainer

- None blocking. The ungated BTD6-floor lane is now thinning (most rosters
  covered) — the ▶ Next action note warns the next empty fire against inventing
  low-value floor builders to fill the queue (forced filler ≠ work) and lists the
  genuinely-uncovered candidates + the plan-first alternatives.

## 💡 Session idea (Q-0089)

A tiny `scripts/check_btd6_floor_coverage.py`: walk every entity file in
`disbot/data/btd6/*.json`, list which entity × question-shape (roster / cost-
compare / immunity / per-level) already has a `_BTD6_LIST_BUILDERS` builder, and
print the *uncovered* cells. This turns "is there a genuine gap left?" from prose
judgement (what I did by hand this session) into a deterministic map — so a future
empty fire either finds a real uncovered shape or sees the lane is exhausted and
takes a plan-first lane, instead of risking forced-filler builders. Sibling to the
`next_night_slice.py` / `dispatch_menu.py` dispatch-tooling family. Filed mentally
under that family; worth a `docs/ideas/` file if the lane keeps getting fired.

## ⟲ Previous-session review (Q-0102)

The previous run (#1011, the night-queue buffer slices) did the exclusivity
discipline well — every new builder added its corpus phrase and a defer case, so
the floor stayed mutually exclusive as it grew. What it (and the whole night-queue
arc) left thin is the same thing I hit: **the lane has no machine-checkable notion
of "what's still uncovered,"** so each fire re-derives it by reading data files +
grepping builders (I nearly duplicated the tower-category roster). **System
improvement:** the floor-coverage map above (today's session idea) is the durable
fix — it closes the same "what does an empty fire build?" gap the previous session
flagged about the *ready queue*, one level more concretely (per-entity, not
per-lane). Until then, the ▶ Next action note I added (warn against filler + list
real candidates) is the prose stopgap.

## Doc audit (Q-0104)

- Ledger: added the #1012 entry; left the pre-existing 6-PR ledger drift for the
  auto-reconciliation routine (Q-0124 — manual/dispatch sessions don't run recon).
- ▶ Next action repointed (night queue consumed → floor-lane status + filler
  warning + plan-first alternatives).
- No new owner decisions, no new docs to reach (`check_docs` green).

## 📤 Run report

- **Did:** closed three BUG-0009 wrong-assembly gaps in the BTD6 answerability
  floor (boss roster · map-difficulty filter · boss immunity) · **Outcome:** shipped
- **Shipped:** #1012 (read-only deterministic, Q-0048, auto-merges on green)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none — auto-deploys on merge (Q-0048, no prod-check)
- **↪ Next:** the BTD6-floor lane is thinning; next empty fire adds a genuinely-
  uncovered shape (boss tier-HP comparison · paragon-ability lookup) **or** takes a
  plan-first lane — do not invent filler builders (see ▶ Next action).
