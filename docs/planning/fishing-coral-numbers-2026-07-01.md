# Fishing coral + curios — pinned numbers (2026-07-01)

> **Status:** `living-ledger` — the tunable constants behind the coral rare-material
> drop and the cosmetic curio collection, with the rationale. Change a number here
> **and** in `tests/unit/utils/test_fishing_curios.py` in the same commit (the test
> pins these values), like the pearl/bonus-catch/gear number docs before it.

## What this is

The fishing rare-material pattern's **second** instance (S1 "▶ next offline
successor"). Mirrors the pearl (`docs/planning/fishing-pearl-numbers-2026-06-28.md`)
but the drop is **deepwater-only** and its sink is a **cosmetic collection** rather
than a bait.

- **coral** (`utils.fishing.rewards.CORAL_ITEM`) — a rare reel byproduct that only
  drops on a **deepwater** (boat) cast, giving that venue (#1340) a unique reward.
- **curios** (`utils.fishing.curios`) — cosmetic carvings crafted from coral
  (`ItemKind.TREASURE`: non-sellable, no gameplay effect). The reward is the
  *collection* — a completionist shelf like the Fishdex / trophy board.

## Drop chance (`utils/fishing/rewards.py`)

| Constant | Value | Rationale |
|---|---|---|
| `CORAL_DROP_CHANCE` | `0.06` | Per-reel chance in **deepwater**. Flat (coral is a reef find, not size-scaled like the pearl). Shore always `0.0`. |

Sizing: the pearl is `0.02`–`0.15` size-scaled (all venues). Coral at a flat `0.06`
is a little more generous per-reel *but only in deepwater*, where reels are slower
and riskier (22% base escape, 6–12 s bites) — so the effective coral-per-hour rate
is comparable to pearls, and it rewards the harder venue. Every carve costs
multiple coral, so the collection is a genuine long-tail.

## Curio recipes (`utils/fishing/curios.py`)

| Curio | Emoji | Coral cost | Rarity (cosmetic) | Net-worth value |
|---|---|---|---|---|
| Carved Coral Shell | 🐚 | 2 | Uncommon | 30 |
| Coral Seahorse | 🌊 | 4 | Rare | 60 |
| Coral Idol | 🗿 | 8 | Epic | 120 |
| Coral Leviathan | 🐉 | 16 | Legendary | 240 |

- **Doubling coral cost** (2 → 4 → 8 → 16) makes the **Leviathan** the top deep-sea
  trophy (the 2026-07-01 second-tier extension): ~30 coral for the full set, i.e.
  ~500 successful deepwater reels at 6% before the average player completes the
  shelf — deliberately long-tail, since it is pure cosmetic completion with no power
  attached. Each tier keeps the geometric ratio (cost ×2, value ×2), so the
  Leviathan is exactly twice the Idol on both axes.
- **`value`** is inventory net-worth display only (curios are `TREASURE`, so
  `market.sell_price` returns `None` — never sellable, no coin faucet).

## Invariants the tests pin

- Coral never drops on a **shore** cast (`roll_coral_drop(SHORE, …) is False`),
  drops at ≈ `CORAL_DROP_CHANCE` in **deepwater**.
- `commit_catch` grants coral only on a deepwater cast, in the same atomic
  transaction, and never writes a dex/trophy row for it.
- Curios are `ItemKind.TREASURE` and therefore **not** sellable
  (`market.sell_price("coral idol") is None`).
- `craft_curio` debits exactly `coral_cost` coral and grants exactly one curio;
  it refuses when the player lacks the coral.
