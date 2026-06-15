# Session — Mining Vault v2: inventory soft-cap + vault-cap upgrade path

> **Status:** `complete`
> **Branch:** `claude/sharp-ptolemy-qf8jz6` · **PR:** #897
> **Date:** 2026-06-15 (autonomous routine — dispatched work order)

## Work order

Dispatched `CLASS: feature`: **Mining Slice A — Vault v2** (inventory soft-cap +
vault-cap upgrade path). Acceptance: `check_quality --full` green + `check_architecture`
0 errors + vault cap math tests. Notes: additive only; warn at cap, no hard-block; no
hard cap approved.

## Phase-gate decision (why I built a feature in a FIX phase)

`check_phase_gate.py --require-invent` → **exit 1 (FIX)** (2 OPEN bugs + 28 not-done
rows). But Q-0114 gates only **agent-self-originated** features. The owner **directly
corrected** this exact scenario in-session (recorded in
`docs/ideas/dispatch-phase-gate-precheck-2026-06-15.md` ⚠ Correction): a *dispatched*
work order is **owner-directed** and flows freely, like a bug fix — and the prior run
built Slice D (#891) on that correction. My routine prompt itself scopes the gate to
"feature (**agent-originated**)". Gating this dispatched feature would have repeated the
mistake the owner called out, so I **built** it. (Found the correction by grepping
`docs/ideas/` — see the 💡 idea below; that discoverability gap is the one real friction.)

## What shipped (#897)

- `disbot/utils/mining/capacity.py` — pure cap math: `PACK_SOFT_CAP=40`, vault capacity
  `30 + level×15` (max tier 6), rising coin upgrade-cost ladder, `CapStatus`, distinct-type
  counts, gentle warning copy. Caps measure **distinct item-types**, not quantity.
- **Pack soft-cap = warning-only** (never blocks): the hub overview shows a 🎒 Pack field +
  nudge, and every mine/harvest/explore swing appends a "stash at the 🏦 Vault" line when
  at/over cap (`MineResult`/`HarvestResult`/`ExploreActionResult.pack_warning`).
- **Vault upgradeable capacity** (coin sink): `mining_workflow.vault_upgrade` (debit +
  `vault_level` raise in one transaction — the `buy`/`skill_service.respec` precedent),
  migration 072 adds `vault_level` to `mining_player_state`, `!vaultupgrade` + the vault
  panel's ⬆️ Upgrade button; the panel shows 📦 Capacity + an over-capacity nudge.
- New write primitive `set_vault_level` registered in the RS02 write-boundary ratchet.
- Fully **additive** — level 0 = the v1 base capacity; deposits/withdrawals never blocked.
- Tests: `tests/unit/utils/test_mining_capacity.py` (cap/ladder/threshold/warning math) +
  vault-upgrade contract + pack-warning pins in `tests/unit/cogs/test_mining_vault.py` +
  conn-dispatch pin. `check_quality --full` green (9719); arch 0.
- Docs: plan Slice A marked DONE; current-state Recently-shipped + mining lane updated;
  archived the oldest entry (#825) to hold the ratchet at 20.

## 💡 Session idea (Q-0089)

**Canonically home the "dispatched feature = owner-directed, ungated" rule.** It currently
lives only in a `status: ideas` file's ⚠ Correction block, so a literal agent reading just
its routine prompt + CLAUDE.md can't find it and may re-gate a dispatched feature (the #888
mistake) — or build a genuinely agent-invented one in fix-phase. *Why worth having:* this is
the **third** recurrence of the scenario (#888 → #889/#891 → #897); the fix is a one-paragraph
docs change (a router Q-block + one sentence in `check_phase_gate.py`'s help) that converts a
grep-into-the-backlog into a canonical lookup. Recorded in detail under "Recurrence #3" in
`docs/ideas/dispatch-phase-gate-precheck-2026-06-15.md` (strengthened the existing idea rather
than spawn a near-duplicate file).

## ⟲ Previous-session review (Q-0102)

Reviewing **#892 + #889** (docs-only loop hygiene): #889 did the disciplined thing — it
*captured* the gated work and authored the dispatch-phase-gate-precheck idea, which is exactly
what let *this* run resolve the ambiguity fast. Credit where due. The miss it shares with #888:
both treated the phase gate's FIX verdict as the final word on a *dispatched* feature, when the
owner had already said dispatched = owner-directed. **System improvement it surfaces** (and that
I acted on): the correction needs a canonical home — see the 💡 idea. Until that lands, the
autonomous loop will keep spending a fire (or worse, a wrong call) re-deriving a decision the
owner already made. The self-auditing loop works, but it's leaning on grep where it should be
leaning on a binding doc.

## Close-out

- Doc audit (Q-0104): `check_current_state_ledger --strict` ✓, `check_docs --strict` ✓.
- Backlog grooming (Q-0015): strengthened the dispatch-phase-gate idea with the canonical-homing
  next step (moved it down its lifecycle toward an actionable router/docs change).
- Active-work claim added at open; removed at close.
