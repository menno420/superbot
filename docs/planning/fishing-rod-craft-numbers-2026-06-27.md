# Fishing fish→rod craft numbers (S1 acquisition-depth follow-up to #1508)

> **Status:** `reference` — the balance rationale for the fish→rod craft ladder.
> Source of truth is the code (`utils/fishing/rods.py` `ROD_RECIPES` / `ROD_LADDER`);
> this doc records *why* the numbers are what they are and is pinned by
> `tests/unit/utils/test_fishing_rods.py`.

## What this is

The rod ladder was **coins-only** (`fishing_workflow.buy_rod` — each tier requires the
one below + a coin price). This slice gives the ladder a **non-coin earn path** —
`!craftrod` crafts the next rod up from caught fish, mirroring the existing fish→charm
(`utils/fishing/gear.py` `CHARM_RECIPES`, #1508) and catch→bait
(`utils/fishing/bait.py` `CRAFT_RECIPES`) loops. Coins stay the fast alternative, exactly
as the charms and starter mining gear are both buyable AND craftable.

A recipe consumes `fish_count` caught fish whose `size_rank` is `≤ max_size_rank`
(smallest-first, via the shared `_plan_fish_spend` planner) and raises the owned rod tier
by one. Like `buy_rod`, `craft_rod` crafts the *next* tier from the one you own, so a
fisher works up the ladder by fishing.

## The ladder

| Rod (tier) | Coin price | Craft cost (fish) |
|---|---|---|
| 🥉 Bronze Rod (1) | 250 🪙 | 10 fish (size ≤ 6) |
| 🥈 Silver Rod (2) | 750 🪙 | 16 fish (size ≤ 12) |
| 🥇 Gold Rod (3) | 2000 🪙 | 26 fish (size ≤ 18) |
| 💎 Diamond Rod (4) | 5000 🪙 | 40 fish (size ≤ 21 = any) |

The starter (🎣 Bare Rod, tier 0) is free and uncraftable. `size_rank` runs 1 (smallest)
… 21 (largest) across the catalog.

## Why these numbers

- **Monotonic up the ladder** — a better rod costs strictly more fish AND accepts larger
  fish, so the bigger catches a higher rod lands can feed the next rod. The pure test pins
  this.
- **The fish path is the *slow* path, and pricier than a charm.** A rod is the marquee
  progression axis, so a rung wants many more fish than a charm (charms 8–18; rods 10–40).
  Grinding the fish is the cost; the coin price is the convenience.
- **Not free arbitrage.** Caught fish that feed a rod are common low-rank catches worth
  far less sold than the rod's coin price — the cheapest 10 eligible fish are worth a few
  dozen coins sold vs the 250-coin Bronze rod — so crafting stays the cheaper-but-slower
  path, never a coin mint. Rods carry no resale value of their own (they're a tier flag,
  not a sellable item), so there is no craft-then-sell loop.
- **Smallest-first spend** keeps the player's trophy catches: the planner drains the
  low-rank common fish a fisher accumulates before touching bigger ones.

## Where the loop closes

`catch (!fish) → craft (!craftrod) → cast better`. This is the rod sibling of the charm
loop `catch → !craftcharm → equip → fish better` and the bait loop `catch → !craftbait →
load → fish better`, all sharing the same `_plan_fish_spend` ingredient planner in
`services/fishing_workflow.py`. Surfaced in the rod shop (`!rod`) as the **🎣 Craft from
fish** button beside **⬆️ Upgrade rod**, with the craft cost advertised in the embed.
