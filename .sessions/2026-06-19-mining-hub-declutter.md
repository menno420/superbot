# Session — mining hub declutter (Option A PR2)

> **Status:** `complete`

**Lane:** ultracode A1 — Mining hub redesign Option A, PR2 ("hub declutter").

## Arc

Slimmed the headline mining hub from 14 buttons (5 rows) to the 6 of owner-picked Option A,
and grouped the rest into dedicated sub-hubs mirroring the existing `MiningWorkshopHubView`
template. PR3 (grid Mine) is owner-sign-off-gated — explicitly out of scope.

## Shipped (PR #1131)

Main hub → **6 buttons**: ⛏️ Mine · 🌲 Harvest · 🗺️ Explore · 🧍 Character · 🧰 Gear · 🔨 Workshop.

- **NEW `disbot/views/mining/character_hub.py`** — `MiningCharacterHubView`: Overview ·
  Inventory · Stats · Skills · Vault · Home. The Inventory/Stats button bodies (inline DB
  reads) and `_render_inventory_file` moved here from `main_panel.py`.
- **NEW `disbot/views/mining/explore_hub.py`** — `MiningExploreHubView`: open-world explorer
  **stub** (Fishing/Roam/Quests "coming soon"). Pure stub — no fishing-module wiring. Uses
  the new `custom_id mining:explore_hub` (distinct from the old `mining:explore`).
- **`main_panel.py`** — trimmed to the 6 Option A actions; `_ACTIONS_GUIDE` /
  `build_overview_embed` / `build_embed` text updated to match.
- **`mine_view.py`** — folded Descend/Ascend + the depth-tied mining random-event explore
  into `MineView` (row 1), each swapping to the navigable `_MineResultsView`.
- **Tests** — new `test_mining_character_hub.py` + `test_mining_explore_hub.py`; updated
  `test_mining_no_root_overview` (6-button IA), `test_mining_descent` (movement now in
  `MineView`), `test_mining_inplace_cards` (inventory in Character hub), `test_mining_cog_dm_guard`
  (new button set + sub-hub guards).
- **Docs** — plan PR2 marked shipped; games folio updated.

**Verified:** `python3.10 scripts/check_quality.py --full` GREEN (10888 passed, 44 skipped;
mypy clean; ruff clean on `disbot/` after fixing two D209 docstrings) ·
`python3.10 scripts/check_architecture.py --mode strict` 0 errors (only pre-existing known
WARNs) · mining test subset 49/49.

**Deviations (flagged in PR #1131 for owner review):**
1. **Home placement** — `🏠 Home` placed in the Character sub-hub (it personalizes the
   Character card; the plan's Character list predated the Home feature #910).
2. **Explore name-clash routing** — the main hub's new `🗺️ Explore` opens the *open-world*
   stub; the depth-tied mining random-event "explore" is a *different concept* and folded
   into the Mine action as an interim until PR3's grid Mine.

## 📤 Run report

- **Did:** mining hub declutter to Option A 6-button IA + Character/Explore sub-hubs (fleet A1).
  · **Outcome:** shipped
- **Shipped:** #1131
- **Run type:** `dispatch · fleet-unit`
- **⚑ Self-initiated:** none (executed the owner-approved plan PR2 verbatim, within lane).
- **⚑ Owner decisions needed:** live-verify the new layout after deploy (UI reorg, fully
  reversible); confirm the two documented deviations (Home placement, Explore routing).

## 💡 Session idea

**A persistent-view custom_id drift guard.** This declutter changed `MiningHubView`'s
component set (removed buttons, renamed `mining:explore` → `mining:explore_hub`). Old posted
panels are superseded — acceptable for a redesign — but there is no automated signal when a
`@register`-ed PersistentView's `custom_id` set changes, which is exactly the kind of change
that can silently break restore paths or orphan live messages. A small check that snapshots
each registered PersistentView's `{custom_id}` set into a committed fixture and fails (warn-
tier) on drift would make every such change *deliberate and reviewed* — the same "pin the
contract so a refactor can't drop it silently" instinct the mining tests already use, lifted
to the registry level. Cheap, verifiable, disposable if noisy.

## ⟲ Previous-session review

The previous fleet session (B2, #1086 — ledger-hygiene linter) did the right disposable-tool
thing: a read-only, warn-only linter with a provenance header, shipped with 19 tests. Its
notable miss was *coverage of its own kill-switch claim* — it documents "delete if unreliable"
but ships no signal for **when** it has proven reliable enough to graduate, so the next agent
has no objective bar. **Concrete system improvement:** adopted convenience checks should record
a tiny "confirmed-correct N times across sessions" tally in their header (incremented when an
agent verifies the tool against ground truth), turning the vague "verify a few times" rule into
a visible, decrementing-toward-trust counter — the missing back-half of the Q-0105 adopt-with-
kill-switch loop.

## Doc audit (Q-0104)

- `check_docs.py --strict` → exit 0, all reachable (one *soft* recently-shipped ratchet warning,
  which belongs to the orchestrator-owned `current-state.md` ledger — not editable from this
  lane by hard rule).
- Plan doc (`mining-hub-redesign-2026-06-15.md`) PR2 marked shipped with PR #; games folio
  updated with the new sub-hub structure. New source files are reachable via the plan's source
  anchors + the folio note.
- `current-state.md` is intentionally untouched (HARD RULE for this lane); the next
  reconciliation pass folds PR #1131 into the living ledger.
