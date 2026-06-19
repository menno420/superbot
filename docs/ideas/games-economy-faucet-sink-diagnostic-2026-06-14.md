# Idea — games economy faucet/sink diagnostic (observe the loop's balance)

> **Status:** `historical` — ✅ **PROMOTED to a plan (2026-06-15, band-#930 reconciliation pass):**
> the gate below ("promote once a sink-heavy slice lands") was cleared by respec (#912) + the
> structures sinks (#905/#910), so this capture became the executable
> [`planning/games-economy-faucet-sink-diagnostic-plan-2026-06-15.md`](../planning/games-economy-faucet-sink-diagnostic-plan-2026-06-15.md).
> Routing: **S1 Bot / games + observability**. Raised 2026-06-14 from the mining Vault session
> (#884) + the structures/skill-tree plan. Kept here for provenance.
> **Subsystem:** economy, games, mining — the economy faucet/sink read model.

## The gap

The mining brainstorm's §7.5 thesis is a **closed, self-balancing loop**: ore is the *faucet*
(sell → coins), and coins drain through *sinks* (buy gear · repair · — and, in the planned slices —
**structure builds · skill respec · vault-capacity upgrades**). Every slice in
[`planning/mining-structures-skill-tree-plan-2026-06-14.md`](../planning/mining-structures-skill-tree-plan-2026-06-14.md)
adds another sink. But there is **no way to observe whether the loop is actually balanced** — in the
sandbox or in prod. Balance today is validated *statically* per feature (the
[`gear-set-numbers`](../planning/gear-set-numbers-2026-06-11.md) sim record), never *observed live*.

## The idea

A read-only **economy faucet/sink diagnostic** — a `diagnostics_service` provider (the established
cogs-register-into-services pattern) that aggregates the `economy_service` reasons already emitted
(`mining:sell_ore` = faucet; `mining:buy_gear` / `mining:repair_gear` / future
`mining:respec` / `mining:build` = sinks) into a per-guild **net coin flow** view: total in vs. out
per reason over a window, and the faucet:sink ratio. Surfaced via the platform/diagnostics hub
(owner-tier), content-free (counts only, no user data).

**Why it's worth having:** it turns "is the economy inflating?" from a guess into a number the owner
can watch as the sinks land — the observability complement to the static sim. It's cheap (the audit
reasons already exist; this just sums them), and it pairs naturally with the skill-tree/structures
slices that each introduce a new sink reason.

## Dedup

Distinct from the static balance-sim ideas (gear-set-numbers record; the survival **P0 balance-sim
harness**, Q-0087) — those *predict* balance offline; this *observes* it live. Distinct from the
existing diagnostics providers (health, media, event_bus) — none covers economy flow.

## Gate

Promote once a sink-heavy slice (skill-tree respec or structure builds) lands — then there's real
flow to observe. Small, read-only; no per-exposure AI lift needed.
