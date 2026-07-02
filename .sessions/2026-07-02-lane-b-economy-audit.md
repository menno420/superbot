# 2026-07-02 — Lane B new-bot capability audit (Economy & Character-sim)

> **Status:** `complete` — docs-only, ULTRACODE. Audited the 11 Lane B subsystems against the §2 manifest
> grammar and wrote the full lane file. No `disbot/` / runtime code. `check_docs --strict` ✓ ·
> `check_current_state_ledger --strict` ✓. PR #1665.

## What shipped
- **`docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-B-economy.md`** — the complete
  Lane B audit: **449 surface units, 67% fit as-written → 88% with amendments** (GO-with-amendments; no
  NO-GO subsystem). Per subsystem: source-verified surface-unit ledger (both tier columns, every claim
  cited `file:line`), a §2 manifest sketch, tier-3 → amendment/escape-hatch dispositions, fit numbers,
  a structural danger-zone matrix, and a MAP→RECONSIDER→SIMULATE→OPTIMIZE recommendation with the
  capstone carry-forward fields (dependency-layer · production-grade done · outperform target · status).
- **Method:** an 11-agent source-verification fan-out (one per subsystem, ~1.24M tokens, `high` effort),
  then a **7-agent adversarial refute pass** on every proposed new amendment + every surprising fit, then
  synthesis. I independently read the highest-risk mutation/settlement paths myself
  (`economy_service.transfer`, `treasury_service.contribute/disburse`, `mining_workflow` ×27 txns,
  `farm_workflow.settle`) as ground truth for the refute pass.

## Key decisions / verdicts (durable)
- **Six new amendment families are the real Lane B ask (all economy/character-sim primitives):**
  **G-7 EconomyTransactionSpec** (the load-bearing one — atomic debit/credit+audit+emit-after-commit;
  6 subsystems; safety-critical), **G-8 ItemCatalogSpec**, **G-9 ProgressionSpec** (declares the *gate*,
  not the payout), **G-11 ShopSpec**, **G-12 CraftingRecipeSpec**, **G-13 IdleAccrualSpec**, plus a
  **scoped G-10** persistent-world store convention (mostly `StoreSpec` + tier-3; only mining needs it).
- **The adversarial pass refuted all seven *new* over-eager amendments the fan-out proposed** (G-14
  LootTable → tier-3 §10.1 engines; G-15 MultiSeatSession → existing `ChallengeSessionSpec`; G-16
  ReadModelProjection → `ProviderRef` projection-args; G-17 ParticipationPref → user-scoped `SettingSpec`;
  G-18 ManagedProjection → `ManagedTaskSpec`; G-19 SettingsPreset → `SettingSpec.presets`; G-20
  AutoResponder → `G-1`+`ProviderRef`). This is the Q-0120 poison-guard working: it halved the amendment
  count and **corrected casino's fit 68% → 24%** (the fan-out over-credited a non-existent multi-seat
  family). Casino is the audit floor — 16%→24%, below blackjack's 44%, because it has *zero* config
  surface and is ~85% game logic (the one thing the grammar must never own).
- **Two residues are legitimate tier-3 forever:** game engines + weighted-RNG reward/encounter/drop rolls
  (§10.1), and stateful live-game loops (casino poker table).
- **Build order:** L0 four_twenty/counters (counters is mis-binned — its kin is the Lane A operator band) →
  L1 economy+xp kernel → L2 inventory+treasury → L3 farm/fishing/creature/casino → **mining last (deepest
  consumer; the acceptance test for the whole Lane B primitive stack)**.
- **Settlement paths are already well-guarded** (conditional single-statement debits + one `db.transaction()`
  + emit-after-commit): no double-spend bug. G-7's value is making that correctness *kernel-owned* so a
  *new* subsystem can't re-derive it wrong.

## ⚑ Self-initiated (flag for review)
- The audit itself was **owner-directed** (session prompt = Lane B). Self-initiated *judgment* worth a
  reviewer's eye: **(1)** the adversarial DOWN-correction of the fan-out's fit numbers — Lane B 91% → 88%,
  casino 68% → 24%, counters/four_twenty −1 unit each — driven by the refute pass (I trust it; casino's 6
  amended units are listed in the file for audit). **(2)** The recurrence-based rubric I applied uniformly
  to accept G-7/8/9/11/12/13 and reject G-14…G-20 (≥2 shipped subsystems + not-a-composition). A reviewer
  who disagrees with any single refute verdict can flip it from the §4 table without touching the ledgers.

## 💡 Session idea (Q-0089)
**A shared append-only amendment-id registry for the capability audit** (`.../new-bot-capability-audit/
amendments.md`, next-free-`G-<n>` like the question router). The BRIEF seeds G-1…G-6 and says "extend the
list" but gives no *coordination* mechanism — so parallel lanes (and even my own sub-agents) locally
numbered new families inconsistently (my fan-out produced three different "G-14"s; I reconciled by hand).
A claimed-id registry lets every lane grab the next free id for a genuinely-new family, and lets the
capstone merge the four lanes' amendment proposals with zero de-collision work. Cheap, and it directly
de-risks the capstone's hardest merge. (Dedup-checked `docs/ideas/` — no existing entry.)

## ⟲ Previous-session review (Q-0102)
**Reviewed:** the audit-substrate sessions (#1660 "prepare the substrate" + #1662 "harden the BRIEF with
launch preconditions") — the direct predecessors my lane executed against. **What they did well:** the
substrate was genuinely excellent to work from — pre-extracted per-subsystem scaffolds (facts-only, blank
tier columns), a frozen grammar spike with three worked manifests + a `measure.py` tier ledger for
calibration, `ground-truth/command-surface.json` cross-checkable command counts, and the explicit
G-1…G-6 amendment seed. The BRIEF's Q-0120 "cite `file:line`, mark `⚠ unverified`" discipline is exactly
what produced the honest caveats in my output, and #1662's capstone carry-forward fields
(dependency/done/outperform) slotted straight into my recommendations. **What it missed → concrete system
improvement:** it never established a **shared amendment-id registry** for *new* families (see the Q-0089
idea) — the single coordination gap that made me reconcile a G-14 id-collision by hand and that will cost
the capstone real effort across four lanes. Adding that registry to the substrate is a small, high-leverage
fix that makes the parallel-lane design compose as cleanly for *amendments* as it already does for
*subsystems*. (No filler — this is the one real gap I hit; everything else about the substrate held up.)

## Q-0104 documentation audit
- `check_docs --strict` ✓ (fixed a `complete`→`reference` badge-token slip the checker caught — the
  audit output is `reference` material; "COMPLETE" lives in the prose).
- `check_current_state_ledger --strict` ✓ (unaffected — a docs audit is not a merged-PR ledger entry).
- No new owner decision to route to the question router; no new durable doc home needed beyond the lane
  file (the BRIEF already homes the audit). Claim file + this session card are the only other writes.

## Context delta
- **needed-not-pointed:** the shared amendment-id registry gap (above); that the fan-out would *over*-credit
  new families without an adversarial pass (the 68%→24% casino swing came *only* from the refute step —
  a single-pass audit would have shipped an inflated number).
- **discovered-by-hand:** the G-7 choreography is genuinely uniform across `transfer`/treasury/mining/farm/
  fishing (I read all of them); casino/four_twenty are truly stateless-of-DB (verified no store/settings/
  events); the xp earn path is a `message_pipeline` `XpStage`, not a raw gateway listener (cite the stage,
  not G-1).
