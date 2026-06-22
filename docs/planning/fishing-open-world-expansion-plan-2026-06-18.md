# Plan — Fishing + the boat / open-world expansion (the unified-character world)

> **Status:** `plan` — owner design brain-dump 2026-06-18 (**Q-0175**). Fishing is the canonical
> **Q-0172** self-build candidate (the ratified ecosystem-#2 verdict, V-14). **The owner is the
> designer — this captures his vision faithfully; verify against source + the owner before building.**
> **Phase 1 is buildable now; Phase 2+ is explicitly "later, not now"** (captured so it isn't lost —
> owner: *"this should be documented before I forget… this should give the planners something to do"*).

## The vision (owner, 2026-06-18)

One character does everything (mining · fishing · exploration · …); you swap **gear types** easily;
fishing adds **real, size-ranked fish**; and a **boat** becomes a second home base that **travels** to
**real destinations** (coordinates + biome), each with its own specialty. Everything ties to the one
cross-game character — the V-13 paper-doll that "later holds the fishing rod."

## Phase 1 — Fishing v1 (the buildable starting point)

**Fish set — 21 fish, ranked by size.**
- A curated **21-fish** dataset, each with a **size rank** (1 = smallest … 21 = largest) + name (value /
  flavour can come later). Like the BTD6 / gear data: a committed JSON the game reads.
- **7 levels, 3 fish per level (by size).** Your **starting rod / character catches the 3 smallest**
  (level 1); each level up unlocks **+3** bigger fish in steps of 3 → **7 levels to catch all 21**
  (`3 × 7 = 21`). (The owner started at "20" then rounded to **21** precisely so it divides into 7
  clean levels.)
- **Scales later:** more fish + levels append cleanly (21 / 7 is the *starting point*, not a cap).
- Leveling = a **fishing level / rod-tier ladder** — reuse the existing tier ladder (`bronze…diamond`)
  and/or the `game_xp` skill level; the planner picks the cleanest fit (don't invent a parallel system).

**One character, swappable gear types (the unified-loadout model).**
- **One character** holds everything (the existing `utils/equipment.py` slots + the `character_render`
  doll). New concept: **named loadout presets per activity type** — mining · fishing · exploration · …
  — each with its own **deterministic saved slot**. *"Put on fishing gear"* swaps your equipped items to
  your saved fishing loadout.
- **Gear is never required.** Any activity works with whatever you're wearing; the **matching** gear just
  **increases the bonuses** (fishing gear → better fishing, etc.). Switching is an *optimization*, not a
  gate.

## Phase 2+ — the boat + open world (LATER — captured, not for now)

**The boat = a second home base.**
- Stores your **rods**; is **not** fishing-only — also the hub for **exploration** travel. A sibling of
  the mining **Home** structure (likely on the `mining_structures` seam).

**Boat travel — a bounded timer + locked-in.**
- Pick a destination → a **timer** ("on your way to …"), **never hours/days** (short, bounded). While
  traveling you are **locked in the boat**: you **can fish** + do "boat stuff" (TBD by the owner), but
  **cannot** do land-locked things (mining, etc.), and **cannot leave until you arrive.**

**Destinations = real coordinates + biome.**
- A few destinations to choose from; arriving **updates your coordinates + your "biome."** Ties to the
  **seed-deterministic grid world (Q-0173)** — destinations are real points in that world.
- **Each place has a specialty** (e.g. one a great **farm** spot, another a great **mine**). Locations
  grant **bonuses for certain things**; **some** features become **location-locked** *eventually* — not
  all (the owner was explicit: bonuses first, hard location-locks only for a few, later).

## Connections to existing systems (build on these, don't duplicate)

- **The one character / paper-doll** — `utils/equipment.py` (slots/stats) + `utils/character_render.py`
  (the doll; V-13: "the same doll later holds the fishing rod"). Loadout-presets extend equipment.
- **The world / coordinates / biome** — the **seed-deterministic grid (Q-0173**, mining-hub-redesign PR3).
- **The boat as a structure** — the mining structures seam (`mining_structures`, `build_structure`).
- **Leveling** — the shared `game_xp` / skill-tree systems.
- **Where it surfaces** — the mining-hub-redesign **Explore hub** (`🎣 Fishing · 🧭 Roam · …`, currently a
  stub) is fishing's home panel.
- **Lineage** — V-13 (multi-ecosystem open world) + the V-14 ecosystem-#2 = **FISHING** verdict, now concrete.

## Open design questions (for the planner / owner — do NOT decide unprompted)

> **Update 2026-06-22:** the **catch-mechanic** question below is now explored with data in
> **`docs/planning/fishing-minigame-design-2026-06-22.md`** — a simulation
> (`tools/sim/fishing_minigame_sim.py`) of the `cast → wait → BITE → reel` loop, the fair reaction
> window, bite timing, the rod-upgrade ladder, and the shore-vs-deepwater split. It recommends a
> direction and routes the remaining feel/scope calls back to the owner.

- **Catch mechanic:** a deterministic roll (like `explore`)? a minigame? what picks *which* fish within
  your unlocked size-band, and what determines success?
- **Leveling:** a dedicated fishing rod-tier ladder, a fishing skill in the skill tree, or both?
- **Loadout presets:** which activity types exist at v1 (mining/fishing/exploration)? the save/switch UI.
- **Fish value / use:** sell? cook (ties the survival-plan P3 food loop)? collection goals / records?
- **Boat "stuff":** what else you do while traveling (owner hasn't decided yet).
- **Phase split:** confirm Phase 1 (fishing + gear-switching) ships before Phase 2 (boat / world).

## Build order (suggested — Phase 1 first)

1. **Fishing v1** — the 21-fish JSON + the level/size-band catch on the Explore hub's `🎣 Fishing`
   (reuse the `cogs/mining/exploration.py` resolve seam). No boat yet (fish from shore / the hub).
2. **Unified loadout presets** — saved gear-type slots + "put on X gear" swap (extends equipment).
3. **The boat structure** + **travel timer + locked-in** behaviour (Phase 2).
4. **Destinations + biome + location specialties / bonuses** (Phase 2+, ties Q-0173).

## Source anchors

- `disbot/utils/equipment.py` (slots/stats) · `disbot/utils/character_render.py` (doll) ·
  `disbot/cogs/mining/exploration.py` (the explore resolve seam) · `disbot/views/mining/main_panel.py`
  (the hub) · `disbot/utils/mining/structures.py` + `mining_structures` (boat-as-structure) ·
  `disbot/utils/mining/world.py` (depth → the grid world, Q-0173) · `disbot/data/` (the fish JSON home).

## Verification / rollback

Docs-only capture; fully reversible. Each phase is an additive game feature (ADR-002: game state is
not restart-safe — accepted). Phase 1 is data + a hub action + the loadout-preset extension; nothing
here touches money/safety seams. Build against the owner's answers to the open questions above.
