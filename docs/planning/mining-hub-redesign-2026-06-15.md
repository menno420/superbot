# Mining hub redesign — declutter + grid Mine + open-world Explore (2026-06-15)

> **Status:** `plan` — owner-directed, live design session 2026-06-15 (Galaxy Bot#6724 test
> server). Captures the agreed information architecture so the build is turn-key. Cross-check
> source before implementing; the owner is the designer.

## Why

The mining hub grew to **16 buttons on one panel** ("way too much stuff on one game panel" —
owner, with screenshots). It must split into dedicated sub-hubs so the main panel is scannable
and each area has room to grow.

## Decision — Option A "Production hub" (owner-picked from rendered mockups)

Compared three layouts as image mockups; owner picked **Option A** ("best looking so far"),
with an exploration rework (below). Mental model: **act · you · make&trade**.

### Main hub — 6 buttons
`⛏️ Mine` · `🌲 Harvest` · `🗺️ Explore` · `🧍 Character` · `🧰 Gear` · `🔨 Workshop`

(Down from 16. Descend/Ascend, Inventory, Stats, Build, Workshop, Market, Vault, Recipes,
Skills, Forge all move into a sub-hub or into the Mine grid — see below.)

### Character hub — "everything about you" (owner-confirmed)
`🧍 Overview` (stat card) · `📦 Inventory` · `📊 Stats` · `🌳 Skills` · `🏦 Vault`

### Workshop hub — "make, repair & trade"
`🔨 Craft` · `🛠️ Repair` · `🔥 Forge` · `🛒 Market`

- **Craft consolidates Build + Craft + Recipes** into one entry (owner: "3 functions … that
  all do basically the same thing … consolidate into one"). They already share
  `mining_workflow.craft`; the recipe browser is the richer surface and subsumes the Build
  modal. Repair = the old Workshop repair flow; Forge = #905 gate; Market = buy/sell.

### Explore hub — open-world (NEW direction, stub for now)
A **separate open-world explorer**, **not tied to mine depth**: `🎣 Fishing` · `🧭 Roam` ·
`📜 Quests` · (more). **Exact commands undefined** (owner: "haven't been defined yet"). Ships
as a stub/"early" hub; fleshed out in its own design pass.

### Mine — 3D grid navigator (NEW world model, needs sign-off before build)
The Mine action gains **6 movement buttons** so the player roams and discovers a grid freely;
this **replaces** the old linear Descend/Ascend.

- Movement: `⬆️ North` · `⬇️ South` · `⬅️ West` · `➡️ East` · `🔼 Up` · `🔽 Down` + `⛏️ Mine here`.
- **Proposed v1 (awaiting owner confirm):** a finite grid per depth level — N/S/E/W roam the
  current level (each cell rolls its own resource odds + occasional event/treasure, revealed on
  visit = light fog-of-war); Up/Down change depth (old `0–3` becomes the z-axis, still gated by
  light, deeper = richer); `Mine here` digs the current cell.
- **Open design questions:** one shared grid vs. per-level · fixed size vs. procedural/infinite ·
  do moves cost a turn / trigger encounters · how cell yields relate to the existing depth-band
  tables (`utils/mining/world.py`, currently 1-D depth).
- **World model — DECIDED (owner, Q-0173, 2026-06-17):** a **seed-deterministic procedural grid we
  generate ourselves** — any number ("seed") feeds our own generator, so `seed 12345` gives everyone
  the same world (deterministic · **shareable** · effectively infinite). This resolves "fixed vs
  procedural/infinite" above → **procedural.** NOT literal Minecraft terrain (no API fetches it;
  replicating it needs Cubiomes for biomes — a *later* upgrade — or a Java generator, rejected as too
  heavy for Railway). The other open questions above stay owner-pending.

## Build order

1. **PR 1 — in-place image cards** ✅ (PR #911) — inventory/gear cards stop stacking as
   ephemerals (independent; already green).
2. **PR 2 — hub declutter** (confirmed, turn-key): main hub → the 6; new **Character** +
   **Workshop** sub-hubs; **Craft** consolidation; **Explore** stub. Mine keeps current
   behaviour as an interim (Descend/Ascend fold into the Mine action, off the main hub) until
   PR 3. *Best done live with the owner once the test-bot token is restored.*
3. **PR 3 — grid Mine** (new mechanic): the (x,y,z) world model + 6-direction movement +
   discovery. Needs the v1 sign-off above first.
4. **Later — open-world Explore**: fishing / quests / roam — own design pass.

## Source anchors

- Hub + sub-hubs: `disbot/views/mining/main_panel.py` (the `MiningHubView` PersistentView) +
  `gear_panel.py` · `market_panel.py` · `vault_panel.py` · `skills_panel.py` · `forge_panel.py`
  · `workshop_panel.py` · `recipe_browser.py` · `character_panel.py`.
- World model (for the grid): `disbot/utils/mining/world.py` (currently linear depth).
- All mining writes go through `disbot/services/mining_workflow.py` (RS02 boundary) — the grid
  movement must too.
- Folio: `docs/subsystems/games.md`; lane plan:
  `docs/planning/mining-structures-skill-tree-plan-2026-06-14.md`.

## Mockups

Rendered comparison images (Option A/B/C + the revised Option A with grid Mine + open-world
Explore) were shared in the live session; the renderer is throwaway (`/tmp/mockups/`). Re-render
from the IA above if needed.

## Design standard this produced

The Category → Type → Variant browser and the hub → sub-hub → panel tree are two instances of one
pattern. It is codified as the **3-layer menu doctrine** (owner directive, 2026-06-15) in
[`../building-roadmap/hub-ui-standard.md`](../building-roadmap/hub-ui-standard.md)
§ "The 3-layer menu doctrine (navigation depth)" — the standard for **any** new menu in the bot:
divide a crowded surface into ≤3 small levels (Category → Type → Variant), each an in-place
`HubView` page with per-level back nav, never a flat list or pagination.
