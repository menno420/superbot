# Session — night-queue slot 5: hero ability roster floor (slot 4 reframed)

> **Status:** `complete`

## Origin

Third slice of the same scheduled dispatch fire (after #1008 slot 2 + #1009 slot 3),
continuing the ▶ NIGHT QUEUE
([`planning/night-queue-2026-06-16.md`](../docs/planning/night-queue-2026-06-16.md)).

**Slot 4 (bloon property roster) is NOT cleanly data-complete — pivoted to slot 5.**
See the finding below; the third slice is **slot 5 — hero ability roster** (§7.6),
which IS data-clean (all 17 heroes carry `abilities[{level,name,summary}]`, 0
missing).

## Slot-4 finding (recorded for the next fire — this is the bug-first move)

The night queue assumed `bloons.json` → `properties[]` answers "which bloons are
camo / fortified / regrow". It does **not**, cleanly: in BTD6 **camo / fortified /
regrow are universal *modifiers*** applied to *any* bloon, not intrinsic per-type
properties. In the data they appear only on the three `category:"modifier"` marker
pseudo-entries (`Camo property` / `Fortified property` / `Regrow property`) plus a
couple of innate cases (DDT is innately camo+black+lead; Lead Bloon is lead). A
roster "which bloons are camo" served from `properties[]` would return just
`[DDT, Camo-property-marker]` — itself a **BUG-0009-class wrong assembly** (it
implies only DDT can be camo, when every bloon can). The existing
`deterministic_bloon_roster_reply` already excludes `category:"modifier"` for this
reason. **Reframe needed before building slot 4** (recorded in the night-queue doc).

## What I'm about to do (slot 5)

Add the **hero ability** roster — the per-hero sibling of the capability / bloon /
relic rosters. "what abilities does Quincy have?", "list Adora's abilities" lists a
hero's abilities (level + name + summary) so the model can never mis-level /
mislabel one (BUG-0009). The "which heroes have an ability at level N" cross-query
was **dropped** — the data only carries levels 3 and 10 uniformly across all 17
heroes, so the cross-query is degenerate (all-or-nothing); the per-hero list is the
useful, clean shape.

- `btd6_data_service.hero_abilities(name)` — resolve one hero via the shared
  surface resolver, return abilities ascending by level, `None` on miss.
- `btd6_context_service.deterministic_hero_ability_roster_reply` — fires on an
  ability cue + exactly one resolved hero; defers on a cost cue (the hero *cost*
  builder's job), strategy, zero or two-or-more heroes. Registered in
  `_BTD6_LIST_BUILDERS` after the relic roster.
- Tests: `tests/unit/services/test_btd6_hero_ability_roster.py` + an exclusivity
  corpus should-fire phrase.

Ships under **Q-0048** (read-only deterministic floor, no prod-check, auto-deploys).

## Done

- `btd6_data_service.hero_abilities(name)` — level-sorted, `None` on miss.
- `btd6_context_service.deterministic_hero_ability_roster_reply` +
  `_format_hero_abilities`; registered in `_BTD6_LIST_BUILDERS` after the relic
  roster.
- `tests/unit/services/test_btd6_hero_ability_roster.py` (13 tests, incl. a
  data-completeness guard that fails loudly if a future dataset drops a hero's
  abilities) + the exclusivity corpus should-fire phrase.
- Docs: night-queue slot 5 ticked `✅ #1010`; **slot 4 reframed → `NEEDS-REFRAME`**
  with the camo/fortified/regrow-are-modifiers finding + reframe options;
  current-state ▶ NIGHT QUEUE re-pointed + a Recently-shipped ledger line.
- `check_quality.py --full` GREEN (10318 passed, +14) · `check_architecture
  --mode strict` 0 errors.

## Fire summary (THREE slices, one scheduled dispatch)

This empty scheduled fire shipped **three** complete night-queue slices end to end,
each merging before the next branched (per-fire discipline held — no shared-anchor
conflicts):
- **#1008** — slot 2, §7.5 power cost comparison (merged)
- **#1009** — slot 3, §7.6 relic category/effect roster (merged)
- **#1010** — slot 5, §7.6 hero ability roster (this PR) + slot-4 reframe

The §7.5/§7.6 deterministic floor queue is now **consumed** bar the reframe-pending
slot 4 and the two buffer slices.

## Handoff → next dispatch

The night-queue's ready slices are done. **Next empty fire options (in order):**
1. A **buffer slice** from the queue doc — *Geraldo items-by-unlock-level roster*
   or *Monkey-Knowledge category roster* (both §7.6, data-complete; each must defer
   to its already-shipped sibling — see the queue's Buffer section).
2. **Reframe + build slot 4** per the three options now in the queue doc (the
   modifier-explainer option (c) is the genuinely useful one the data supports).
3. A fresh **plan-first** lane (image-mod is in-flight #941; security tiers #929) —
   but those are owner/Hermes-review-gated, so a buffer slice is the cleaner
   ungated default.
Per the per-fire discipline: **sync `origin/main` first**; the floor builders share
the `_BTD6_LIST_BUILDERS` + `_SHOULD_FIRE` append anchors.

## 💡 Session idea (Q-0089)

(Fire's idea recorded in the slot-2 log: a generic `rank_entities_by(...)` helper
for the §7.5 comparison primitives; extended in the slot-3 log to a `roster_reply(...)`
helper for the §7.6 roster builders.) **This slice is the fourth roster instance**
(capability · bloon · relic · hero-ability), so the roster shape is now empirically
stable enough that the `roster_reply` abstraction is worth building *next* — a small
dedicated refactor PR that collapses the four builders to their cues + grouper,
removing the duplicated `subject-cue → list-cue → strategy-defer → format/truncate`
skeleton each currently re-implements. Filed (not built — keeps this PR one clean
slice); a strong candidate for a non-night-queue daytime slice.

## ⟲ Previous-session review (Q-0102)

The previous slice this fire was #1009 (relic roster). *Did well:* its handoff
explicitly named slot 4 as next AND flagged the per-fire sync discipline — which is
exactly what let *this* slice catch the slot-4 data problem early (I checked the
data before building, per the slot-3 log's "sync first / check the seam" habit) and
pivot cleanly instead of shipping a misleading roster. *System improvement surfaced:*
the night-queue doc asserted every slice was "data-complete today" but slot 4 wasn't
— the planning assumption ("a field exists in the JSON" ⇒ "a clean roster exists")
is too weak; a field existing ≠ the field *meaning* what the question asks. The
durable fix is the habit this fire used and the queue now documents: **verify the
data answers the question's *semantics*, not just that the column exists, before
building a data-driven floor.** Recorded inline in the queue's slot-4 note so the
next author inherits it.

## 📋 Doc audit (Q-0104)

`current-state.md` ▶ NIGHT QUEUE re-pointed (queue consumed → buffer/plan-first
next); #1010 ledger line added; night-queue slots 4 (reframe) + 5 (✅) updated. No
new owner decision. The standing `Ledger: ⚠` merged-PR backlog predates this fire
and remains the reconciliation routine's lane (#1020 boundary) — three new ledger
lines added this fire (#1008/#1009/#1010), none deferred.
