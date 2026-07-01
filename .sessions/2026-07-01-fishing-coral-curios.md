# 2026-07-01 — Fishing: coral 🪸 deepwater rare-material drop → cosmetic curio collectibles

> **Status:** `in-progress`

**Run type:** `routine · dispatch`

## What I'm about to do

Scheduled dispatch fire, no work order. Both FIX-backlog bugs are gated (BUG-0019 #1 = owner
design fork; BUG-0009 remainder = data-gated on release-order source), so I take the next real
plan slice under S1's completion-first posture: the **fishing rare-material successor** — the
explicit `[offline]` "▶ Next offline successor" in `docs/current-state/S1-bot.md`.

Mirror the pearl pattern (#1518) with a **second** rare reel-drop material feeding a **new,
non-bait craft target** (the roadmap's "a dedicated craft material that feeds a *new* craft
target rather than the premium bait — e.g. a cosmetic or a structure"):

- **coral 🪸** — a rare reel-drop material, **deepwater-venue-gated** (thematic reef find; also
  gives the boat venue #1340 a unique payoff — deepens an existing feature). Mirrors the pearl:
  stored in the generic `mining_inventory` (no migration), never a dex/trophy row, byte-identical
  economics when it doesn't drop.
- **Curios** (`utils/fishing/curios.py`) — cosmetic **carving collectibles** crafted from coral
  (`ItemKind.TREASURE` → non-sellable, no crafting use), a completionist collection like the
  Fishdex/trophies. Shown by the **existing** inventory browser (no new panel) + a `!curios`
  list + `!craftcurio`. Also catalogues coral + the pre-existing (uncatalogued) pearl for clean
  display — fix-on-sight drift.

No migration, no minigame-view mechanic wiring, pure + sim-pinnable, self-mergeable. Deepens two
completion units (fishing + inventory).

Aim: 2–3 slices — this material→collection slice first; then a second plan slice if budget allows.

## What shipped

_(to be filled at close)_
