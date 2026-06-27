# Fishing-charm craft numbers (S1 acquisition-depth follow-up to #1504)

> **Status:** `reference` — the (sim-pinned) balance rationale for the fish→charm craft ladder.
> Source of truth is the code (`utils/fishing/gear.py` `CHARM_RECIPES`,
> `utils/mining/market.py` `GEAR_SHOP`); this doc records *why* the numbers are what
> they are and is pinned by `tests/unit/utils/test_fishing_gear.py`.

## What this is

The three CHARM-slot fishing charms were **coins-only** (bought from the mining gear
shop). #1504 made them *do* something (`fishing_power`/`bite_luck` → cast knobs); this
slice gives them a **non-coin earn path** — craft them from caught fish, mirroring the
existing catch→bait loop (`utils/fishing/bait.py` `CRAFT_RECIPES`). Coins stay the fast
alternative, exactly as starter mining gear (pickaxe/torch/lantern) is both buyable AND
craftable.

A recipe consumes `fish_count` caught fish whose `size_rank` is `≤ max_size_rank`
(smallest-first, via the shared `_plan_fish_spend` planner) and yields **one** charm into
the mining inventory; you then equip it from the gear panel (`!gear`).

## The ladder

| Charm | Stats (#1504) | Shop price (coins) | Craft cost (fish) |
|---|---|---|---|
| `fishing charm` | `fishing_power=2, bite_luck=1` | 90 | 8 fish (size ≤ 8) |
| `anglers charm` | `fishing_power=4, bite_luck=2` | 220 | 12 fish (size ≤ 14) |
| `master angler charm` | `fishing_power=6, bite_luck=3` | 420 | 18 fish (size ≤ 21 = any) |

`size_rank` runs 1 (smallest) … 21 (largest) across the catalog's 32 species.

## Why these numbers

- **Monotonic up the ladder** — a better charm costs strictly more fish AND accepts
  larger fish, so the top charm can absorb a deep haul. The pure test pins this.
- **The fish path is the *slow* path.** A charm wants many more fish than a bait pack
  (bait recipes are 3–6 fish; charms 8–18), because a charm is *permanent* gear, not a
  consumable pack. Grinding the fish is the cost; the coin price is the convenience.
- **Not free arbitrage.** Charms (like all gear/tools) are **not sellable** back to the
  market (`market.sell_price` only pays out for `RESOURCE`-kind items), so there is no
  craft-then-sell loop. And the fish a charm consumes sell for far less than the charm's
  shop price — the cheapest 8 eligible fish are worth ~30 coins sold vs the 90-coin
  `fishing charm` — so crafting stays the cheaper-but-slower path, never a coin mint.
- **Smallest-first spend** keeps the player's trophy catches: the planner drains the
  low-rank common fish a fisher accumulates before touching bigger ones.

## Where the loop closes

`catch (!fish) → craft (!craftcharm) → equip (!gear) → fish better`. This is the charm
sibling of the bait loop `catch → !craftbait → load → fish better`, sharing the same
`_plan_fish_spend` ingredient planner in `services/fishing_workflow.py`.
