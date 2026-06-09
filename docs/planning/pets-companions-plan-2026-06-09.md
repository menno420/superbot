# Pet Companions — structured plan (mining-platform extension)

> **Status:** `plan` — structured from an idea; **not implementation approval**.
> **Horizon:** Later (games lane) — behind the Wave-1 keystone slices.
> **Source idea:** [`../ideas/fun-and-ease-brainstorm-2026-06-09.md`](../ideas/fun-and-ease-brainstorm-2026-06-09.md) §A1
> — the maintainer's ⭐ fun-cluster pick that session (router **Q-0053**).
> **Boundary:** ADR-002 unaffected (pets are durable DB state, not game sessions).

## Planning contract

- Source code, merged PRs, binding contracts, subsystem folios, and
  `docs/current-state.md` outrank this draft.
- Preserve domain-service mutation ownership, the direct-vs-draft lane rules,
  auditability, and the no-pay-to-win line (owner-vision §2a/§13).
- Before implementation, re-verify source, live PRs, the games folio, and the gates
  below.

## Context and objective

Pets give the mining character platform a **recurring emotional hook** plus the
economy's most-wanted mechanic: a **likeable coin/ore sink** (owner-vision §15 wants
sinks; the Workshop+durability slice is the keystone sink — pets are the *charming*
one). A rare egg found while exploring becomes a nameable companion on your
`!character` card; keeping it fed and happy costs ore/coins and grants tiny,
flavor-first perks. Pets are the owner's top pick from the 2026-06-09 fun/ease
brainstorm.

## Scope

- Egg drops from the existing exploration/mining loot path, rarity scaled by depth
  (riding "The Descent" #607).
- Hatch + name + display on the character card (#610).
- A care loop (feed with ore via the inventory owner, or coins via
  `economy_service`) with mood/growth — the recurring sink.
- Tiny non-pay-to-win perks (≤1–2%, e.g. explore luck while happy), composed through
  the shared pure stat seam.
- Spotlight showcase + optional pet-level leaderboard category (P4).

## Out of scope (explicit)

- **Pet battles** (would be a new game — separate idea if ever raised).
- **Breeding / marketplace trading** — deferred to the captured marketplace idea
  (`economy-marketplace-rewards-roadmap` §4); pets must be *ownable* first.
- XP multipliers or any gameplay-power perk beyond the flagged ceiling (no-P2W).
- Background schedulers for mood decay — mood is **computed lazily from
  `last_fed_at` on read** (no new task, no restart concerns).
- Cross-guild/account-wide pets — pets are per **(guild, user)** like all mining
  state (owner-vision §9 multi-tenancy); revisit only with an owner decision.

## Current state and verified seams to reuse

| Need | Existing owner (verified 2026-06-09) |
|---|---|
| Loot/drop path | `disbot/cogs/mining/exploration.py` event/loot tables; depth/biome from `cogs/mining/world.py` + `utils/db/games/mining_player_state.py` (#607) |
| Item taxonomy (eggs/food as non-sellable special items) | `cogs/mining/items.py` — combat gear in #608 set the "non-sellable, grouped" precedent |
| Coin mutations (feeding with coins) | **`services/economy_service.py` only** (`debit` + audit reason; #609 precedent) |
| Ore consumption (feeding with ore) | the mining inventory owner (direct-lane, like recipes/build) |
| Stat composition for perks | `utils/equipment.py` — pure `EffectiveStats` / `compute_stats` (#608); extend the pure function with an optional pet input, never a parallel stat path |
| Display | `views/mining/character_panel.py` (#610) — aggregates, owns nothing; add a pet line |
| Social surface | Community Spotlight (#613) EventBus feed — emit hatch/level-up events |
| Persistence pattern | `utils/db/games/mining_player_state.py` + migration 061 are the direct-lane template |

## Proposed phases (each ≈ one bounded PR)

1. **P1 — Egg & hatch (foundation).** Additive migration `player_pets`
   (guild_id, user_id, species, name, hatched_at, level, mood inputs `last_fed_at`
   etc.); egg drop wired into exploration loot with seeded-RNG tests (deeper biome →
   rarer species); hatch + naming modal; pet line on the character card. Pure species
   catalogue module (emoji/text presentation first — PIL stays a later idea, same as
   the character card).
2. **P2 — Care loop (the sink).** Feed with ore (inventory consume) or coins
   (`economy_service.debit`, audited reason `pets.feed`); lazy mood from
   `last_fed_at`; growth stages gated on cumulative care. Balance constants in one
   tunable table-in-code like `_GEAR`.
3. **P3 — Perks (balance-reviewed, gated).** Happy-pet bonus ≤1–2% explore
   luck/rare-find chance, composed via the pure stat seam; simulation-style tests
   pinning the ceiling; owner sign-off on the exact numbers before merge.
4. **P4 — Showcase & social.** Spotlight feed entries for hatches/growth; `!pets`
   showcase subpanel on the mining hub; optional leaderboard provider (pet level).
   Marketplace handoff stays with the marketplace plan.

## Dependencies and gates

- **Gate 1:** the Wave-1 keystone slices ship first (Workshop + durability, mother-panel
  live overview — `docs/current-state.md` ▶ Next action). Pets join the games lane
  *behind* them, or fold P1 into a Wave-2 batch.
- **Gate 2:** balance review — feeding cost vs. the post-Workshop faucet/sink picture
  (don't stack two new sinks blind; reuse its tuning evidence).
- **Gate 3:** owner promotion per `docs/ideas/README.md` (this plan structures; it
  does not approve).

## Risks and mechanics

Main risks: perk power creep (mitigated by the pinned ≤1–2% ceiling + tests), sink
mis-sizing (Gate 2), and species-catalogue scope creep (start ~6 species, one rarity
axis). Migration is additive; rollback = feature-flag the drop + panel (table stays,
harmless). No caches beyond existing read paths; invalidate nothing new. Tests:
seeded drop distribution, hatch idempotency, feed-debit through a mocked economy
seam, mood-from-clock with a fake clock, stat-ceiling pin, card rendering.

## Open questions (for the build/promotion session)

- Species/art direction: emoji-text presentation confirmed cheap; PIL card later?
- Exact perk ceiling and whether perks apply outside mining (recommend: mining-only
  first).
- One pet active at a time vs. a stable (recommend: one active, stable later with
  the showcase).
