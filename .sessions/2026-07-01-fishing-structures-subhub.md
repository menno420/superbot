# 2026-07-01 — Fishing structures sub-hub (🏗 Structures child) + completion-deepening

> **Status:** `in-progress`

**Dispatch run (routine · dispatch), no explicit work order — advancing the next offline plan slice.**
The `2026-07-01-fishing-dock-sail-alias-crash` handoff named the ▶ next offline successor: the
fishing menu now carries two structure buttons (🪸 Tide Pool + ⚓ Dock) and needs a **"🏗 Structures"
sub-hub** so the menu stays lean as more structures land. Building that this run, then continuing
with further completion-first deepening as capacity allows.

## Plan
- New `views/fishing/structures_hub.py` — `StructuresView` (🪸 Tide Pool · ⚓ Dock · ↩ Fishing menu),
  `build_structures_embed` (both structures at a glance), `open_structures_hub` (the panels' back target).
- `menu.py` — replace the two structure buttons with one **🏗 Structures** button opening the sub-hub.
- `tide_pool.py` / `dock.py` — back button → the Structures sub-hub (canonical parent).
- Tests for the new sub-hub + updated back-nav.

_(Will fill in verification + enders and flip to `complete` as the final step.)_
