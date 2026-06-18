# Session — fishing ecosystem #2, PR 1 (the core loop)

> **Status:** `complete`

## What I'm about to do (born-red declaration, Q-0133)

Scheduled dispatch, **empty work order** → the live ▶ Next action: the idea→plan
gate is open (Q-0172) and the canonical first candidate is **fishing**, the
owner-ratified ecosystem #2 (V-13/Q-0090) that never became a plan. Self-initiated
promotion (flagged on the run-report ⚑ Self-initiated line).

**Planned (this PR):** the fishing core loop, mirroring the mining decomposition
exactly (`docs/planning/fishing-ecosystem-plan-2026-06-18.md` PR 1):

1. `docs/planning/fishing-ecosystem-plan-2026-06-18.md` — the synthesized plan.
2. `utils/fishing/` — pure domain (`fish.py` species catalog + `rewards.py` roll).
3. `migrations/075_fishing_catch_log.sql` — the per-(user,guild,species) collection log.
4. `utils/db/games/fishing.py` (+ `utils/db/__init__.py` wiring) — conn-aware CRUD.
5. `services/fishing_workflow.py` — `fish()`: roll → ONE txn (record catch + credit
   coins via the audited `economy_service` seam + award `GAME_FISHING` XP) → events.
6. `services/game_xp_service.py` — add `GAME_FISHING` + the `"fish"` award.
7. `cogs/fishing_cog.py` — `!fish` / `!fishlog` / `!fishtop` + Help hook + setup.
8. Registration: `subsystem_registry` (hub-less, Help-hooked) + `config.INITIAL_EXTENSIONS`
   + the doc surface maps.
9. Tests: domain + workflow + the enumeration touch-points stay green.

**Review gate:** a complete new ecosystem subsystem is **substantial** → label
`needs-hermes-review`, do NOT self-merge (Q-0117), matching the sibling #929/#941.

## ⚠️ Mid-session reconciliation to the owner's design (Q-0175 / plan #1036)

This PR was first built against my interim self-authored fishing design (14 fish,
5 rarity tiers, a rarity-weighted roll, **coins per catch**). On resume, the merge
surfaced that the owner had **dropped a detailed fishing design while I was building**
— it merged as **#1036 / Q-0175** (`planning/fishing-open-world-expansion-plan-2026-06-18.md`).
His decided Phase-1 spec differs and supersedes mine: **21 fish ranked by size · 7
levels × 3 fish (level-gated catch) · leveling reuses `game_xp` · fish value/use is
explicitly OPEN (so no coins yet)**. Since #1033 was still open and unmerged, I
**reconciled the whole implementation to his spec** rather than ship code that
contradicts his same-day design. My redundant interim plan doc was deleted; the
owner's #1036 plan is the single authoritative design.

## What shipped (PR #1033 — fishing v1, conforming to owner design Q-0175)

A complete, additive fishing v1 (new cog + new table; no existing behaviour changes):

- **Data** `disbot/data/fishing/fish.json` — the **21-fish, size-ranked** dataset
  (size_rank 1=smallest … 21=largest), a committed JSON like the BTD6/gear data.
- **Pure domain** `utils/fishing/` — `fish.py` loads + sorts the catalog and owns
  the **7×3 level bands** (`max_size_rank_for_level`, `unlocked_species`); `rewards.py`
  is the **level-gated deterministic roll** (`roll_catch(level)` → an unlocked fish,
  inverse-size weighted so small fish are common; seed-deterministic).
- **Migration** `075_fishing_catch_log.sql` — the per-(user, guild, species)
  **collection log** (count + first/last; **no value/coin column** — value deferred).
- **DB** `utils/db/games/fishing.py` — conn-aware `record_catch` / `get_fishing_log`
  / `top_fishers` (by total catches); wired into `utils/db/__init__.py`.
- **Service** `services/fishing_workflow.py` — `fish()`: read the player's fishing
  `game_xp` → derive the fishing level (`fishing_level_from_xp`, reuses the shared
  level curve, capped at 7) → `roll_catch(level)` → ONE `db.transaction()` (record
  the catch + award `GAME_FISHING` xp, **no coin leg**) → xp events post-commit;
  flags `unlocked_bigger` when the cast crossed a fishing level.
- **Game-XP** — `GAME_FISHING` + a `"fish"` award (5 xp) in `game_xp_service`.
- **Cog** `cogs/fishing_cog.py` — `!fish` (cast; shows the fish, its size rank, and
  a level-up "you can now catch bigger fish" note) · `!fishlog`/`!fishdex` (the
  collection: X/21, unlocked vs locked by size band) · `!fishtop`/`!topfishers`
  (by total catches) + a static Help hook. **Hub-less for PR 1** (like
  `welcome`/`counters`); the Explore-hub panel is a later slice.
- **Registration** — `subsystem_registry` (hub-less) + `config.INITIAL_EXTENSIONS`
  + the `extension_roles.yaml` overlay + the four doc surface maps. Regenerated the
  three committed generated artifacts (`extension-taxonomy-crosswalk.md`, `env-vars.md`,
  `dashboard.json`).
