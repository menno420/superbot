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

## What shipped (PR #1033 — fishing ecosystem #2, PR 1)

A complete, rewarding fishing minigame on its own — pure additive (new cog + new
table; no existing behaviour changes), mirroring the mining decomposition:

- **Pure domain** `utils/fishing/` — `fish.py` (a self-contained 14-species
  catalog: rarity tiers + coin/weight bands; its own loot ladder, not a reskin)
  + `rewards.py` (`roll_catch`, two-stage rarity-weighted roll, seed-deterministic
  for tests, with a `rod_bonus` hook for the later rod ladder).
- **Migration** `075_fishing_catch_log.sql` — the per-(user, guild, species)
  **collection log** (`BIGINT` identity, the `game_xp`/`mining_structures`
  precedent; an empty table is byte-identical to the pre-fishing bot).
- **DB** `utils/db/games/fishing.py` — conn-aware `record_catch` (upsert: bump
  count + total value, keep best weight, stamp times) / `get_fishing_log` /
  `top_fishers`; wired into `utils/db/__init__.py`.
- **Service** `services/fishing_workflow.py` — `fish()`: roll → ONE
  `db.transaction()` (record the catch + credit coins via the audited
  `economy_service.credit_in_txn` seam + award `GAME_FISHING` XP) → balance/XP
  events post-commit. Frozen `FishResult`.
- **Game-XP** — `GAME_FISHING` + a `"fish"` award row in `game_xp_service`
  (no schema change; the service is built to extend).
- **Cog** `cogs/fishing_cog.py` — `!fish` (cast) · `!fishlog`/`!fishdex` (your
  collection) · `!fishtop`/`!topfishers` (top anglers) + a static Help hook +
  `setup`. **Hub-less for PR 1** (like `welcome`/`counters`) — the Games/Explore
  actionability contract requires a games-child to own an *actionable* panel,
  which is a later plan slice, so PR 1 stays hub-less and surfaces via the typed
  commands + Help hook.
- **Registration** — `subsystem_registry` (hub-less) + `config.INITIAL_EXTENSIONS`
  + the `extension_roles.yaml` overlay + the four doc surface maps
  (help-command-surface-map, settings-customization-command-map, repo-navigation-map,
  ownership). Regenerated the three committed generated artifacts that track the
  live registries: `extension-taxonomy-crosswalk.md`, `env-vars.md`, `dashboard.json`.
- **Tests (+33)** — domain (catalog integrity, roll determinism/distribution/bands,
  rod-bonus redistribution), workflow (the three legs run on one conn; events emit
  after commit; level-up note; value→both-legs), and every enumeration/manifest/
  actionability touch-point updated.

**Verification:** `check_quality --full` GREEN (10521 passed) · `check_architecture
--mode strict` 0 errors · `check_docs` ✓ · `new_subsystem.py check` all touch-points ✓.

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
