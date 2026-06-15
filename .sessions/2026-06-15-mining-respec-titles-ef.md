# Session — 2026-06-15 · mining Slices E + F — respec polish + skill/milestone titles

> **Status:** `complete`

## What I'm about to do

Dispatch routine. Work order pointed at the mining lane (▶ Next action = mining respec-polish /
skill-titles / home — Slices E/F/C). **Home (C) shipped #910**; the remaining ▶ startable slices are
**E (respec polish)** and **F (titles)** of
[`mining-structures-skill-tree-plan-2026-06-14.md`](../docs/planning/mining-structures-skill-tree-plan-2026-06-14.md),
both unblocked by the #891 skill tree.

One open PR (#911, owner's live mining-hub UX restructure) touches `main_panel.py` + `gear_panel.py`,
so I deliberately surface both slices **away from those files** — Slice E lives in
`skills_panel.py`/`skill_service.py`; Slice F's title display goes on the `character_panel.py`
aggregator (its docstring already anticipates titles) and a `🏆 Titles` button on the skills panel,
not the main hub.

**Slice E — respec polish:** add a confirm step (cost + point preview, "are you sure") before the
coin charge, and a **partial respec of one branch** (`skill_service.respec_branch`) for a reduced
cost. Today the Respec button charges instantly with no confirm.

**Slice F — titles from skill mastery + milestones:** a pure trigger table
(`utils/mining/titles.py`) → an `equipped_title` store on `mining_player_state` (migration 074) →
`services/title_service.py` (earn-check + equip/unequip) → a `🏆 Titles` panel + `!titles` + the
equipped title surfaced on the Character embed. Earned set is **derived** from existing progression
(skill allocation at cap, max depth, game level) — only the equipped *choice* is persisted, so it's
fully additive (no title equipped → byte-identical).

Verify each slice: `check_quality --full` green + `check_architecture --mode strict` 0.

## What shipped (PR #912)

**Slice E — respec polish:**
- `services/skill_service.py` — `respec_branch_cost` + `respec_branch(guild, user, branch)` (a cheaper
  single-branch refund through the same audited economy lane / one-transaction atomicity as the full
  `respec`).
- `views/mining/skills_panel.py` — the Respec button now opens a confirm card
  (`build_respec_confirm_embed` + `MiningRespecView`): cost + point preview, nothing charged until you
  pick **Refund all** / a per-branch **♻ <branch>** button (`_BranchRespecButton`) / **Cancel**.
- Numbers pinned in `docs/planning/respec-numbers-2026-06-15.md`; tests in
  `tests/unit/services/test_skill_service.py` (cost-cheaper-than-full invariant + the
  guards/atomicity).

**Slice F — titles:**
- `utils/mining/titles.py` — pure `Title` / `TitleContext` catalogue (`_RULES`) of 9 v1 titles; the
  **earned** set is *derived* (skill branch at cap · deepest biome · game level), so nothing is granted
  on a mutation path. Depth titles are biome-*named* → extend cleanly when the **P6 grid** deepens
  the world (owner-flagged this run).
- migration `074_mining_equipped_title.sql` + `get_equipped_title`/`set_equipped_title` on
  `mining_player_state` (the write primitive on the RS02 boundary ratchet) + db re-exports.
- `services/title_service.py` — `build_context` / `earned` / `equip` / `unequip` and `equipped_title`
  (gated on **still earned**, so a respec silently un-displays a mastery title).
- `views/mining/titles_panel.py` (`MiningTitlesView` + `_TitleSelect`) + a `🏆 Titles` button on the
  Skills panel + `!titles` command + the equipped title surfaced on the `character_panel.py` embed
  (additive — no title → byte-identical).
- Numbers pinned in `docs/planning/titles-numbers-2026-06-15.md`; tests in
  `tests/unit/utils/test_mining_titles.py` + `tests/unit/services/test_title_service.py` +
  the character-embed title-shown/byte-identical cases in `tests/unit/views/test_mining_character.py`.

**Verified:** `python3.10 scripts/check_quality.py --full` green (9808 passed); `check_architecture
--mode strict` 0 errors. Surfaced **away from** the open PR #911's files (`main_panel.py`/`gear_panel.py`)
to avoid collision with the owner's live hub-UX restructure.

## Handoff / next

The mining **structures / skill-tree lane is COMPLETE** — every ▶ startable slice shipped
(D #891 · A #897 · B #905 · C #910 · E + F #912). The plan
(`mining-structures-skill-tree-plan-2026-06-14.md`) is ready to re-badge `historical` once #912
merges; its only remaining items are **owner-gated** (Vault-cap *hard* enforcement · ⛔ V-16 phase 2
real sprites). Next ▶ startable off-plan work per current-state: **P1-3 invariants** (find a specific
uncovered contract or close the track) · the reserved **Railway log-triage skill** slot · then the
creds/review-blocked P1-1 remainder. **Owner steer this run:** depth will grow into a **P6 x/y grid
with N/S/E/W movement** — a future big arc; titles already accommodate it (biome-named milestones,
appended to `_RULES` as the world deepens).

## 💡 Session idea (Q-0089)

**Title progress hints on the Skills/Character surfaces.** Titles are earned-or-locked today; the
locked list shows the *requirement* but not *how close* you are (e.g. "Mining 7/10", "deepest: Cavern
— reach the Deep"). A pure `titles.progress(ctx)` returning `(earned, fraction)` per title would let
the panel render a "🔒 the Coreborn — 2/3 biomes" nudge, turning the catalogue into a visible goal
ladder (the §7.3 progression hook). Small, pure, additive over the existing `TitleContext`.
Dedup-checked `docs/ideas/` — none.

## ⟲ Previous-session review (Q-0102)

The #910 Home-slice session built cleanly and left a sharp handoff (it correctly named E/F as the
remaining ▶ slices, which is exactly what this run picked up), and its process-incident write-up (the
`cd`-wedges-the-shared-cwd lesson) was genuinely valuable. One miss: it added the Home (#910) entry to
current-state but **did not update the games folio** with Forge (#905) or Home (#910) bullets — so the
folio drifted behind the ledger (I added the structures bullets this run). **System improvement:** the
`check_docs` orphan/reachability guard catches *unlinked* docs but not *stale folios* — a folio that
silently lags shipped slices passes every check. A lightweight "every Recently-shipped PR touching
`disbot/<area>/` is mentioned in that area's folio within N PRs" lint would catch this drift class the
way the ledger guard catches current-state drift. Worth a router DISCUSS (it's a new check → owner owns
the CI surface per Q-0106), not a self-add.

## 📋 Doc audit (Q-0104)

`check_quality --full` green incl. `check_docs` (the two new `*-numbers-*.md` records are linked from
the structures plan Slice E/F sections, so no orphans). Structures plan Slices E/F marked SHIPPED +
executor pointer de-staled; games folio gained the respec-polish + titles bullets; current-state
Recently-shipped gained the #912 entry (and archived the oldest live entry #829 to hold the ratchet
net-neutral). **Known residual drift (deferred to the #930 reconciliation, per the #910 note):** the
Recently-shipped count sits 3 over the soft ratchet, and the inter-cadence routine/docs PRs
**#902/#904/#907/#908** are not yet in the living ledger — these are the reconciliation pass's batch
fold-in, not a per-session fix. No new owner decision to route (the P6-grid steer is captured in the
titles model + numbers doc + this handoff; it's a pre-existing roadmap item, not a new decision).
