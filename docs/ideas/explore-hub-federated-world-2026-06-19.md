# The Explore hub — a federated open world (one world, each subsystem its own game)

> **Status:** `ideas` — **owner-directed (2026-06-19, brainstorm).** Not a plan, not approval; capture of
> the owner's framing so a dedicated planning session starts from it. Source + the binding contracts win.
> **Subsystem:** games, mining, fishing — the federated open-world spine.

## The owner's framing (verbatim intent)

> *"a bit of survival/RPG as well as adventure and quests, each subsystem like mining and fishing etc
> should be part of one world but also should feel like their own game."*

## Why this is the missing spine

Mining, fishing, pets, and RPG-survival are each planned as **separate lanes** today
([fishing](../planning/fishing-open-world-expansion-plan-2026-06-18.md) ·
[mining-hub-redesign](../planning/mining-hub-redesign-2026-06-15.md) ·
[rpg-survival](../planning/rpg-survival-difficulty-design-2026-06-10.md) ·
[pets-companions](../planning/pets-companions-plan-2026-06-09.md)). They all *want* to plug into a shared
world that **doesn't exist yet** — so defining that world is the single highest-leverage design move: one
decision homes four gated lanes.

## The principle: a **federated** world

- **Shared (the "one world" half):** one character, one economy/currency, the shared `game_xp` track, a
  light **survival/RPG + adventure/quest overlay**, and an **Explore hub** that acts as the "town square"
  you walk out from into each game.
- **Distinct (the "its own game" half):** each subsystem stays a **complete, satisfying game on its own** —
  you can just fish, or just mine, and it feels whole without the rest.

This already matches the in-flight direction: the fishing plan (Q-0175) reuses `game_xp`, a unified
character, and swappable gear-type loadouts — i.e. it was *already* drifting toward "one character across
games." This idea codifies that into an explicit world model instead of letting each lane re-decide it.

## Open design questions (for the dedicated planning session — do not decide unprompted)

1. **What the hub *is*** — a Discord HubView that routes into each game (Mine · Fish · Explore · …), or a
   richer map/location model with destinations/biomes that gate which game is reachable where?
2. **How the survival/adventure overlay attaches** without forcing it on cozy players — difficulty modes
   (Easy ≡ today's game, byte-identical, per the rpg-survival plan), opt-in stakes, quests as optional goals.
3. **Where each existing subsystem docks** into the hub (mining-hub-redesign Option A already splits into
   sub-hubs — the Explore hub is the parent of those).
4. **Cross-game identity** — a single profile that characterizes a player across games (the per-user
   identity seed) is the natural front-end for this world.

→ relates [fishing-open-world-expansion-plan](../planning/fishing-open-world-expansion-plan-2026-06-18.md) ·
[mining-hub-redesign](../planning/mining-hub-redesign-2026-06-15.md) ·
[rpg-survival-difficulty-design](../planning/rpg-survival-difficulty-design-2026-06-10.md) ·
[pets-companions](../planning/pets-companions-plan-2026-06-09.md) · the [games folio](../subsystems/games.md).
