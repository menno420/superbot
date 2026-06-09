# 2026-06-09 — Multi-lane plan execution: Workshop + durability + live overview; lane confirms routed

**Prompt:** maintainer asked to "execute the multi-lane plan from the recent PR" (the
#621 repo review's §4 executability table), use judgement on improvements, and document
all open questions in the repo. Explicitly a test of the system *and* the agent.

## Arc

Executed in the review's readiness order: **lane 1 (mining — turn-key)** built
end-to-end; **lanes 2–4 (adaptive Q-0045 / answerability / orchestration)** are
confirm-blocked by the repo's own gates, so their blocking inputs were converted into
one-line-answerable router questions instead of guessed at. Judgement call recorded in
Q-0047: a general "execute the plan" prompt is **not** an explicit AI-exposure gate
lift (the repo's pattern is per-feature lifts; "unanswered questions are not approval").

## Shipped (one PR)

- **Workshop + durability keystone** (brainstorm §7.5): migration **063**
  (`mining_gear_wear` + `last_broken_item`), `utils/equipment.MAX_DURABILITY`,
  `cogs/mining/workshop.py` (wear tick / audited repair via economy_service / shared
  atomic `apply_craft` / quick-craft-with-auto-equip), Workshop panel + hub button,
  `!workshop` `!repair` `!quickcraft` + `!craft` alias, wear wired into mine + explore.
- **§6.3 mother-panel live overview**: `build_overview_embed` (location · tool+durability ·
  light · net worth · broken-gear hint) on `!minemenu`, the Help hook (graceful
  fallback), and every back-to-hub path.
- **Design correction over the §6.4 sketch:** durability keyed by item *name* in its own
  table, not a column on `mining_equipment` — slot-keyed durability resets on
  unequip/re-equip (free-repair exploit). Brainstorm corrected in place.
- **Adjacent root-cause fixes:** dead torch recipe (coal unobtainable) + missing
  pickaxe/lantern recipes; `!build`'s half-consumed-recipe risk closed via
  one-transaction `db.apply_inventory_deltas`; mine bonus made equipment-aware
  (iron pickaxe ×3, legacy inventory fallback preserved); `ownership.md` mining row
  drift (missing `mining_player_state`) fixed; a known views→cogs module-level import
  retired (arch warnings 87→86).
- **Docs/routing:** Q-0046 (durability tuning confirm), Q-0047 (answerability Phase 3
  gate lift + tool list, with recommendation), Q-0048 (orchestration Phase 4 MVP slice,
  with recommendation); current-state + roadmap lane pointers re-synced; R5
  (roadmap-freshness line) adopted into the journal END checklist.

## Verification

CI mirror green (**8393 passed**, +41 new tests; mypy/black/isort/ruff/docs clean);
architecture **0 errors / 86 warnings**; clean boot (migration 063 applied, MiningCog
loaded, 0 errors); **live DB round-trip** of the full loop: 60 wear ticks → break →
inventory consumed → quick-craft (atomic, auto-equip) → repair debits real coins through
economy_service → insufficient-funds rejected with wear intact.

## Open / for the maintainer (all one-liners, in the router)

- **Q-0045** — audience simulation (blocks adaptive P1B/P1C). Pre-existing.
- **Q-0046** — confirm/retune the shipped durability numbers; should duels tick
  weapon/armor wear next?
- **Q-0047** — answerability Phase 3: gate lift + the four-tool list (recommended: yes).
- **Q-0048** — orchestration Phase 4 MVP: deterministic-first slice (recommended shape
  in the entry).

## Context delta

- **Needed but not pointed to:** that `recipes.json` *on disk* shadows
  `DEFAULT_RECIPES` entirely (the loader never merges) — easy to "add" a recipe in code
  that never loads; and that `test_mining_no_root_overview.py` pins the hub's exact
  button count (any hub-button slice must update it). Neither is in the games folio.
- **Pointed to but didn't need:** CodeGraph symbol tools — `context_map.py` + targeted
  reads carried the whole session (consistent with the P0C experience for known-shape
  work).
- **Discovered by hand:** the §6.4 durability-on-equipment sketch is exploitable
  (unequip/re-equip reset); now corrected in the brainstorm itself so the next agent
  doesn't re-derive it. Also: `pgrep -f disbot/bot1` matches *your own* pgrep shell —
  the journal's comm-check kill recipe is the right one, trust it.
