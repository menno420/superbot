# 2026-07-01 — Inventory: item-detail density (rarity-tier fields) — completion deepening

> **Status:** `in-progress`

**Run type:** `routine · dispatch`

## What I'm about to do

Second slice of this dispatch run (first: logging ignored-lists #1594, merged). Advancing the S1
completion-deepening ▶ Next — **Inventory completion cert punch #4** (`item-detail density`,
`[offline, minor]`, `docs/planning/feature-completion/units/inventory.md`).

**Problem:** the `_CategoryView` detail page renders every item as one dense line
(`emoji **name** × qty ` + rarity + type`) in a single embed description — a wall of text for large
inventories.

**Scope (pure display logic, offline-testable):** in the **default rarity sort** (the dominant case),
render the page grouped into **per-rarity-tier embed fields** (Epic / Rare / Uncommon / Common /
Unknown), each field listing that tier's items — readable, dedicated fields per the punch, and
matching the active rarity ordering. In the explicit **quantity / name sorts** keep the flat single
description (so the field grouping never fights the chosen sort). Single-page/empty output stays
correct. Extend `test_inventory_display_logic.py`; no migration; self-merge on green.
