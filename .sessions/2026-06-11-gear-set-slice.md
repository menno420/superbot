# 2026-06-11 — The gear-lane slice: V-16 phase 1, full Q-0092 scope (PR #702)

**PR:** [#702](https://github.com/menno420/superbot/pull/702) — merged same
session (Q-0084 envelope). **Authoritative docs:** the games folio (set-piece
model + compositor entries) · [`docs/planning/gear-set-numbers-2026-06-11.md`](../docs/planning/gear-set-numbers-2026-06-11.md)
(numbers rationale) · router §38 Q-0092 (execution note).

## What shipped (one line each)

- 9-slot set-piece equipment model + same-tier set bonus; migration 068 folds
  the legacy "armor" items/slot in (live-replay-verified on seeded rows).
- Bronze + silver as real mining ores; every set item forges from its tier's
  ore (44 recipes).
- The 30-item stat/economy tables under **full numbers authority**, pinned by
  `tests/unit/utils/test_gear_set_numbers.py` (monotonic ladders + duel-sim
  win-rate bands over the real `_Duel` math).
- Gear-picker stat previews (+ delta vs equipped, "⚠ breaks set bonus"
  warning) and a set-progress line on the gear embed.
- The paper-doll compositor (`utils/character_render.py`): manifest = naming
  convention over `disbot/assets/gear/` (owner pack 1:1),
  procedural tier-palette placeholders, wired to `!gear` + hub Gear button.
- Capacity fixes the 41-item catalogue forced: categorized market fields +
  per-section buy selects (the old single select silently truncated at
  `[:25]`), workshop craft-field cap fix + craftable-first ordering.

## Design findings worth remembering

- **The set bonus creates an intentional breakpoint**: it outweighs any
  single next-tier piece, so "upgrade by batches" is the collection goal.
  Two seams absorb it: `best_loadout` is **set-aware** (the naive greedy
  Equip Best would have *lowered* stats — the sim caught this) and the
  picker warns before a set-breaking equip.
- **The duel formula cliffs at defense ≥ 15 base attack** (flat reduction
  floored at 1) — full-diamond defense is pinned at 14 and the set bonus
  carries no defense so the cap can't creep.
- **Always-attack sims overstate decisiveness** (no defend-action variance):
  +1 damage ≈ 0.81 win rate. Bands encode "favoured, never guaranteed"
  (≤0.85 single-piece) rather than pretending 0.80 is a law of nature.

## Context delta (reflection interview)

1. **Route miss:** none material — the three-pointer handoff
   (current-state ▶ · router §38 · session-log handoff) was exactly
   sufficient; every decision I needed was pre-made.
2. **Route excess:** current-state's header page-1 was all I needed — the
   per-lane bullet convention is working.
3. **Discovered by hand:** the market panel's silent `options[:25]`
   truncation and the workshop embed's 1024-char overflow at 30+ recipes —
   *every catalogue growth trips a Discord cap* (25 options / 1024 field /
   5 rows / 100-char descriptions); a one-line caps checklist in the games
   folio or hub-ui-standard would have surfaced both before the live build.
   Also: the equip-time slot is derived (`slot_for`), so re-slotting needs a
   data migration only for *stored* rows — read paths self-heal.
4. **Decisions made alone (all within the Q-0092 grant):** tier order
   bronze<iron<silver<gold<diamond; legacy "armor"→chestplate **rename
   migration** over a dual catalog; set bonus excludes defense; all 30 items
   shop-listed (repair pricing derives from the shop knob); doll wiring =
   `!gear` embed image + hub follow-up (the inventory-card pattern, no
   safe_edit attachment plumbing).
5. **Weak point of what shipped:** the duel sim has no defend-action policy
   (bands are honest about it but coarser than live play); the placeholder
   doll is functional, not pretty — phase 2 is the owner's pack; previews
   show the set-bonus *loss* warning but not the prospective *gain* from
   completing a set.
6. **One change that would have helped:** the Discord-caps checklist (see 3).

💡 **Session idea (Q-0089): sprite-template tint build step.** One grayscale
template per gear family (6 images) + a palette-tint pass over
`equipment.TIER_ORDER` generates all 30 tier sprites — and every future
ecosystem's tiered gear (fishing rods) — with perfect visual consistency.
The owner already demo'd palette-swap tiers live (V-16 notes); the new part
is making it a *build step over the asset dir* (`template_{family}.png` →
`{family}_{tier}.png` for any tier missing a hand-drawn file), so the
owner's art cost per family drops from 5 drawings to 1. Routed: noted here +
fits V-16 phase 2's art-direction section when that session starts.

## Verification record

CI mirror 8,960 passed / 3 skipped; arch strict 0 errors; clean boot on real
Postgres (migration 068 applied); 068 replay over seeded legacy rows = exact
transforms; live equip/buy/craft/repair round-trips through
`mining_workflow`; set bonus + set-break live in the gear embed; doll PNG
rendered; market/workshop/recipe/gear/character panels all under caps.
