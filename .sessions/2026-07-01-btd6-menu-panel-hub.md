# 2026-07-01 — BTD6 panel: Layout-B category hub (owner picked B)

> **Status:** `in-progress`

**Run type:** `owner-directed`

## What I'm about to do

Continuation of the menu-layout session (PR #1617 merged: round-range fix + the layout
simulator + design doc). The owner reviewed the simulator and **picked Layout B** (category
hub). Implement it in the live panel:

- Rebuild `BTD6PanelView` (`disbot/views/btd6/panel.py`) as an **8-category hub** (≤4 buttons/row
  per the mobile-truncation finding): 🧠 Ask (modal) · 🎯 Events · 🗼 Units · 🎲 Rounds & Economy ·
  🗺️ Maps & Modes · 📋 Strategy · 📊 Status · 🛠️ Admin. (Calculators + Challenge-Index categories
  are omitted — all-unbuilt `add` functions; they get their own future slices.)
- New `disbot/views/btd6/hub_panels.py` — ephemeral `BaseView` sub-panels per category, wiring the
  existing browsers (`open_tower_browser` / `open_hero_browser` / `open_paragon_calculator` /
  `open_live_events_browser` / `open_leaderboard_browser` / CT / maps / modes / status / strategy)
  + input modals for the previously-panel-invisible Rounds & Economy functions (Round/RBE/Income,
  Bloon lookup).
- Back-compat: reused custom_ids (`btd6:ask/events/maps/strategy/status/admin`) keep routing; the
  6 dropped leaf ids need a one-time panel **re-post** (`!btd6menu`) — noted for the owner.
- Tests: category buttons open their sub-panels; custom_ids stable; staff gating on Admin.

Every function stays ≤2 clicks; the top panel drops from a 13-button wall to 8 clean subdivisions.

## What shipped

_(filled in at close)_

## 📤 Run report

_(filled in at close)_
