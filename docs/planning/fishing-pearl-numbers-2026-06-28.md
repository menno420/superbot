# Fishing — pearl rare-material numbers (sim-pinned, 2026-06-28)

> **Status:** `living-ledger` — sim-pinned balance numbers (the pearl drop + its bait sink).
>
> Companion to the fishing economy number docs
> ([gear](fishing-gear-numbers-2026-06-27.md) · [charm craft](fishing-charm-craft-numbers-2026-06-27.md) ·
> [rod craft](fishing-rod-craft-numbers-2026-06-27.md) ·
> [bonus catch](fishing-bonus-catch-numbers-2026-06-27.md)). Pins the **pearl**
> rare-material drop + its premium-bait sink so a later balance change is a
> deliberate, reviewed edit — not a silent drift. Source of truth:
> `utils/fishing/rewards.py` + `utils/fishing/bait.py`; the test mirror is
> `tests/unit/utils/test_fishing_rewards.py` and
> `tests/unit/services/test_fishing_workflow.py`.

## What the pearl is

A **pearl** (`utils.fishing.rewards.PEARL_ITEM = "pearl"`) is a dedicated rare
crafting material a *successful reel* can also yield — distinct from the lucky
double-catch (#1515), which drops a second **fish**. A pearl is its own inventory
item in the shared `mining_inventory`; it is **never** a catch-log / dex / trophy
row. Its sole sink is the pearl-only craft path for the premium **Royal Feast**
bait (the one bait deliberately left with no fish recipe), so the rare drop has a
**repeatable** home (bait is consumed → pearls never go dead) while coins stay the
fast alternative.

## The drop chance (size-scaled)

`pearl_drop_chance(size_rank)` = `BASE + PER_RANK × (rank − 1)`, capped at `MAX`:

| Constant | Value |
|---|---|
| `PEARL_DROP_BASE_CHANCE` (smallest fish, rank 1) | `0.02` (2%) |
| `PEARL_DROP_PER_SIZE_RANK` | `0.004` (+0.4pp / rank) |
| `PEARL_DROP_MAX_CHANCE` (ceiling) | `0.15` (15%) |

Worked points (size ranks span ~1–21 across the shore + deepwater pools):

| `size_rank` | chance |
|---|---|
| 1 (minnow-tier) | 2.0% |
| 6 | 4.0% |
| 11 | 6.0% |
| 21 (trophy-tier) | 0.02 + 0.004×20 = **10.0%** |
| 40 (hypothetical, clamped) | 0.15 (cap) |

So a trophy haul is ~5× likelier than the smallest fish to yield a pearl, and even
the largest fish can never make pearls common. The roll is drawn **after** the
bonus-catch roll on the shared `rng` (documented order, for seed-determinism).

## The sink — pearls → premium bait

`PEARL_BAIT_RECIPES` (in `utils/fishing/bait.py`) keys a bait by the pearls it
costs. Only baits with **no** fish recipe belong here, so the two earn paths never
overlap:

| Bait | Pearls / pack | Coin price (the fast alt.) | Charges |
|---|---|---|---|
| Royal Feast (`feast`) | **4** | 1800 🪙 | 10 |

### Why 4 pearls

At an average mid-pool drop chance of ~5%, a pearl is roughly one per 20 successful
reels, so a Royal Feast pack (4 pearls) is roughly an 80-catch investment — clearly
the *slow*, gameplay-native path next to the 1800🪙 coin buy, mirroring how the
fish-craft shelves price a charm/rod far above casual sell value. A dedicated fisher
earns the top bait by fishing; a coin-rich player just buys it. The number is a
tunable constant — bump `PEARL_BAIT_RECIPES["feast"]` to make the earn path slower.

## Invariants the tests pin

- `pearl_drop_chance` is monotonic non-decreasing in `size_rank`, equals `BASE` at
  rank ≤ 1, and never exceeds `MAX`.
- `commit_catch` grants exactly one pearl **iff** the pearl roll fires; the fish
  grant stays the **last** `update_mining_item` call (stable seam); the dex/trophy
  row is unaffected; byte-identical inventory when no pearl drops.
- `craft_pearl_bait` debits exactly `PEARL_BAIT_RECIPES[key]` pearls and loads the
  bait in one transaction; refuses (no debit) when the player has too few pearls or
  the bait has no pearl recipe; stacks charges on the same bait.
