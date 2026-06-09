# Economy, Marketplace, and Rewards — roadmap draft

> **Status:** `plan` — planning/routing draft; not implementation approval.
> **Horizon:** Later. **Primary source:** `docs/ideas/owner-vision-ideas-2026-06-08.md` §2, §12–15, §23.
> **Owner decision Q-0039 — answered (2026-06-09, router):** donation benefits =
> **cosmetic identity + supporter recognition only**; convenience/progression perks only
> on the earned milestone track; supporter status read from an externally-managed
> Discord role — **SuperBot stores/processes no payment data**. Decides the fairness
> boundary only; the VIP phase still needs economy-health evidence + promotion.

## Planning contract

- **Status:** roadmap draft; routing only, not approval and not an active implementation lane.
- Source code, merged PRs, binding contracts, subsystem folios, and `docs/current-state.md` outrank this draft.
- Preserve domain-service mutation ownership, direct-vs-draft lane rules, deterministic event flow, auditability, rollback safety, observability, cache invalidation, and testability.
- Before implementation, re-verify source, live PRs, the relevant folio, and every named gate.

## Context and objective

This draft groups marketplace trading, mining trade goods, cosmetics/titles, collectibles, streaks, chance rewards, coin sinks, starter onboarding, VIP tiers, and blueprint crafting behind the existing economy authority. The objective is a coherent, auditable economy rather than independent reward and trade mutation paths.

## Scope

Player listings/trades; mining resources as goods; non-gameplay cosmetics/titles and collectibles; currency/cosmetic/lottery streak rewards; transparent coin sinks; starter packs and first-run economy guidance; and future blueprint-drop crafting. VIP's fairness boundary is decided (Q-0039, 2026-06-09: donation = cosmetic + recognition only; no billing in the bot); the VIP phase itself still needs promotion.

## Out of scope

Pay-to-win boosts, XP multipliers, gameplay advantages from donations, opaque gambling mechanics, or direct balance writes outside `economy_service`.

## Current state and seams to reuse

`disbot/services/economy_service.py` is the mutation seam; existing economy, inventory, mining, leaderboard, and audit DB helpers are the source-verification starting points. Mining recipes/items already exist and must be extended rather than replaced. Existing panel/view standards own UI composition.

Likely roots: `disbot/services/economy_service.py`, `disbot/cogs/economy_cog.py`, `disbot/cogs/inventory_cog.py`, `disbot/cogs/mining/`, `disbot/cogs/mining_cog.py`, `disbot/utils/db/games/`, economy audit migrations, and economy/inventory views.

## Proposed phases

1. **Economy health and vocabulary:** measure faucets/sinks, define item identity/transferability, audit reasons, anti-abuse and rollback contracts.
2. **Safe onboarding/reward slice:** starter pack and deterministic streak ledger with idempotent claim; lottery remains disabled pending chance-reward review.
3. **Cosmetic/collectible ownership:** non-gameplay catalog and display bindings.
4. **Marketplace:** atomic listing/escrow/purchase/cancel flows with fees as explicit sinks.
5. **Mining/crafting integration:** tradeable resources and blueprint drops only after mining balance and item ownership are stable.
6. **VIP decision follow-up:** only benefits explicitly approved through Q-0039 and technically enforced as non-pay-to-win.

## Dependencies and gates

Economy balance evidence; item ownership/source-of-truth decision; anti-fraud/rate-limit review; chance-reward legality/product review; Q-0039; and social/guild treasury semantics before shared-bank trading.

## Risks and mechanics

High risk: duplication exploits, race conditions, inflation, fraud, chargeback/donation coupling, and irreversible item transfers. Use transactions/idempotency, append-only audit reasons, explicit cache invalidation, additive migrations, admin reconciliation reads, and feature flags/safe-disable. Rollback must compensate through the economy owner, never rewrite balances ad hoc.

## Migration, cache, audit, rollback, and test implications

Add item/listing/reward schemas incrementally with reconciliation/backfill plans. Invalidate wallet, inventory, listing, and profile reads on canonical mutations. Audit every transfer, claim, fee, sink, and compensation with stable reason codes. Rollback uses disable plus economy-owned compensating entries, never ad hoc balance rewrites. Tests need transaction races, duplicate/retry behavior, fraud limits, odds, balance simulation, and migration rollback.

## Open questions and next session

- Q-0039 answered (2026-06-09): donation = cosmetic-only, no bot-side billing — see the
  router entry for the full marked-up answer (allow/forbid lists + the CI invariant).
- Decide legal/product posture for lottery entries before any executable plan.
- **Recommended next model/session:** Opus economy architecture/revision; a later Sonnet slice may draft starter-pack or deterministic streak-read planning after economy-health evidence exists.
