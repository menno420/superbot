# Mining market — sell ore / buy gear (Wave 1 economy loop)

**Branch:** `claude/mining-market` · **Date:** 2026-06-09

Third slice of the session (after #607 Descent + #608 combat gear, both merged). The
maintainer said "continue with the plan for as long as you can," so I took the next
Wave-1 slice: the **economy loop** — sell raw resources for coins (faucet), buy gear
with coins (sink), closing *mine → sell → upgrade → descend*.

## What shipped
- **`cogs/mining/market.py`** — the market domain module:
  - *Pure pricing:* `sell_price` (only **explicitly-catalogued resources** sell — reuses
    `items.item_value`, one source of truth), `GEAR_SHOP` (tunable coin catalogue),
    `sellable_inventory` / `total_sale_value` / `shop_listing`.
  - *Orchestration:* `apply_sell` / `apply_sell_all` / `apply_buy` — the **only** place
    mining touches money. Coins move exclusively through the audited
    `services.economy_service` (`credit`/`debit` → audit row + balance event); the
    inventory side stays direct-lane. One implementation, shared by cog + view (DRY).
- **`views/mining/market_panel.py`** — `MiningMarketView` (Sell-All button + buy-gear
  `Select` + back-to-hub) + a `🛒 Market` button on the persistent hub.
- **Commands:** `!sell <item> [n]`, `!sellall`, `!buy <item>`, `!market`.
- **Item taxonomy:** combat gear (`sword`/`iron sword`/`shield`/`armor`) added to
  `items._CATALOG` as TOOL so it groups under Tools, counts toward net worth, and is
  **non-sellable** (TOOL, not RESOURCE).
- **No new layer debt:** `market.py` is a `cogs`-layer module (may import services + utils);
  the view lazy-imports it (views→cogs rule). `economy_service` is reached cog→services /
  via the market module — clean.

## Verification
- `check_quality.py --full`: **8257 passed**, 0 fail. `check_architecture --mode strict`:
  **0 errors**, 0 new warnings.
- **Live boot:** clean — market commands register (no `!shop` collision after dropping that
  alias), 0 errors.
- **Live money round-trip** (real DB, throwaway script): sell 2 diamond → **+24** coins (1
  left); buy iron sword → **−60** + item granted; buy armor while broke (64<70) → **rejected,
  coins unchanged**. The audited credit/debit + inventory integration is correct.

## Learnings / gotchas
- **`items.classify` defaults unknown → RESOURCE**, which made *combat gear and any
  uncatalogued item sellable* in the first cut (caught by my own market tests). Fixed two
  ways: `sell_price` now sells only items that are **explicitly** RESOURCE via
  `items.lookup` (no minting coins from junk), and combat gear was added to the taxonomy.
  Lesson: a permissive default classification becomes a money bug the moment a feature keys
  off it.
- **`!shop` is taken by the economy cog** — my `aliases=["shop"]` on `!market` would be a
  `CommandRegistrationError` at load (bot won't start). Grep existing command names/aliases
  before adding one. Removed the alias.
- **Money has no cross-store transaction** (coins live in `xp`, inventory in
  `mining_inventory`, separate modules). Each op is ordered to favour *no exploit* over *no
  harm*: sell removes ore **before** crediting; buy debits **before** granting. The window
  is one await on the same DB — acceptable for best-effort game state (ADR-002), documented
  in the module. A future audited "market service" with a shared txn is the someday-fix.
- **Formatter dance:** black + ruff(COM812) both needed a pass on the new files
  (`ruff --fix` then `black`), then `check_quality --check-only` settled green. The
  PostToolUse auto-format hook doesn't fire in this container — run the fixers yourself.

## Next steps (Wave 1 remainder)
- **Audited Workshop + durability** — durability is the keystone recurring sink (§7.5) that
  makes the market matter long-term (gear wears → buy/repair). Likely the point a real
  `services/`-level market/crafting seam (shared txn) becomes warranted.
- **Mother-panel live overview** (§6.3) — the hub embed is still static; show depth/biome/
  gear/coins/net-worth at a glance.
- Then Wave 2 (game-XP + skills + profile card).

## Context delta
- **Well-pointed:** `economy_service`'s docstring (credit/debit/InsufficientFundsError) and
  `views/economy/shop_panel.py` (an existing buy-select + audited-debit pattern) made the
  money seam + UI obvious; brainstorm §7.2/§7.5 had the faucet/sink design decided.
- **Found by hand:** the `items.classify` unknown→RESOURCE default being a sell-money hole
  (only surfaced by writing the tests); the `!shop` name collision (grep, not documented).
- **Reaffirmed gap (3rd session running):** still no "testing Discord views/panels" note in
  the games folio — view callbacks + panel buttons keep needing bespoke mock setups. Worth
  promoting now; I've hit it in all three mining slices this session.
