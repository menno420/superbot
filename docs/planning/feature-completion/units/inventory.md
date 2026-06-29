# Inventory — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `inventory` · **Type:** server-fn · **Family:** economy
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/inventory_cog.py` (`!inventory`/`!inv` + `UnifiedInventoryView` +
> `build_help_menu_view`) · `disbot/utils/db/inventory.py` (read primitives) ·
> `disbot/views/economy/main_panel.py` (Economy-hub 🎒 button) · folio
> `docs/subsystems/games.md` / economy folio

> Assessed during the completion-first arc (Q-0209). Inventory is a **read-only unified item browser**:
> it merges the economy item table and the mining inventory, groups by category (`ITEM_CATALOGUE`),
> paginates (8/page) and sorts by rarity. Writes happen **upstream** (mining/shop/crafting workflows,
> which audit their *coin* leg via `EVT_BALANCE_CHANGED`); the inventory unit itself performs no
> mutations. The honest gaps are real and shape the punch-list: declared mutation capabilities
> (`inventory.item.use`, `inventory.craft.recipe`) are **aspirational / unenforced**, item-grant has
> **no `audit.action_recorded`**, there is **no server configuration**, and tests cover only the
> navigation lifecycle (not the display/sort logic). This is a clean Phase-1 read-only unit; use/sell/
> trade/gift + audit + config are explicitly future work.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise (view items)** — `_build_combined_inventory` merges mining + economy items, grouped
      + rarity-sorted; empty state guides to `!mine`/`!shop`.
- [ ] **Every best-in-class sub-option** — ❌ **read-only.** No use/equip/sell/trade/gift actions exist;
      no sort/filter UI beyond the fixed category+rarity order. → punch #1/#5.
- [x] **Failure modes honest** — empty inventory message is accurate; reads can't fail destructively.
- [x] **Idempotent** — pure reads (no view-layer writes; pinned by `test_no_view_level_purchase_writes`).

### B. Reachability & UI
- [x] **A command panel exists** — `!inventory`/`!inv` → `UnifiedInventoryView` (category buttons →
      paginated `_CategoryView`); Economy-hub 🎒 button (`economy:inventory`).
- [x] **Reachable every natural way** — command + Economy-hub button + `build_help_menu_view` hook.
- [N/A] **Integrated into Setup** — items are earned via mining/shop; nothing to configure at onboarding.
- [x] **Return navigation** — `_CategoryView` Back → hub; Economy path attaches back-to-economy.
- [x] **In-place, not spammy** — command uses `send_panel`; the Economy button edits in place.

### C. Convenience
- [x] **Pagination** — 8 items/page with boundary-disabled nav; hub previews first 3 + count per category.
- [ ] **Sort/filter** — ❌ no name/qty/rarity sort or type filter; fixed order only. → punch #5.
- [x] **Clear feedback** — empty state + page footer; ⚠ item-detail line is dense (emoji·name·qty·rarity·
      type on one line) — readability degrades for large inventories. → punch #4.

### D. Authority & safety
- [x] **Authority re-checked at callback** — view ownership enforced by `BaseView.interaction_check`
      (read-only; no capability gate needed for a self-view).
- [ ] **All mutations through the audited seam** — ⚠ **N/A here, but a gap upstream:** the inventory unit
      writes nothing; however the item-grant primitives (`utils/db/inventory.add_item` / mining
      `apply_inventory_deltas`) do **not** call `emit_audit_action` — only the coin leg is audited
      (`EVT_BALANCE_CHANGED`). The item trail is incomplete. → punch #2.
- [N/A] **Provisioning pipeline** — no resource creation.
- [ ] **Reuses governance** — capabilities `inventory.item.view/use` + `inventory.craft.recipe` are
      **declared but unenforced** (the read view has no capability check beyond user-tier visibility).
      → punch #3.

### E. Configuration
- [ ] **Settings pipeline** — ❌ **no `inventory` schema.** `ITEM_CATALOGUE` is hardcoded; no per-guild
      enable/disable/rename. → punch #6. (Arguably correct for a global item model — flagged, not faulted.)
- [N/A] **config-input widgets** — no server-level config surface.
- [N/A] **Everything configurable that should be** — pending the #6 decision (is per-guild config wanted?).

### F. Wiring & discoverability
- [x] **Registry** — key `inventory`, `category: economy`, `visibility_tier: user`,
      `parent_hub: economy`, entry `inventory`, depends on economy, capabilities declared (see #3).
- [x] **Discoverable in Help** — `build_help_menu_view` hook; surfaced as an Economy child.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — ✅ **display logic now covered (punch #7, 2026-06-29).**
      `test_inventory_display_logic.py` pins `_build_combined_inventory` (two-table merge + summed
      overlapping keys · category grouping · rarest-first sort · unknown→Other · zero/negative drop ·
      empty→`{}`) and `_CategoryView` pagination (round-up, single-page nav suppression, empty-page
      render, footer position, prev/next boundary clamp). The navigation lifecycle stays covered by
      `test_economy_inventory_edit.py`.
- [x] **Authority tests** — view ownership via `BaseView` (inherited; no inventory-specific test).
- [N/A] **Mutation-seam tests** — no mutations in this unit (upstream workflows tested separately).
- [ ] **Live walkthrough recorded** — pending → punch #8.
- [ ] **Owner ✔** — pending → punch #9.

## Punch-list (clear these to certify)
1. **Item actions** *(owner, deepening)* — decide + build use / sell / trade / gift / equip (today the
   browser is read-only). Biggest completeness gap.
2. **Audit item grants** *(offline/owner, deepening)* — have `add_item` / mining `apply_inventory_deltas`
   emit an item-grant audit event so the item trail matches the coin trail.
3. **Capability enforcement** *(owner, minor)* — either enforce the declared `inventory.*` capabilities or
   remove the aspirational ones from the registry until their features exist.
4. **Item-detail density** *(offline, minor)* — multi-line / dedicated fields for large inventories.
5. **Sort / filter UI** *(offline, deepening)* — sort by qty/name/rarity, filter by type.
6. **Server configuration** *(owner, minor)* — decide whether items should be per-guild configurable; if
   so, add a SubsystemSchema.
7. ~~**Display-logic tests**~~ ✅ **DONE 2026-06-29 (dispatch run)** — `test_inventory_display_logic.py`
   covers the merge/sum/sort/group/unknown/zero-drop/empty + pagination-boundary paths (10 cases).
8. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + click-through (hub → category → page →
   back), with screenshots.
9. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/views/test_economy_inventory_edit.py` (navigation lifecycle) ·
  `tests/unit/cogs/test_inventory_display_logic.py` (display logic — 10 cases, punch #7) ·
  `tests/unit/invariants/test_no_view_level_purchase_writes.py`
- **Walkthrough:** pending (punch #8)
- **Owner sign-off:** pending (punch #9)

## Verdict
Inventory is a **correct, well-routed read-only item browser** (unified mining+economy view, paginated,
rarity-sorted, reachable via command/hub/Help). It is **the least mature** server-fn assessed so far on
the *ceiling* axis: it deliberately ships no item actions, item grants are unaudited upstream, the
declared mutation capabilities are unenforced placeholders, and there is no server config. The
display-logic test gap is now closed (punch #7, 2026-06-29). None of this is a safety hazard (it's
read-only), but a `◐ → ✔` path needs an owner decision on item actions + audit + capability cleanup
(#1–#3) before it is "done-done."
