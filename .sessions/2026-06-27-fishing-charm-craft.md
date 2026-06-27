# 2026-06-27 — Fishing-gear acquisition depth: fish→charm craft path

> **Status:** `complete`

**Run type:** routine · dispatch

## What this run did

Empty-fire dispatch. The `dispatch_menu.py --unattended` tool (built last run, #1482) pointed at the
S1 `[offline]` ▶ Next item: **fishing-gear acquisition depth**, the offline successor to #1504
(fishing-specific gear stats). The three CHARM-slot fishing charms (`fishing charm` / `anglers charm` /
`master angler charm`) were **coins-only** — a single source. This run gives them a **non-coin earn
path**, mirroring the existing catch→bait loop.

**PR #1508 — the fish→charm craft path.**

1. **Pure ladder** (`utils/fishing/gear.py`): a `CharmRecipe` dataclass + `CHARM_RECIPES` (8/12/18
   fish, size-caps 8/14/21), `charm_recipe` / `charm_recipe_text` / `craftable_charm_for` helpers —
   the exact shape of `utils/fishing/bait.py`'s `CRAFT_RECIPES`. Monotonic up the ladder; sim-pinned in
   `docs/planning/fishing-charm-craft-numbers-2026-06-27.md`.
2. **Workflow** (`services/fishing_workflow.py`): `craft_charm` mirrors `craft_bait` — an inventory-only
   conversion (no coins, no audit, no external call) that debits eligible fish (smallest-first) and
   grants `+1` charm into the mining inventory in **one** `db.transaction()`. The existing
   `_plan_fish_spend` planner was generalized from `bait_mod.BaitRecipe` to a `_FishRecipe` Protocol so
   bait and charm recipes share it — no logic duplicated.
3. **Command** (`cogs/fishing_cog.py`): `!craftcharm [name]` (alias `charmcraft`), parallel to
   `!craftbait`. Reachable via the fishing cog's subsystem homing (0 reachability gaps).
4. **Design**: coins stay the *fast* path (the gear shop still sells charms); crafting is the *slow,
   gameplay-native* path — charms want far more fish than a bait pack, charms are never sellable back
   (no arbitrage), and the fish consumed are worth less sold than the charm's shop price.

The loop closes: `!fish → !craftcharm → !gear (equip) → fish better`, the charm sibling of the bait loop.

## Verification
- New tests: 24 — `tests/unit/utils/test_fishing_gear.py` (+4: every recipe targets a real shop charm,
  case-insensitive resolution, strict-monotonic cost ladder, recipe text) and
  `tests/unit/services/test_fishing_workflow_charm.py` (+6: shared planner accepts a charm recipe,
  debit+grant in one delta map / no coins, case-insensitive, insufficient-fish writes nothing,
  oversize-fish rejected by the size cap, uncraftable/unknown bails before any read).
- `python3.10 scripts/check_quality.py --full` GREEN (12856+ passed); `check_architecture --mode strict`
  0; `check_command_reachability` 0 gaps; `check_consistency` ✓; mypy clean on the three files.
- Regenerated dashboard artifacts (`+1` command → 456) so the freshness guards stay green.

## 💡 Session idea (Q-0089)
*A `fish-loot drop` channel — give a cast a small chance to yield charm/craft materials (or a charm
fragment) directly, not just a fish.* Today both earn paths for charms route through *selling/spending*
(coins) or *converting whole fish* (craft); a rare on-cast drop would add a third, more exciting source
and a reason to keep fishing past the point of having enough fish to craft. It reuses the existing
`commit_catch` inventory-grant seam (just an extra delta on a rare roll) and is pure + sim-pinnable —
the natural next offline successor, already routed onto the S1 ▶ Next line. Genuinely tied to this run's
loop, not filler.

## ⟲ Previous-session review (Q-0102)
The previous run (2026-06-27, #1482 offline-fit startability tags) did its best work in **closing its own
loop**: it didn't just add the tag convention, it wired `dispatch_menu.py --unattended` to surface the
concrete `[offline]` item per sector — and *this* run is the proof it worked, because that tool is
exactly what told me what to build, with zero orient-time spent hunting for an offline lane. Its Q-0102
note proposed a cheap upgrade: have the Q-0102 ender **promote a twice-flagged observation into the
bug-book / `docs/ideas/` on the second occurrence** rather than re-noting it in prose, so the latency
between "flagged" and "built" shrinks. **System improvement this run surfaces:** the dispatch tool gives
a *sector* + *item*, but I still had to read three source files (`bait.py`, `market.py`,
`fishing_workflow.py`) to learn the *pattern* to mirror. A future upgrade would be for an `[offline]`
▶ Next item to optionally name its **"mirror this" seam** (e.g. "mirror `craft_bait`") inline — the tag
already says *it's buildable*; naming the template would cut the remaining orient cost. Low urgency,
routed as an observation here, not a unilateral edit.

## Doc audit (Q-0104)
Durable homes: the feature lives in code (`gear.py` / `fishing_workflow.py` / `fishing_cog.py`); the
balance rationale in `docs/planning/fishing-charm-craft-numbers-2026-06-27.md` (linked from S1-bot.md,
no orphan); the S1 ▶ Next line de-staled to mark acquisition-depth shipped and point at the next
successor. `check_current_state_ledger --strict` lag (#1503–#1507) is benign newest-merge lag — the
docs-reconciliation routine records it at the next pass (#1530), not a manual dispatch's lane (Q-0124);
this PR's #1508 fact lands in the next session/recon's Recently-shipped. `check_docs --strict` +
`check_consistency` green. Claim file deleted at close. No bug-book entry to mark (no bug fixed/found).

## 📤 Run report
- **Did:** shipped the fish→charm craft path (S1 acquisition-depth successor to #1504) — pure
  `CharmRecipe` ladder + `craft_charm` workflow (shares `_plan_fish_spend`) + `!craftcharm` + 24 tests +
  a sim-pinned numbers doc; regenerated the dashboard. PR #1508, self-merge on green.
- **Next (handoff):** S1 ▶ Next now points at the **fish-loot drop** successor (rare on-cast material
  drop via the `commit_catch` grant seam) or extending the same craft pattern to the **rod ladder** —
  both `[offline]`, pure, sim-pinnable.
- **Run type:** routine · dispatch
- ⚑ **Self-initiated:** none (this is the dispatch-menu's flagged S1 `[offline]` item, not an
  unprompted promotion).
- ⚑ **Owner-decisions:** none.
- ⚑ **Owner-manual-steps:** none (the charm ladder is code + data; it goes live on the auto-deploy of
  the merge — no seed step, no migration).
