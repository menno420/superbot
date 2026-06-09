# Mining Character overview (§7.6 profile seed)

**Branch:** `claude/mining-character` (stacked on #609) · **Date:** 2026-06-09

Fourth slice of the session ("continue with the plan for as long as you can"). After the
Descent (#607), combat gear (#608), and the market (#609), this is the read-only **Character
overview** — the brainstorm §7.6 profile card's stat-card-first step, done as an embed.
Deliberately picked a *safe, contained* slice (no migration, no mutation, no money) for this
depth in the session; the remaining Wave-1 work (durability/Workshop) carries a migration and
is better with fresh capacity.

## What shipped
- **`views/mining/character_panel.py`** — `build_character_embed(user_id, guild_id)`: a pure
  aggregation that **owns no data**. It composes from the existing owners: position
  (`cogs.mining.world`), equipped gear + `EffectiveStats` (`utils.equipment`), coins (the
  economy `db.get_coins`), and inventory net worth (`cogs.mining.items`).
- **`!character`** (aliases `!profile`, `!char`) + a hub **🧍 Character** button (shown
  in-place on the hub). One builder, shared by both — no duplicate composition.
- Because it reads each owner, it grows for free: when game-XP / skills / titles land, they
  slot into the same embed.

## Verification
- `check_quality.py --full`: **8259 passed**, 0 fail. `check_architecture --mode strict`:
  **0 errors**, 0 new warnings. Live boot clean (commands register, 0 errors).

## Notes
- This is the §7.6 *stat card first* step as an embed; the PIL card + paper-doll remain the
  later visual-roadmap steps.
- It overlaps `!gear` + `!minestats` by design (it's the unified view); those stay for now —
  consolidating is a later cleanup, not worth the churn/test-pin disruption now.
- Mixed user-id types remembered: mining/depth/equipment use `str(user_id)` (TEXT columns),
  coins use `int(user_id)` (the `xp` BIGINT column). The builder handles both.

## Context delta
- Everything needed was already shipped this session (world/equipment/items/economy owners),
  so this was pure composition — the payoff of building the platform seams first.
- **Promote-now gap (flagged in all four slices):** there's still no "testing Discord
  views/panels" note in the games folio. Each slice re-derived how to drive a button/select
  callback or mock a panel's DB reads in a unit test. This has earned promotion — next
  session should add a short testing-views section to `docs/subsystems/games.md`.
