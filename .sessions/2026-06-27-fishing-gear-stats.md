# 2026-06-27 — Fishing-specific gear stats (loadout presets become a real optimisation)

> **Status:** `complete` — ready to merge (Q-0133). Run type: routine · dispatch.
> Full CI mirror green (pytest **12848 passed**, arch **0 errors**, formatters/lint/check_docs/
> check_consistency clean).

> **Run type:** `routine · dispatch` — empty-fire schedule fire, no work order. Took the next real
> plan slice: the offline-tagged S1 ▶ Next item **Fishing-specific gear stats**
> ([idea](../docs/ideas/fishing-gear-stats-2026-06-27.md)), the offline successor to the gear loadout
> presets (#1499).

**Branch:** `claude/funny-franklin-iv2rzi` (off `main` @ #1503 merge, `a7c11f53`).

## What I'm about to do (intentions)

Complete the Q-0175 / V-14 "matching gear → better fishing" half. The loadout-*swap* shipped (#1499),
but a "fishing loadout" only changes *which* mining/combat gear is equipped — nothing biases fishing,
because `utils/equipment.EffectiveStats` models only mining + combat stats. So a fishing loadout is
currently cosmetic convenience, not an optimisation.

Plan (pure, sim-pinned, offline-self-mergeable — reuses the cross-game `EffectiveStats` seam, no
parallel fishing-stat store, no migration):

1. `utils/equipment.py` — add `fishing_power` + `bite_luck` to `EffectiveStats` (additive, default 0,
   so every existing stat read is byte-identical), wire `__add__`/`STAT_LABELS`/`STAT_GLYPHS`. Add a
   small **fishing-charm ladder** in the existing CHARM slot (kept off the combat SET_SLOTS so the
   duel-balance sim is untouched) to `_GEAR` + `MAX_DURABILITY` + `GEAR_SHOP` (buyable = reacquirable).
2. `utils/fishing/gear.py` (new, pure) — convert `EffectiveStats` → the two cast knobs (a bounded
   rarity-pull multiplier from `fishing_power`, a bounded faster-bite multiplier from `bite_luck`).
3. `services/fishing_workflow.begin_cast` — read equipped gear + skills → `character_stats` → fold the
   gear knobs into `effective_pull` / `effective_bite_speed` as the **4th** how-well knob
   (rod × bait × weather × **gear**). Default-preserving: no fishing gear ⇒ ×1.0 ⇒ byte-identical.
4. Surface a small cast-panel note when fishing gear is contributing; the gear panel + shop pick up the
   new items automatically (slot-grouped).
5. Sim-pin the numbers (mirror `docs/planning/gear-set-numbers-2026-06-11.md`) + tests.

## What shipped

The Q-0175 / V-14 **"matching gear → better fishing"** half — the offline successor to the gear
loadout presets (#1499). A fishing loadout was previously cosmetic (it only changed *which* mining/
combat gear was equipped); now it **biases the cast**, reusing the cross-game `EffectiveStats` seam
(no parallel fishing-stat store, no migration).

1. **`utils/equipment.py`** — `EffectiveStats` gained `fishing_power` + `bite_luck` (additive,
   default-0 → every existing stat read byte-identical; wired `__add__`/`STAT_LABELS`/`STAT_GLYPHS`).
   A **CHARM-slot fishing-charm ladder** (fishing / anglers / master-angler charm) added to `_GEAR` +
   `MAX_DURABILITY`, deliberately *off* the combat `SET_SLOTS` so the duel-balance sim is untouched.
2. **`utils/mining/market.py`** — gear-shop rows for the three charms (coins-only, no recipe →
   satisfies `test_every_wearing_gear_is_reacquirable` without touching the curated-recipe lint).
3. **`utils/fishing/gear.py`** (new, pure) — `fishing_pull_mult` / `fishing_bite_speed_mult`, the
   bounded converters from `EffectiveStats` to the two cast knobs; `has_fishing_bonus` for the panel.
4. **`services/fishing_workflow.begin_cast`** — reads `character.character_stats(equipped, skills)`
   and folds the gear knobs into `effective_pull` / `effective_bite_speed` as the **4th** how-well
   knob (rod × bait × weather × **gear**); `CastStart.fishing_gear_bonus` carries it to the panel.
   No fishing gear ⇒ both multipliers `1.0` ⇒ byte-identical (additive safety property).
5. **`views/fishing/cast_view.py`** — a `🎣 fishing gear` cast-panel footer note when a bonus is active.
6. Numbers sim-pinned in `docs/planning/fishing-gear-numbers-2026-06-27.md`.

**Tests (all green):** `tests/unit/utils/test_fishing_gear.py` (the converter — neutrality, the pinned
ladder ×1.08/1.16/1.24 pull & ×0.97/0.94/0.91 bite, caps, monotonicity, negatives clamped) ·
`test_equipment.py` (charms are CHARM-slot/off-sets, monotonic, wear+buyable, flow through
`compute_stats`) · `test_fishing_workflow.py` (gear folds into the knobs; no-gear byte-identical) ·
`test_fishing_workflow_bait.py` (autouse fixture defaults the new reads) · `test_fishing_cast_view.py`
(footer note shown/omitted).

## Context delta

- **Needed but not pointed to:** that `begin_cast` is the single fold-point for the cast's how-well
  knobs (rod × bait × weather) — found by reading the workflow, not routed. The S1 idea doc pointed at
  the right files, which was enough. **Discovered by hand:** the recipe↔catalog alignment lint
  (`test_recipes_catalog_alignment.py`) means new wearing gear must be **either** craftable **or** in
  `GEAR_SHOP` — buyable-only is the contained path that leaves `recipes.json` (and its exact-set lint)
  untouched.
- **Pointed to but didn't need:** CodeGraph — a contained, idea-doc-scoped change; `context_map` +
  targeted grep carried it (matches the CLAUDE.md "contained change" guidance).
- **Decisions made alone:** (a) fishing gear lives **only in the CHARM slot** (a single fishing-charm
  ladder), not a new slot or the combat set slots — keeps it migration-free and duel-balance-neutral,
  at the cost that a "fishing loadout" fills one slot, not several; (b) the per-point knob constants
  (0.04 pull / 0.03 bite) + caps, tuned so the full ladder ≈ one rod tier of pull. Both reversible
  tuning; flagged for the owner's eventual balance pass.
- **Flagged for maintainer / known limits:** numbers are **sim-pinned, not live-played** — the
  cast-balance feel wants a Q-0086-style live walk (same posture as the rod/bait/weather knobs). The
  charms are **coins-only** for now (no craft/loot earn) — captured as the next offline successor in
  the S1 ▶ Next.
- **🛠 Friction → guard:** my `python3` heredoc edit to add DB mocks across the begin_cast tests
  **bypassed the PostToolUse auto-format hook** (only Edit/Write trigger it), so lint wasn't auto-fixed
  on those lines — caught by the explicit `check_quality --check-only` pass before flipping the card.
  No new guard shipped (the existing pre-PR mirror already catches it); **the durable lesson is the
  rule itself: prefer the Edit tool over shell heredocs for test edits so the format hook runs.** Also:
  adding two `db` reads to `begin_cast` reddened *two* test files' begin_cast suites — the second
  (`_bait`) only surfaced in the full mirror, not the targeted run. Cheapest durable fix used: an
  autouse fixture in the bait file rather than per-test patches.

## 💡 Session idea (Q-0089)

**A `check_effectivestats_knob_coverage` guard / test** — every `EffectiveStats` field should be
*read* by at least one game's stat-consumption path, or it's a dead stat (a field added to the block
but never folded into any cast/descent/duel). `fishing_power`/`bite_luck` are now read by `begin_cast`,
`mining_power`/… by descent, `damage`/… by the duel — but nothing asserts a *new* field gets wired to
a consumer. A small test mapping each field → its consumer (grep/AST) would catch a future "added the
stat, forgot the knob" half-ship. Genuinely useful, small, offline. Captured here; if it earns a file
it goes under `docs/ideas/` next pass.

## ⟲ Previous-session review (Q-0102)

Previous run (`2026-06-26-btd6-eval-anchor-coverage`, #1466) **did well:** it explicitly teed up its
own next lane ("▶ remaining anchor-tooling tail: none cleanly offline → the live llm_judge battery"),
which made *this* session's dispatch decision instant — I could see S2's offline lane was exhausted
and move to S1's offline item without re-deriving it. That's the handoff-sharpening loop working.
**Could improve / system note:** the S2 sector file's "none cleanly offline" verdict is only in prose;
the `dispatch_menu.py --unattended` resolver still listed "S2 (Next): P1-1 BTD6 eval cases" as a 🟢
self-mergeable lane, which contradicts the sector file. **Improvement:** the resolver's offline-fit
tag should be driven by the same per-item `[offline]/[needs-live-bot]` tags the sector files carry, so
a sector that has *narrated* its offline tail as exhausted isn't re-suggested as 🟢 — otherwise a
dispatch run can be pointed at a lane that's actually creds-gated. (This is the same class as the
band-#1482 "per-sector offline-fit startability tags" idea — worth folding the resolver onto those
tags.) Not shipped this run (it touches the dispatch tooling + sector-file convention); noting it for
the docs/S3 lane.

## 📤 Run report

- **Did:** shipped the Q-0175 "matching gear → better fishing" half — fishing stats on `EffectiveStats`
  + a CHARM-slot charm ladder + the 4th cast knob in `begin_cast`. · **Outcome:** shipped
- **Shipped:** #1504 — feat(fishing): fishing-specific gear stats (self-merge on green, Q-0113)
- **Run type:** `routine · dispatch`
- **Class:** feature (dispatched empty-fire → next real plan slice; contained, reversible, test-covered)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (merge auto-deploys; the new charms appear in the gear shop on the
  next boot — no seed/data step)
- **⚑ Self-initiated:** **yes** — this was an empty-fire schedule run (no work order); I promoted the
  already-captured S1 idea [`fishing-gear-stats-2026-06-27`](../docs/ideas/fishing-gear-stats-2026-06-27.md)
  straight to a build (idea→ship is open, Q-0172). The idea pre-existed (captured alongside #1499); no
  new feature was invented from nothing.
- **↪ Next:** S1 ▶ — **fishing-gear acquisition depth** (a craft/loot earn for the charms, currently
  coins-only); pure + offline + sim-pinnable. The cast-balance feel still wants a Q-0086 live walk.

## ⟲ Bug-book

No bug-book entries fixed or opened this run (the open BUG-0009/0011/0019 items are data-/VPS-/
owner-decision-gated, none offline-actionable this run).