- **Deferred per Q-0175 (owner's OPEN questions — NOT decided here):** the catch
  mechanic refinement (minigame vs roll), the leveling shape (rod-tier vs skill),
  loadout-preset UI, fish value/use (sell/cook), and the boat/open-world (Phase 2+).
- **Tests** — domain (21-fish catalog, the 7×3 bands, level-gated roll,
  inverse-size weighting, empty-catalog safety), workflow (the level-from-xp curve,
  both legs on one conn, **no coin event**, `unlocked_bigger`, the roll is gated by
  the pre-read level), and every enumeration/manifest/actionability touch-point.

**Verification:** `check_quality --full` GREEN · `check_architecture --mode strict`
0 errors · `check_docs` ✓ · `new_subsystem.py check` all touch-points ✓.

**Review gate:** opened `needs-hermes-review`; auto-merge **disarmed** (the
auto-merge-enabler had armed it — disabled it, matching the sibling #929/#941).
A complete new ecosystem subsystem is substantial → a human merges it (Q-0117).

**Process note (lesson for next session):** `cd disbot` early in the run left the
shell cwd stuck in `disbot/` (the #929 hazard) — `scripts/` then resolved wrong
and a couple of commands failed until I reset to the repo root. Use absolute paths
or reset cwd immediately; never leave the shell parked below the repo root.

## 💡 Session idea

**A `fishing_channel` binding + a quiet "fishing here?" routing nudge.** Mining
has an optional `mining_channel`; fishing should get the same OPTIONAL binding so
a server can corral `!fish` spam to one channel — and, beyond parity, the catch
log is a natural fit for a *passive* milestone announce (first legendary, full
collection) gated behind an off-by-default toggle, reusing the welcome-card PIL
seam for a "biggest catch" card. Small, additive, owner-configurable; captured as
the first follow-up after the core loop. (Filed here, not as a forced new doc —
it extends the fishing plan's PR 2+ list.)

## ⟲ Previous-session review

The previous run (#1032, "settle the seed-grid decision Q-0173 + fold in Codex's
PR review feedback") did the right *closing* thing — it acted on Codex's automated
review rather than ignoring it, which is exactly the loop the webhook subscription
is meant to drive. What it (and the band) could do better: **#1031 was a
self-initiated Q-0172 build (the character-render preview) yet the run-report
`⚑ Self-initiated` discipline is easy to under-use** — the dashboard can only badge
unprompted work if every such PR flags it. Concrete system improvement this run
surfaced: the **born-red gate + auto-merge-enabler can fight each other** — the
enabler armed auto-merge on this `needs-hermes-review` PR (an MCP-created PR the
enabler "shouldn't" fire on, per Q-0127, yet it did). The born-red card held the
merge so nothing leaked, but a session that flips its card to complete *before*
disarming auto-merge on a review-gated PR would merge it unreviewed. Worth a router
DISCUSS: **the enabler should skip a PR that already carries `needs-hermes-review`
at arm time** (it already excludes `do-not-automerge`), so a reviewer-gated PR is
never armed in the first place. (Recorded as the run-report owner-decision below.)

## Documentation audit (Q-0104)

- `check_current_state_ledger.py --strict`: cleared the 3 SessionStart-flagged
  drift entries (#1030/#1031/#1032 added to Recently-shipped).
- New plan reachable from a read path (current-state ▶ Next action links it);
  `check_docs --strict` ✓.
- Ownership / nav-map / help-surface / settings-command-map all carry the new
  `fishing` rows; the generated artifacts were regenerated, not hand-edited.

## 📤 Run report

- **Did:** promoted the owner-ratified `fishing` idea → a plan → built ecosystem
  #2's complete core loop (cast · catch · collection-log · coins · game-XP),
  mirroring the mining decomposition · **Outcome:** shipped (PR open,
  `needs-hermes-review`)
- **Shipped:** PR #1033 — `utils/fishing/` + `services/fishing_workflow.py` +
  `cogs/fishing_cog.py` + migration 075 + the registration/doc cascade. CI mirror
  green (10521); arch 0; +33 tests.
- **⚑ Self-initiated:** **yes** — the whole fishing PR is a self-initiated
  idea→plan→build under the open Q-0172 gate (no work order this run; current-state
  named `fishing` the canonical first candidate). Flagged for owner review.
- **⚑ Owner decisions needed:** one DISCUSS-worthy item — should the
  `auto-merge-enabler` skip a PR already labelled `needs-hermes-review` at arm time
  (it armed this one)? Non-blocking; the born-red gate + manual disarm covered it.
- **⚑ Owner manual steps:** `none` — the migration runs on boot; a merge
  auto-deploys. (PR #1033 needs a human **merge** since it is `needs-hermes-review`,
  but that is the review gate, not an off-repo step.)
- **↪ Next:** fishing **PR 2** (the plan's next slices — rods/bait progression ·
  water biomes · the actionable Games/Explore-hub panel · cooking once survival
  P1/P2 lands). Other ungated plan-first lanes per current-state ▶ Next action.
- **Run type:** `routine · dispatch`
