# 2026-06-09 — Multi-lane plan execution: Workshop + durability + live overview; lane confirms routed

**Prompt:** maintainer asked to "execute the multi-lane plan from the recent PR" (the
#621 repo review's §4 executability table), use judgement on improvements, and document
all open questions in the repo. Explicitly a test of the system *and* the agent.

## Arc

Executed in the review's readiness order: **lane 1 (mining — turn-key)** built
end-to-end; **lanes 2–4 (adaptive Q-0045 / answerability / orchestration)** are
confirm-blocked by the repo's own gates, so their blocking inputs were converted into
one-line-answerable router questions instead of guessed at. Judgement call (recorded
here): a general "execute the plan" prompt is **not** an explicit AI-exposure gate
lift (the repo's pattern is per-feature lifts; "unanswered questions are not approval").
The parallel gate-lifting interview validated the read: those lifts were granted
explicitly there (and a standing read-only-deterministic lift, Q-0048, now exists).

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
- **Docs/routing:** durability-tuning confirm routed (renumbered **Q-0054** after the
  merge — a parallel gate-lifting interview session took Q-0046–Q-0053 and *answered*
  the orchestration-MVP + answerability-gate questions I had routed under those
  numbers); current-state + roadmap lane pointers re-synced; R5 (roadmap-freshness
  line) adopted into the journal END checklist.

## Verification

CI mirror green (**8393 passed**, +41 new tests; mypy/black/isort/ruff/docs clean);
architecture **0 errors / 86 warnings**; clean boot (migration 063 applied, MiningCog
loaded, 0 errors); **live DB round-trip** of the full loop: 60 wear ticks → break →
inventory consumed → quick-craft (atomic, auto-equip) → repair debits real coins through
economy_service → insufficient-funds rejected with wear intact.

## Open / for the maintainer (post-merge state)

- **Q-0054** — confirm/retune the shipped durability numbers + the Q-0050
  "craft-once lights" interplay (do torches/lanterns wear, as shipped, or never break?).
- Q-0045/Q-0046/Q-0047/Q-0048 (main's numbering) were **answered** in the parallel
  gate-lifting interview — the lanes this session routed as questions are now unblocked.

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
