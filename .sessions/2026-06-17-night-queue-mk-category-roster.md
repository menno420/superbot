# Session — night-queue buffer slices + slot-4 reframe (three §7.6 floor builders)

> **Status:** `complete`

## Origin

Scheduled dispatch fire, no work order → advance the ▶ NIGHT QUEUE
([`planning/night-queue-2026-06-16.md`](../docs/planning/night-queue-2026-06-16.md)).
The §7.5/§7.6 ready slots were all consumed (#1000/#1008/#1009/#1010); slot 4 was
`NEEDS-REFRAME`; the prior handoff named the remaining work as the **buffer slices**
+ the slot-4 reframe. No new actionable bug (BUG-0011 is the OPEN Hermes-gateway
issue, out of scope). One PR (#1011) carries all three slices — a cohesive,
low-risk §7.6 floor batch.

## Done (three deterministic BTD6 floor builders — all BUG-0009 class, all Q-0048)

1. **Monkey-Knowledge category roster** (buffer slice).
   - `btd6_data_service.monkey_knowledge_by_category()` — groups the 134 MK by
     in-game tab in tab order, name-sorted within each tab.
   - `btd6_context_service.deterministic_mk_category_roster_reply` — MK cue + a
     named tab (Primary/Military/Magic/Support/Heroes/Powers) + an enumeration
     cue; defers on strategy / no-tab / **named tower** (deferring to the shipped
     `deterministic_mk_reference_reply` so the two MK builders never both fire).
   - `tests/unit/services/test_btd6_mk_category_roster.py`.

2. **Slot-4 reframe — bloon modifier explainer** (option (c), the genuinely
   useful answer the data supports; the original "property roster" stays rejected).
   - `btd6_data_service.bloon_modifiers()` — the three `category:"modifier"`
     marker entries (Camo/Fortified/Regrow).
   - `btd6_context_service.deterministic_bloon_modifier_reply` — explains a named
     modifier (or all) and **reframes** "which bloons are camo?" into "camo is a
     modifier, not a bloon type" instead of assembling the misleading `[DDT]`
     roster. Defers whenever a tower / detect-or-pop verb / tower-subject is
     present (that is the capability roster's / model's job), so it never overlaps
     the bloon roster (MOAB/immunity) or the capability roster.
   - `tests/unit/services/test_btd6_bloon_modifier.py`.

3. **Geraldo starting-kit angle** (buffer slice — shipped as an *extension*, not a
   redundant sibling, because the per-level/specific-level angles were already
   covered; only "what does Geraldo start with" missed the level/list cue).
   - Extended `deterministic_geraldo_per_level_reply` with a starting-kit cue that
     maps to his level-0 items. Tests added to
     `tests/unit/services/test_btd6_geraldo_per_level.py`.

- All three registered in `_BTD6_LIST_BUILDERS` + the exclusivity invariant corpus
  (the new MK/bloon builders); `test_btd6_floor_builder_exclusivity.py` passes the
  exactly-one-fires contract.
- Docs: night-queue slots/buffer ticked `✅ #1011`, slot-4 reframed-and-shipped;
  current-state ▶ NIGHT QUEUE re-pointed (queue **fully consumed** → fresh
  plan-first next) + a Recently-shipped ledger line.
- `check_quality.py --full` GREEN (10344 passed, +14) · `check_architecture
  --mode strict` 0 errors · mypy clean.

## Handoff → next dispatch

**The night queue is fully consumed.** Next empty scheduled fire has no buffer
slice left — it takes a **fresh plan-first lane**:
- **image moderation** (Q-0108, plan-first) · the **AI §7 next workflow family**
  beyond the floor builders · the **Hermes bug-triage `gh issue create` write**
  (Q-0121). image-mod (#941) and security tiers (#929) are in-flight but
  owner/Hermes-review-gated.
- Or promote a `docs/ideas/` entry into an executable plan (the reconciliation
  routine's idea→plan job; a dispatch fire can own one if plans run dry).
Per the per-fire discipline: **sync `origin/main` first**. The floor builders no
longer have a queued backlog, so the shared `_BTD6_LIST_BUILDERS` / `_SHOULD_FIRE`
anchors are only touched by a *new* family a future plan defines.

## 💡 Session idea (Q-0089)

**A "data answers the question's *semantics*, not just the column exists" pre-flight
for any future data-driven floor builder.** The slot-4 saga (a `properties[]`
field that exists but doesn't mean what the roster question asks) cost a reframe
mid-flight twice. Worth a tiny `scripts/` helper or a documented checklist step:
before adding a roster/comparison builder, assert the candidate field's *value
distribution* actually partitions the entities the question implies (e.g. "would a
`properties[]` roster return >1 meaningful bucket, or collapse to a degenerate
list?"). Filed, not built — keeps this PR one clean batch; a good non-night-queue
daytime slice and a natural companion to the previously-filed `roster_reply(...)`
abstraction idea (now **five** roster instances: capability · bloon · relic ·
hero-ability · MK-category — the abstraction is overdue).

## ⟲ Previous-session review (Q-0102)

Previous run was the #1008/#1009/#1010 three-slice fire. *Did well:* it caught the
slot-4 data problem **before building** (checked the data semantics first) and left
a crisp handoff naming the exact remaining work (buffer slices + reframe options),
which let this fire start building within minutes — the handoff-as-continuation
loop worked exactly as designed. *Could improve / system note:* its handoff listed
the Geraldo buffer as a clean new builder, but inspection showed the shipped
per-level builder already covered most of it — the real gap was one phrasing.
**System improvement surfaced (and acted on):** a buffer/queue slice should be
re-validated against the *currently shipped* code before building, not just against
the plan doc — the night-queue's buffer description can go stale as siblings ship.
This fire did that (tested the shipped builder first, extended it instead of
duplicating). The durable habit — *grep/test the existing seam before trusting a
queue entry's "not yet built" framing* — is the same "verify against shipped
source" rule the collaboration model already states; no doc change needed beyond
this note.

## 📋 Doc audit (Q-0104)

night-queue doc fully reconciled (table + buffer + slot-4); current-state ▶ NIGHT
QUEUE re-pointed and #1011 ledger line added. No new owner decision. The standing
`Ledger: ⚠` merged-PR backlog predates this fire and remains the reconciliation
routine's lane (#1020 boundary); the #1011 line added this fire is not deferred.
